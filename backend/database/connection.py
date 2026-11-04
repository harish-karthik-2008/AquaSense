"""
Database Connection Manager for AquaSense AI
Provides unified async interface for MongoDB with seamless fallback to
persistent local JSON storage if MongoDB daemon is unreachable.
"""

import os
import json
import socket
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
motor = None

USE_MONGODB = os.getenv("USE_MONGODB", "false").lower() in ("true", "1", "yes")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "aquasense_ai")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "aquasense_db.json")

if USE_MONGODB:
    try:
        import motor.motor_asyncio
    except (ImportError, Exception):
        motor = None

class LocalCollection:
    """Async-compatible in-memory + file-persisted collection mimicking Motor/MongoDB."""
    def __init__(self, name: str, parent_db):
        self.name = name
        self.parent_db = parent_db

    async def insert_one(self, doc: Dict[str, Any]):
        data = self.parent_db.get_collection_data(self.name)
        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            import uuid
            doc_copy["_id"] = str(uuid.uuid4())
        # serialize any datetime objects
        for k, v in list(doc_copy.items()):
            if isinstance(v, datetime):
                doc_copy[k] = v.isoformat()
        data.append(doc_copy)
        await self.parent_db.persist()
        return type("InsertResult", (), {"inserted_id": doc_copy["_id"]})

    async def find_one(self, filter_dict: Optional[Dict[str, Any]] = None, sort: Optional[List] = None):
        items = await self._find_matching(filter_dict)
        if sort:
            for field, direction in reversed(sort):
                items.sort(key=lambda x: x.get(field, ""), reverse=(direction < 0))
        return items[0] if items else None

    async def _find_matching(self, filter_dict: Optional[Dict[str, Any]]):
        data = self.parent_db.get_collection_data(self.name)
        if not filter_dict:
            return list(data)
        matches = []
        for doc in data:
            match = True
            for k, v in filter_dict.items():
                if isinstance(v, dict):
                    # Handle basic operators like $gte, $lte, $eq, $ne
                    doc_val = doc.get(k)
                    if "$gte" in v and not (doc_val is not None and doc_val >= v["$gte"]):
                        match = False
                    if "$lte" in v and not (doc_val is not None and doc_val <= v["$lte"]):
                        match = False
                    if "$gt" in v and not (doc_val is not None and doc_val > v["$gt"]):
                        match = False
                    if "$lt" in v and not (doc_val is not None and doc_val < v["$lt"]):
                        match = False
                    if "$eq" in v and not (doc_val == v["$eq"]):
                        match = False
                    if "$ne" in v and not (doc_val != v["$ne"]):
                        match = False
                else:
                    if doc.get(k) != v:
                        match = False
            if match:
                matches.append(dict(doc))
        return matches

    def find(self, filter_dict: Optional[Dict[str, Any]] = None):
        collection = self
        class Cursor:
            def __init__(self):
                self._filter = filter_dict
                self._sort_fields = []
                self._limit_val = None
                self._skip_val = 0

            def sort(self, key_or_list, direction=1):
                if isinstance(key_or_list, list):
                    self._sort_fields = key_or_list
                else:
                    self._sort_fields = [(key_or_list, direction)]
                return self

            def limit(self, n: int):
                self._limit_val = n
                return self

            def skip(self, n: int):
                self._skip_val = n
                return self

            async def to_list(self, length: Optional[int] = None):
                items = await collection._find_matching(self._filter)
                if self._sort_fields:
                    for field, direction in reversed(self._sort_fields):
                        items.sort(key=lambda x: str(x.get(field, "")), reverse=(direction < 0))
                start = self._skip_val
                limit = length if length is not None else self._limit_val
                if limit is not None:
                    return items[start:start + limit]
                return items[start:]

            def __aiter__(self):
                async def gen():
                    items = await self.to_list()
                    for item in items:
                        yield item
                return gen()

        return Cursor()

    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        data = self.parent_db.get_collection_data(self.name)
        for doc in data:
            match = all(doc.get(k) == v for k, v in filter_dict.items())
            if match:
                if "$set" in update_dict:
                    for sk, sv in update_dict["$set"].items():
                        if isinstance(sv, datetime):
                            sv = sv.isoformat()
                        doc[sk] = sv
                else:
                    for k, v in update_dict.items():
                        doc[k] = v
                await self.parent_db.persist()
                return type("UpdateResult", (), {"modified_count": 1})
        return type("UpdateResult", (), {"modified_count": 0})

    async def update_many(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        data = self.parent_db.get_collection_data(self.name)
        modified = 0
        for doc in data:
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                if "$set" in update_dict:
                    for sk, sv in update_dict["$set"].items():
                        if isinstance(sv, datetime):
                            sv = sv.isoformat()
                        doc[sk] = sv
                modified += 1
        if modified > 0:
            await self.parent_db.persist()
        return type("UpdateResult", (), {"modified_count": modified})

    async def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None):
        items = await self._find_matching(filter_dict)
        return len(items)

    async def delete_many(self, filter_dict: Optional[Dict[str, Any]] = None):
        data = self.parent_db.get_collection_data(self.name)
        if not filter_dict:
            count = len(data)
            data.clear()
            await self.parent_db.persist()
            return type("DeleteResult", (), {"deleted_count": count})
        initial_len = len(data)
        matches = await self._find_matching(filter_dict)
        match_ids = {m.get("_id") for m in matches}
        self.parent_db._store[self.name] = [d for d in data if d.get("_id") not in match_ids]
        await self.parent_db.persist()
        return type("DeleteResult", (), {"deleted_count": initial_len - len(self.parent_db._store[self.name])})

    async def delete_one(self, filter_dict: Optional[Dict[str, Any]] = None):
        return await self.delete_many(filter_dict)


class LocalAsyncDatabase:
    """Local JSON-backed persistent fallback store."""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._store = json.load(f)
            except Exception:
                self._store = {}
        else:
            self._store = {}

    async def persist(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            print(f"[FallbackDB] Error saving to {self.filepath}: {e}")

    def get_collection_data(self, name: str) -> List[Dict[str, Any]]:
        if name not in self._store:
            self._store[name] = []
        return self._store[name]

    def __getitem__(self, name: str):
        return LocalCollection(name, self)


class DatabaseManager:
    _instance = None
    _db = None
    _is_fallback = False
    _client = None

    @classmethod
    async def get_db(cls):
        if cls._db is None:
            await cls.init_db()
        return cls._db

    @classmethod
    async def init_db(cls):
        if USE_MONGODB and motor is not None:
            try:
                print(f"[Database] Connecting to MongoDB at {MONGODB_URI}...")
                client = motor.motor_asyncio.AsyncIOMotorClient(
                    MONGODB_URI,
                    serverSelectionTimeoutMS=2000
                )
                await client.admin.command('ping')
                cls._client = client
                cls._db = client[DB_NAME]
                cls._is_fallback = False
                print(f"[Database] Successfully connected to live MongoDB at {MONGODB_URI}/{DB_NAME}")
                return
            except Exception as e:
                print(f"[Database] MongoDB connection failed: {e}. Switching to persistent local document store.")

        # Default fast, reliable local store
        print(f"[Database] Active storage: Persistent Local Document DB ({DATA_FILE}).")
        cls._db = LocalAsyncDatabase(DATA_FILE)
        cls._is_fallback = True

    @classmethod
    def is_fallback(cls) -> bool:
        return cls._is_fallback

    @classmethod
    async def get_status(cls) -> Dict[str, Any]:
        return {
            "type": "Local Persistent Fallback" if cls._is_fallback else "MongoDB",
            "connected": True,
            "database_name": DB_NAME,
            "using_fallback": cls._is_fallback,
            "storage_path": DATA_FILE if cls._is_fallback else MONGODB_URI
        }

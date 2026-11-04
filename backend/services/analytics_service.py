"""
AquaSense AI - Historical Water Quality Analytics Service
Computes statistical aggregations, parametric bounds (min, max, avg),
status distribution, daily/weekly trends, anomaly frequency patterns,
and plain-English water quality executive summaries.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter

from database.connection import DatabaseManager

class AnalyticsService:
    def __init__(self):
        pass

    async def get_readings_collection(self):
        db = await DatabaseManager.get_db()
        return db["sensor_readings"]

    async def get_historical_readings(
        self,
        timeframe: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Fetch chronological records matching date range or timeframe."""
        col = await self.get_readings_collection()
        filter_dict: Dict[str, Any] = {}
        now = datetime.now(timezone.utc)

        # 1. Custom Date Range filtering (Requirement 10)
        if start_date or end_date:
            ts_filter: Dict[str, str] = {}
            if start_date:
                # Support YYYY-MM-DD or full ISO
                start_iso = f"{start_date}T00:00:00+00:00" if len(start_date) == 10 else start_date
                ts_filter["$gte"] = start_iso
            if end_date:
                end_iso = f"{end_date}T23:59:59+00:00" if len(end_date) == 10 else end_date
                ts_filter["$lte"] = end_iso
            if ts_filter:
                filter_dict["timestamp"] = ts_filter
        elif timeframe:
            tf = timeframe.lower()
            if tf == "1h":
                since = (now - timedelta(hours=1)).isoformat()
                filter_dict["timestamp"] = {"$gte": since}
            elif tf in ("24h", "today"):
                since = (now - timedelta(hours=24)).isoformat()
                filter_dict["timestamp"] = {"$gte": since}
            elif tf == "7d":
                since = (now - timedelta(days=7)).isoformat()
                filter_dict["timestamp"] = {"$gte": since}
            elif tf == "30d":
                since = (now - timedelta(days=30)).isoformat()
                filter_dict["timestamp"] = {"$gte": since}
            # "all" does not constrain timestamp

        cursor = col.find(filter_dict).sort("timestamp", 1).limit(limit)
        items = await cursor.to_list(length=limit)
        for item in items:
            if "_id" in item:
                item["id"] = str(item["_id"])
        return items

    async def compute_analytics(
        self,
        timeframe: Optional[str] = "24h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Compute comprehensive historical water quality metrics."""
        readings = await self.get_historical_readings(
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        filter_label = f"{start_date} to {end_date}" if (start_date or end_date) else (timeframe or "24h")

        # Handle empty database gracefully (Technical Requirement)
        if not readings:
            return {
                "has_data": False,
                "count": 0,
                "total_readings": 0,
                "timeframe": timeframe,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "applied_filter": filter_label
                },
                "tds": {"min": 0, "max": 0, "avg": 0},
                "ph": {"min": 0, "max": 0, "avg": 0},
                "turbidity": {
                    "min": 0,
                    "max": 0,
                    "avg": 0,
                    "note": "Turbidity values are simulated units based on Wokwi potentiometer"
                },
                "water_quality_score": {"min": 0, "max": 0, "avg": 0},
                "status_counts": {
                    "normal": 0,
                    "warning": 0,
                    "critical": 0
                },
                "status_percentages": {
                    "normal_pct": 0.0,
                    "warning_pct": 0.0,
                    "critical_pct": 0.0
                },
                "daily_trends": [],
                "weekly_trends": [],
                "trend_direction": "insufficient_data",
                "anomalies_summary": {
                    "total_anomalies": 0,
                    "anomaly_rate_pct": 0.0,
                    "frequent_anomalies": []
                },
                "most_frequently_abnormal_parameter": {
                    "parameter": "None",
                    "breach_count": 0,
                    "breach_percentage": 0.0,
                    "description": "No sensor readings available for analysis."
                },
                "summary_text": "No sensor records found for the selected timeframe. Connect the ESP32 simulator to begin streaming water quality telemetry.",
                "key_observations": [
                    "Database has zero records in the requested date range.",
                    "Awaiting initial sensor data stream from Wokwi simulation node."
                ]
            }

        total = len(readings)

        # 1. Parameter Bounds (Min, Max, Avg) - Requirements 1, 2, 3
        tds_vals = [float(r["tds"]) for r in readings if "tds" in r and r["tds"] is not None]
        ph_vals = [float(r["ph"]) for r in readings if "ph" in r and r["ph"] is not None]
        turb_vals = [float(r["turbidity"]) for r in readings if "turbidity" in r and r["turbidity"] is not None]
        wqi_vals = [float(r.get("water_quality_score", 100)) for r in readings]

        tds_stats = {
            "min": round(min(tds_vals), 1) if tds_vals else 0.0,
            "max": round(max(tds_vals), 1) if tds_vals else 0.0,
            "avg": round(sum(tds_vals) / len(tds_vals), 1) if tds_vals else 0.0
        }

        ph_stats = {
            "min": round(min(ph_vals), 2) if ph_vals else 0.0,
            "max": round(max(ph_vals), 2) if ph_vals else 0.0,
            "avg": round(sum(ph_vals) / len(ph_vals), 2) if ph_vals else 0.0
        }

        turb_stats = {
            "min": round(min(turb_vals), 2) if turb_vals else 0.0,
            "max": round(max(turb_vals), 2) if turb_vals else 0.0,
            "avg": round(sum(turb_vals) / len(turb_vals), 2) if turb_vals else 0.0,
            "note": "Turbidity values are simulated units based on Wokwi potentiometer"
        }

        wqi_stats = {
            "min": round(min(wqi_vals), 1) if wqi_vals else 0.0,
            "max": round(max(wqi_vals), 1) if wqi_vals else 0.0,
            "avg": round(sum(wqi_vals) / len(wqi_vals), 1) if wqi_vals else 0.0
        }

        # 2. Status Counts (Normal, Warning, Critical) - Requirements 4, 5
        status_counts = {"normal": 0, "warning": 0, "critical": 0}
        for r in readings:
            st = str(r.get("overall_status", "Normal")).lower()
            if st in status_counts:
                status_counts[st] += 1
            else:
                status_counts["normal"] += 1

        status_percentages = {
            "normal_pct": round((status_counts["normal"] / total) * 100, 1),
            "warning_pct": round((status_counts["warning"] / total) * 100, 1),
            "critical_pct": round((status_counts["critical"] / total) * 100, 1)
        }

        # 3. Daily & Weekly Trends - Requirement 6
        daily_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        weekly_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for r in readings:
            ts = r.get("timestamp", "")
            try:
                # Normalize timestamp ISO
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                day_key = dt.strftime("%Y-%m-%d")
                year, week_num, _ = dt.isocalendar()
                week_key = f"{year}-W{week_num:02d}"
            except Exception:
                day_key = ts[:10] if len(ts) >= 10 else "Unknown"
                week_key = "Unknown"

            daily_groups[day_key].append(r)
            weekly_groups[week_key].append(r)

        daily_trends = []
        for day_k in sorted(daily_groups.keys()):
            grp = daily_groups[day_k]
            d_tds = [r["tds"] for r in grp if "tds" in r]
            d_ph = [r["ph"] for r in grp if "ph" in r]
            d_turb = [r["turbidity"] for r in grp if "turbidity" in r]
            d_wqi = [r.get("water_quality_score", 100) for r in grp]

            d_norm = sum(1 for r in grp if str(r.get("overall_status", "")).lower() == "normal")
            d_warn = sum(1 for r in grp if str(r.get("overall_status", "")).lower() == "warning")
            d_crit = sum(1 for r in grp if str(r.get("overall_status", "")).lower() == "critical")

            daily_trends.append({
                "date": day_k,
                "readings_count": len(grp),
                "tds_avg": round(sum(d_tds) / len(d_tds), 1) if d_tds else 0.0,
                "ph_avg": round(sum(d_ph) / len(d_ph), 2) if d_ph else 0.0,
                "turbidity_avg": round(sum(d_turb) / len(d_turb), 2) if d_turb else 0.0,
                "water_quality_score_avg": round(sum(d_wqi) / len(d_wqi), 1) if d_wqi else 0.0,
                "normal_count": d_norm,
                "warning_count": d_warn,
                "critical_count": d_crit
            })

        weekly_trends = []
        for week_k in sorted(weekly_groups.keys()):
            grp = weekly_groups[week_k]
            w_tds = [r["tds"] for r in grp if "tds" in r]
            w_ph = [r["ph"] for r in grp if "ph" in r]
            w_turb = [r["turbidity"] for r in grp if "turbidity" in r]
            w_wqi = [r.get("water_quality_score", 100) for r in grp]

            weekly_trends.append({
                "week": week_k,
                "readings_count": len(grp),
                "tds_avg": round(sum(w_tds) / len(w_tds), 1) if w_tds else 0.0,
                "ph_avg": round(sum(w_ph) / len(w_ph), 2) if w_ph else 0.0,
                "turbidity_avg": round(sum(w_turb) / len(w_turb), 2) if w_turb else 0.0,
                "water_quality_score_avg": round(sum(w_wqi) / len(w_wqi), 1) if w_wqi else 0.0
            })

        # Calculate overall water quality trend direction
        trend_direction = "stable"
        if len(readings) >= 6:
            mid = len(readings) // 2
            first_half_wqi = sum(wqi_vals[:mid]) / mid
            second_half_wqi = sum(wqi_vals[mid:]) / (len(readings) - mid)
            delta = second_half_wqi - first_half_wqi
            if delta >= 2.0:
                trend_direction = "improving"
            elif delta <= -2.0:
                trend_direction = "degrading"

        # 4. Frequently Occurring Anomalies - Requirement 7
        anomalies_detected = [r for r in readings if r.get("anomaly_detected")]
        anomaly_count = len(anomalies_detected)
        anomaly_rate_pct = round((anomaly_count / total) * 100, 1)

        anomaly_reasons = []
        for a in anomalies_detected:
            reason = a.get("anomaly_reason") or "Pattern anomaly deviation"
            # Extract core explanation summary
            if ":" in reason:
                reason_summary = reason.split(":")[0].strip()
            else:
                reason_summary = reason[:60]
            anomaly_reasons.append(reason_summary)

        reason_counts = Counter(anomaly_reasons)
        frequent_anomalies = [
            {"pattern": pattern, "count": cnt, "percentage": round((cnt / anomaly_count) * 100, 1)}
            for pattern, cnt in reason_counts.most_common(5)
        ]

        # 5. Most Frequently Abnormal Sensor Parameter - Requirement 8
        tds_abnormal = sum(1 for r in readings if str(r.get("tds_status", "")).lower() in ("warning", "critical"))
        ph_abnormal = sum(1 for r in readings if str(r.get("ph_status", "")).lower() in ("warning", "critical"))
        turb_abnormal = sum(1 for r in readings if str(r.get("turbidity_status", "")).lower() in ("warning", "critical"))

        # Also account for AI-flagged anomaly primary parameters
        ai_param_counts = Counter([
            r.get("anomaly_reason", "").split(" deviated")[0].replace("Unusual water-quality pattern detected: ", "").strip()
            for r in anomalies_detected if "Unusual water-quality pattern detected:" in str(r.get("anomaly_reason", ""))
        ])

        param_breach_totals = {
            "TDS": tds_abnormal + ai_param_counts.get("TDS", 0),
            "pH": ph_abnormal + ai_param_counts.get("pH", 0),
            "Turbidity": turb_abnormal + ai_param_counts.get("Turbidity", 0)
        }

        total_breaches = sum(param_breach_totals.values())
        if total_breaches > 0:
            top_param, top_count = max(param_breach_totals.items(), key=lambda x: x[1])
            top_pct = round((top_count / total_breaches) * 100, 1)
            abnormal_desc = (
                f"{top_param} showed the highest frequency of abnormal readings, "
                f"accounting for {top_count} of {total_breaches} ({top_pct}%) flagged status events."
            )
        else:
            top_param = "None"
            top_count = 0
            top_pct = 0.0
            abnormal_desc = "All monitored parameters remained within safe drinking thresholds."

        # 6. Understandable Water-Quality Summaries - Requirement 9
        summary_paragraphs = []
        summary_paragraphs.append(
            f"Over the analyzed period ({filter_label}, {total} readings), overall water quality achieved "
            f"an average purity score of {wqi_stats['avg']}/100. "
            f"System status was {status_percentages['normal_pct']}% Normal, {status_percentages['warning_pct']}% Warning, "
            f"and {status_percentages['critical_pct']}% Critical."
        )

        param_details = (
            f"TDS averaged {tds_stats['avg']} ppm (min {tds_stats['min']}, max {tds_stats['max']}), "
            f"pH averaged {ph_stats['avg']} (min {ph_stats['min']}, max {ph_stats['max']}), and "
            f"simulated turbidity averaged {turb_stats['avg']} (min {turb_stats['min']}, max {turb_stats['max']})."
        )
        summary_paragraphs.append(param_details)

        if anomaly_count > 0:
            summary_paragraphs.append(
                f"A total of {anomaly_count} AI pattern anomalies were detected ({anomaly_rate_pct}% anomaly rate). "
                f"{abnormal_desc}"
            )
        else:
            summary_paragraphs.append(
                "Zero multivariate anomalies were detected; water sensor patterns matched learned baseline operating profiles."
            )

        summary_paragraphs.append(f"Overall water quality trend is evaluated as {trend_direction.upper()}.")

        full_summary_text = " ".join(summary_paragraphs)

        key_observations = [
            f"Evaluated {total} historical records over {filter_label}.",
            f"{status_percentages['normal_pct']}% compliance with Normal drinking water guidelines.",
            f"TDS range: {tds_stats['min']} - {tds_stats['max']} ppm (avg: {tds_stats['avg']} ppm).",
            f"pH range: {ph_stats['min']} - {ph_stats['max']} (avg: {ph_stats['avg']}).",
            f"Simulated Turbidity range: {turb_stats['min']} - {turb_stats['max']} (avg: {turb_stats['avg']}).",
            f"Overall quality trend direction: {trend_direction.capitalize()}."
        ]

        if top_param != "None":
            key_observations.append(f"Most frequent abnormal parameter: {top_param} ({top_count} events).")

        return {
            "has_data": True,
            "count": total,
            "total_readings": total,
            "timeframe": timeframe,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "applied_filter": filter_label
            },
            "tds": tds_stats,
            "ph": ph_stats,
            "turbidity": turb_stats,
            "water_quality_score": wqi_stats,
            "status_counts": status_counts,
            "status_percentages": status_percentages,
            "daily_trends": daily_trends,
            "weekly_trends": weekly_trends,
            "trend_direction": trend_direction,
            "anomalies_summary": {
                "total_anomalies": anomaly_count,
                "anomaly_rate_pct": anomaly_rate_pct,
                "frequent_anomalies": frequent_anomalies
            },
            "most_frequently_abnormal_parameter": {
                "parameter": top_param,
                "breach_count": top_count,
                "breach_percentage": top_pct,
                "description": abnormal_desc
            },
            "summary_text": full_summary_text,
            "key_observations": key_observations
        }

# Global singleton
analytics_service = AnalyticsService()


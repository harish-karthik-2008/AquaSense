/**
 * AquaSense AI - Real-time WebSocket Client
 * Connects to FastAPI backend WebSocket channel with auto-reconnection and event dispatching.
 */

class WebSocketClient {
  constructor() {
    this.ws = null;
    this.listeners = new Map(); // event -> Set of callbacks
    this.statusListeners = new Set();
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 30;
    this.reconnectInterval = 2000;
    this.pingTimer = null;
    this.status = 'disconnected'; // 'connecting' | 'connected' | 'disconnected'
  }

  getWsUrl() {
    const host = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      ? 'localhost:8000'
      : `${window.location.hostname}:8000`;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${host}/ws`;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const url = this.getWsUrl();
    this.updateStatus('connecting');

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected to AquaSense AI stream');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateStatus('connected');
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const type = payload.type;
          const data = payload.data !== undefined ? payload.data : payload;

          if (this.listeners.has(type)) {
            this.listeners.get(type).forEach((cb) => {
              try {
                cb(data);
              } catch (err) {
                console.error(`[WebSocket] Callback error on ${type}:`, err);
              }
            });
          }

          // Also trigger generic 'message' listeners
          if (this.listeners.has('*')) {
            this.listeners.get('*').forEach((cb) => cb({ type, data }));
          }
        } catch (err) {
          // Plain text or pong
          if (event.data !== 'pong') {
            console.warn('[WebSocket] Non-JSON message received:', event.data);
          }
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.updateStatus('disconnected');
        this.stopHeartbeat();
        this.scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.warn('[WebSocket] Connection error. Reconnecting...');
        this.ws?.close();
      };
    } catch (err) {
      console.error('[WebSocket] Setup exception:', err);
      this.scheduleReconnect();
    }
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.pingTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 15000);
  }

  stopHeartbeat() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('[WebSocket] Reconnect attempts exhausted.');
      return;
    }
    const delay = Math.min(this.reconnectInterval * Math.pow(1.3, this.reconnectAttempts), 15000);
    this.reconnectAttempts++;
    setTimeout(() => {
      console.log(`[WebSocket] Reconnecting (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, delay);
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).delete(callback);
    }
  }

  onStatusChange(callback) {
    this.statusListeners.add(callback);
    callback(this.status);
    return () => this.statusListeners.delete(callback);
  }

  updateStatus(newStatus) {
    this.status = newStatus;
    this.statusListeners.forEach((cb) => cb(newStatus));
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }
}

export const wsClient = new WebSocketClient();


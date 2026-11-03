/**
 * AquaSense AI - REST API Client
 */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : `http://${window.location.hostname}:8000`;

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`[API Error] ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Sensor Data
  getLatestReading: () => request('/api/sensor-data/latest'),
  getHistory: (limit = 100, timeframe = 'all') =>
    request(`/api/sensor-data/history?limit=${limit}&timeframe=${timeframe}`),
  getAnalytics: (timeframe = '24h') =>
    request(`/api/sensor-data/analytics?timeframe=${timeframe}`),
  sendSensorData: (data) =>
    request('/api/sensor-data', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  // Alerts
  getAlerts: (status = null, limit = 50) => {
    const query = status ? `?status=${status}&limit=${limit}` : `?limit=${limit}`;
    return request(`/api/alerts${query}`);
  },
  acknowledgeAlert: (alertId) =>
    request(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' }),
  acknowledgeAllAlerts: () =>
    request('/api/alerts/acknowledge-all', { method: 'POST' }),
  clearAcknowledgedAlerts: () =>
    request('/api/alerts/clear-acknowledged', { method: 'DELETE' }),

  // Device Status
  getDeviceStatus: () => request('/api/device/status'),

  // Filter Health
  getFilterHealth: () => request('/api/filter-health'),
  resetFilterHealth: () => request('/api/filter-health/reset', { method: 'POST' }),

  // Settings
  getSettings: () => request('/api/settings'),
  updateSettings: (settings) =>
    request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    }),

  getBaseUrl: () => API_BASE
};


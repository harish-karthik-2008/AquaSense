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

  // Notifications
  getNotifications: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.status) qs.append('status', params.status);
    if (params.severity) qs.append('severity', params.severity);
    if (params.category) qs.append('category', params.category);
    if (params.parameter) qs.append('parameter', params.parameter);
    if (params.limit) qs.append('limit', params.limit);
    const queryString = qs.toString();
    return request(`/api/notifications${queryString ? '?' + queryString : ''}`);
  },
  getNotificationsSummary: () => request('/api/notifications/summary'),
  getNotification: (id) => request(`/api/notifications/${id}`),
  markNotificationAsRead: (id, readBy = 'User') =>
    request(`/api/notifications/${id}/read`, {
      method: 'POST',
      body: JSON.stringify({ read_by: readBy })
    }),
  markAllNotificationsAsRead: () =>
    request('/api/notifications/mark-all-read', { method: 'POST' }),
  acknowledgeNotification: (id, ackBy = 'User') =>
    request(`/api/notifications/${id}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by: ackBy })
    }),
  acknowledgeAllNotifications: (ackBy = 'User') =>
    request('/api/notifications/acknowledge-all', {
      method: 'POST',
      body: JSON.stringify({ acknowledged_by: ackBy })
    }),
  clearAcknowledgedNotifications: () =>
    request('/api/notifications/clear', { method: 'DELETE' }),

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

  // Recommendations
  getRecommendations: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.priority) qs.append('priority', params.priority);
    if (params.category) qs.append('category', params.category);
    if (params.include_dismissed) qs.append('include_dismissed', 'true');
    const queryString = qs.toString();
    return request(`/api/recommendations${queryString ? '?' + queryString : ''}`);
  },
  dismissRecommendation: (id) =>
    request(`/api/recommendations/${id}/dismiss`, { method: 'POST' }),

  getBaseUrl: () => API_BASE
};

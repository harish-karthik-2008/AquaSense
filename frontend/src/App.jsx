import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Overview from './pages/Overview';
import LiveMonitoring from './pages/LiveMonitoring';
import Analytics from './pages/Analytics';
import Alerts from './pages/Alerts';
import FilterHealth from './pages/FilterHealth';
import DeviceManagement from './pages/DeviceManagement';
import Settings from './pages/Settings';

import { api } from './services/api';
import { wsClient } from './services/websocket';

import './styles/theme.css';
import './styles/layout.css';
import './styles/components.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Sensor Telemetry State
  const [latestReading, setLatestReading] = useState(null);
  const [previousReading, setPreviousReading] = useState(null);
  const [recentReadings, setRecentReadings] = useState([]);
  const [isStreamPaused, setIsStreamPaused] = useState(false);

  // System & Alert State
  const [alerts, setAlerts] = useState([]);
  const [deviceStatus, setDeviceStatus] = useState({ is_online: false, status: 'offline' });
  const [filterHealth, setFilterHealth] = useState(null);
  const [settings, setSettings] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Ref to hold paused state inside callbacks
  const isPausedRef = useRef(isStreamPaused);
  isPausedRef.current = isStreamPaused;

  // Initial Load from REST Backend
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [latestRes, historyRes, alertsRes, devRes, filterRes, settingsRes] = await Promise.allSettled([
          api.getLatestReading(),
          api.getHistory(30, 'all'),
          api.getAlerts(null, 50),
          api.getDeviceStatus(),
          api.getFilterHealth(),
          api.getSettings()
        ]);

        if (latestRes.status === 'fulfilled' && latestRes.value?.data) {
          setLatestReading(latestRes.value.data);
        }

        if (historyRes.status === 'fulfilled' && historyRes.value?.data) {
          const hist = historyRes.value.data;
          setRecentReadings(hist);
          if (hist.length > 1) {
            setPreviousReading(hist[hist.length - 2]);
          }
        }

        if (alertsRes.status === 'fulfilled' && alertsRes.value?.data) {
          setAlerts(alertsRes.value.data);
        }

        if (devRes.status === 'fulfilled' && devRes.value?.data) {
          setDeviceStatus(devRes.value.data);
        }

        if (filterRes.status === 'fulfilled' && filterRes.value?.data) {
          setFilterHealth(filterRes.value.data);
        }

        if (settingsRes.status === 'fulfilled' && settingsRes.value?.data) {
          setSettings(settingsRes.value.data);
        }
      } catch (err) {
        console.error('[AquaSense] Error fetching initial data:', err);
      }
    };

    fetchInitialData();
  }, []);

  // WebSocket Live Updates Connection
  useEffect(() => {
    wsClient.connect();

    const unsubStatus = wsClient.onStatusChange((status) => {
      setWsConnected(status === 'connected');
    });

    // Handle incoming live sensor readings
    const unsubSensor = wsClient.on('sensor_update', (data) => {
      if (!data) return;

      setLatestReading((prev) => {
        setPreviousReading(prev);
        return data;
      });

      // Update device online status on sensor data packet
      setDeviceStatus((prev) => ({
        ...prev,
        is_online: true,
        status: 'online',
        last_seen: data.timestamp
      }));

      // Append to live waveform buffer if not paused
      if (!isPausedRef.current) {
        setRecentReadings((prev) => {
          const updated = [...prev, data];
          return updated.length > 50 ? updated.slice(updated.length - 50) : updated;
        });
      }
    });

    // Handle new alerts
    const unsubAlert = wsClient.on('alert_triggered', (newAlert) => {
      if (!newAlert) return;
      setAlerts((prev) => {
        // Avoid duplicate ID
        const exists = prev.some((a) => a.id === newAlert.id);
        if (exists) return prev;
        return [newAlert, ...prev];
      });
    });

    // Handle alert acknowledged event
    const unsubAck = wsClient.on('alert_acknowledged', (payload) => {
      if (!payload?.id) return;
      setAlerts((prev) =>
        prev.map((a) => (a.id === payload.id ? { ...a, acknowledged: true } : a))
      );
    });

    // Handle batch alert acknowledge event
    const unsubAckAll = wsClient.on('alerts_all_acknowledged', () => {
      setAlerts((prev) => prev.map((a) => ({ ...a, acknowledged: true })));
    });

    // Periodic Heartbeat Poll (every 10 seconds)
    const heartbeatTimer = setInterval(async () => {
      try {
        const res = await api.getDeviceStatus();
        if (res?.data) {
          setDeviceStatus(res.data);
        }
      } catch {
        // silent poll fail
      }
    }, 10000);

    return () => {
      unsubStatus();
      unsubSensor();
      unsubAlert();
      unsubAck();
      unsubAckAll();
      clearInterval(heartbeatTimer);
    };
  }, []);

  // Alert Actions
  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
      );
    } catch (err) {
      console.error('[AquaSense] Failed to acknowledge alert:', err);
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      await api.acknowledgeAllAlerts();
      setAlerts((prev) => prev.map((a) => ({ ...a, acknowledged: true })));
    } catch (err) {
      console.error('[AquaSense] Failed to acknowledge all alerts:', err);
    }
  };

  const handleClearAcknowledged = async () => {
    try {
      await api.clearAcknowledgedAlerts();
      setAlerts((prev) => prev.filter((a) => !a.acknowledged));
    } catch (err) {
      console.error('[AquaSense] Failed to clear acknowledged alerts:', err);
    }
  };

  // Filter Reset Action
  const handleResetFilters = async () => {
    try {
      const res = await api.resetFilterHealth();
      if (res?.data) {
        setFilterHealth(res.data);
      }
    } catch (err) {
      console.error('[AquaSense] Failed to reset filter health:', err);
    }
  };

  // Settings Save Action
  const handleSaveSettings = async (newSettings) => {
    const res = await api.updateSettings(newSettings);
    if (res?.data) {
      setSettings(res.data);
    }
  };

  const unreadAlertCount = alerts.filter((a) => !a.acknowledged).length;
  const activeAlerts = alerts.filter((a) => !a.acknowledged);

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        unreadAlertCount={unreadAlertCount}
        deviceConnected={deviceStatus?.is_online}
        wsConnected={wsConnected}
      />

      {/* Main Content Area */}
      <div className={`main-wrapper ${sidebarCollapsed ? 'expanded' : ''}`}>
        {/* Topbar Navigation */}
        <Topbar
          activeTab={activeTab}
          deviceName={deviceStatus?.device_id || 'AquaSense ESP32'}
          deviceConnected={deviceStatus?.is_online}
          lastReceivedTimestamp={latestReading?.timestamp || deviceStatus?.last_seen}
          unreadAlertCount={unreadAlertCount}
          onOpenAlerts={() => setActiveTab('alerts')}
        />

        {/* Page Content View */}
        <main className="content-area">
          {activeTab === 'overview' && (
            <Overview
              latestReading={latestReading}
              previousReading={previousReading}
              recentReadings={recentReadings}
              activeAlerts={activeAlerts}
              deviceStatus={deviceStatus}
              filterHealth={filterHealth}
              settings={settings}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'live' && (
            <LiveMonitoring
              latestReading={latestReading}
              previousReading={previousReading}
              recentReadings={recentReadings}
              deviceStatus={deviceStatus}
              settings={settings}
              isPaused={isStreamPaused}
              onTogglePause={() => setIsStreamPaused(!isStreamPaused)}
              onClearBuffer={() => setRecentReadings([])}
            />
          )}

          {activeTab === 'analytics' && (
            <Analytics settings={settings} />
          )}

          {activeTab === 'alerts' && (
            <Alerts
              alerts={alerts}
              onAcknowledge={handleAcknowledgeAlert}
              onAcknowledgeAll={handleAcknowledgeAll}
              onClearAcknowledged={handleClearAcknowledged}
            />
          )}

          {activeTab === 'filter' && (
            <FilterHealth
              filterData={filterHealth}
              onResetFilters={handleResetFilters}
            />
          )}

          {activeTab === 'device' && (
            <DeviceManagement deviceStatus={deviceStatus} />
          )}

          {activeTab === 'settings' && (
            <Settings
              settings={settings}
              onSaveSettings={handleSaveSettings}
            />
          )}
        </main>
      </div>
    </div>
  );
}


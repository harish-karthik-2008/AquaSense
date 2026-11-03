import React from 'react';
import { Bell, Cpu, Clock, Layers, Sparkles } from 'lucide-react';

export default function Topbar({
  activeTab = 'overview',
  deviceName = 'AquaSense ESP32',
  deviceConnected = false,
  lastReceivedTimestamp = null,
  unreadAlertCount = 0,
  onOpenAlerts = () => {}
}) {
  // Format relative timestamp
  const formatTime = (ts) => {
    if (!ts) return 'Awaiting initial stream';
    try {
      const date = new Date(ts);
      const now = new Date();
      const diffSec = Math.floor((now - date) / 1000);

      if (diffSec < 5) return 'Just now';
      if (diffSec < 60) return `${diffSec}s ago`;
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return 'Streaming';
    }
  };

  const pageTitles = {
    overview: 'Water Quality Overview',
    live: 'Live Sensor Telemetry',
    analytics: 'Water Quality Analytics',
    alerts: 'Smart Alerts & Incidents',
    filter: 'Predictive Filter Health',
    device: 'Device Management & Simulator',
    settings: 'Threshold Configurations'
  };

  return (
    <header className="topbar">
      {/* Left: Breadcrumbs & Title */}
      <div className="topbar-left">
        <div>
          <div className="page-breadcrumb">
            <span>AquaSense AI</span>
            <span>/</span>
            <span>{pageTitles[activeTab] || 'Dashboard'}</span>
          </div>
          <h1 className="page-title-badge">{pageTitles[activeTab] || 'Dashboard'}</h1>
        </div>
      </div>

      {/* Right: Device Status, Simulation Pill, Notifications, Profile */}
      <div className="topbar-right">
        {/* Simulation Mode Badge */}
        <div className="simulation-mode-badge" title="Data is originating from Wokwi ESP32 Potentiometer Simulation">
          <Layers className="simulation-icon" />
          <span>Simulation Mode (Wokwi)</span>
        </div>

        {/* Device Status */}
        <div className="topbar-device-pill" title={`Connected to ${deviceName}`}>
          <span className={`status-dot ${deviceConnected ? 'online' : 'offline'}`} />
          <span>{deviceName}</span>
        </div>

        {/* Timestamp */}
        <div className="topbar-timestamp" title="Last Sensor Data Telemetry">
          <Clock size={14} />
          <span>{formatTime(lastReceivedTimestamp)}</span>
        </div>

        {/* Notifications Icon */}
        <button
          className="topbar-btn"
          onClick={onOpenAlerts}
          title={`${unreadAlertCount} active alerts`}
        >
          <Bell size={18} />
          {unreadAlertCount > 0 && (
            <span className="topbar-badge-count">
              {unreadAlertCount > 9 ? '9+' : unreadAlertCount}
            </span>
          )}
        </button>

        {/* User Profile */}
        <div className="topbar-user">
          <div className="user-avatar" title="Atomberg QA Engineer">
            AQ
          </div>
          <div className="user-info">
            <span className="user-name">Atomberg Lab</span>
            <span className="user-role">Purifier Track 2</span>
          </div>
        </div>
      </div>
    </header>
  );
}


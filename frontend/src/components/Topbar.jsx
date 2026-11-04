import React from 'react';
import { Clock, Layers, Menu, X } from 'lucide-react';

export default function Topbar({
  activeTab = 'overview',
  deviceName = 'AquaSense ESP32',
  deviceConnected = false,
  lastReceivedTimestamp = null,
  onToggleMobile = () => {},
  mobileOpen = false
}) {
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
    overview: 'Overview',
    live: 'Live Monitoring',
    analytics: 'Analytics',
    filter: 'Filter Health'
  };

  return (
    <header className="topbar">
      {/* Left: Mobile Hamburger Toggle + Breadcrumb/Title */}
      <div className="topbar-left">
        <button
          type="button"
          className="mobile-menu-btn"
          onClick={onToggleMobile}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          title={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="topbar-title-group">
          <div className="page-breadcrumb">
            <span>AquaSense AI</span>
            <span>/</span>
            <span>{pageTitles[activeTab] || 'Dashboard'}</span>
          </div>
          <h1 className="page-title-badge">{pageTitles[activeTab] || 'Dashboard'}</h1>
        </div>
      </div>

      {/* Right: Simulation Mode, Device Status, Timestamp */}
      <div className="topbar-right">
        {/* Simulation Mode Indicator */}
        <div className="simulation-mode-badge" title="Data is originating from Wokwi ESP32 Potentiometer Simulation">
          <Layers className="simulation-icon" />
          <span className="badge-text-full">Simulation Mode (Wokwi)</span>
          <span className="badge-text-compact">Wokwi Sim</span>
        </div>

        {/* Device Status */}
        <div className="topbar-device-pill" title={`Connected to ${deviceName}`}>
          <span className={`status-dot ${deviceConnected ? 'online' : 'offline'}`} />
          <span className="device-name-full">{deviceName}</span>
          <span className="device-name-compact">{deviceConnected ? 'Online' : 'Offline'}</span>
        </div>

        {/* Last Updated Timestamp */}
        <div className="topbar-timestamp" title="Last Sensor Data Telemetry">
          <Clock size={13} />
          <span>{formatTime(lastReceivedTimestamp)}</span>
        </div>
      </div>
    </header>
  );
}

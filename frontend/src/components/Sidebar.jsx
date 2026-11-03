import React from 'react';
import {
  LayoutDashboard,
  Activity,
  BarChart3,
  Bell,
  Filter,
  Cpu,
  Settings,
  ChevronLeft,
  Sparkles
} from 'lucide-react';

export default function Sidebar({
  activeTab = 'overview',
  onSelectTab = () => {},
  collapsed = false,
  onToggleCollapse = () => {},
  unreadAlertCount = 0,
  deviceConnected = false,
  wsConnected = false
}) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'live', label: 'Live Monitoring', icon: Activity },
    { id: 'analytics', label: 'Water Analytics', icon: BarChart3 },
    { id: 'alerts', label: 'Alerts & Notifications', icon: Bell, badge: unreadAlertCount },
    { id: 'filter', label: 'Filter Health', icon: Filter },
    { id: 'device', label: 'Device Management', icon: Cpu },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Brand Header */}
      <div className="sidebar-header">
        <a href="#overview" onClick={(e) => { e.preventDefault(); onSelectTab('overview'); }} className="sidebar-brand">
          <div className="brand-logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2.5C12 2.5 5 10.5 5 15.5C5 19.366 8.134 22.5 12 22.5C15.866 22.5 19 19.366 19 15.5C19 10.5 12 2.5 12 2.5Z" fill="white" fillOpacity="0.9" />
              <circle cx="12" cy="15.5" r="3.2" fill="#7B2CBF" />
              <path d="M12 7V11" stroke="#3B1259" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>
          <div className="brand-text-container">
            <span className="brand-title">
              AquaSense <span className="brand-tag">AI</span>
            </span>
            <span className="brand-subtitle">Atomberg atomQUEST</span>
          </div>
        </a>

        <button 
          className="sidebar-toggle-btn"
          onClick={onToggleCollapse}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft size={16} />
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        <span className="nav-section-title">Telemetry & Purifier</span>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                onSelectTab(item.id);
              }}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="nav-icon" />
              <span className="nav-label">{item.label}</span>
              {Boolean(item.badge) && item.badge > 0 && (
                <span className="nav-badge">{item.badge}</span>
              )}
            </a>
          );
        })}
      </nav>

      {/* Sidebar Footer - Connection Status */}
      <div className="sidebar-footer">
        <div className="connection-status-pill" title={deviceConnected ? "ESP32 Sensor Active" : "ESP32 Awaiting Connection"}>
          <span className={`status-dot ${deviceConnected ? 'online' : 'offline'}`} />
          <span>{deviceConnected ? 'ESP32 Streaming' : 'ESP32 Offline'}</span>
        </div>
      </div>
    </aside>
  );
}


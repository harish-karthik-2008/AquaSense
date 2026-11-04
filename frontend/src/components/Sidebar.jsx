import React from 'react';
import {
  LayoutDashboard,
  Activity,
  BarChart3,
  Filter,
  ChevronLeft,
  X
} from 'lucide-react';

export default function Sidebar({
  activeTab = 'overview',
  onSelectTab = () => {},
  collapsed = false,
  onToggleCollapse = () => {},
  deviceConnected = false,
  mobileOpen = false,
  onCloseMobile = () => {}
}) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'live', label: 'Live Monitoring', icon: Activity },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'filter', label: 'Filter Health', icon: Filter }
  ];

  const handleNavClick = (tabId) => {
    onSelectTab(tabId);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      <div
        className={`sidebar-backdrop ${mobileOpen ? 'active' : ''}`}
        onClick={onCloseMobile}
        aria-hidden="true"
      />

      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-header">
          <a 
            href="#overview" 
            onClick={(e) => { 
              e.preventDefault(); 
              handleNavClick('overview'); 
            }} 
            className="sidebar-brand"
          >
            <div className="brand-logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2.5C12 2.5 5 10.5 5 15.5C5 19.366 8.134 22.5 12 22.5C15.866 22.5 19 19.366 19 15.5C19 10.5 12 2.5 12 2.5Z" fill="#000000" />
                <circle cx="12" cy="15.5" r="3.2" fill="#FDB813" />
              </svg>
            </div>
            <div className="brand-text-container">
              <span className="brand-title">
                AquaSense <span className="brand-tag">AI</span>
              </span>
              <span className="brand-subtitle">Water Monitoring</span>
            </div>
          </a>

          {/* Desktop Collapse Toggle */}
          <button 
            type="button"
            className="sidebar-toggle-btn desktop-only"
            onClick={onToggleCollapse}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronLeft size={15} />
          </button>

          {/* Mobile Close Button */}
          <button
            type="button"
            className="sidebar-close-btn mobile-only"
            onClick={onCloseMobile}
            title="Close navigation menu"
            aria-label="Close navigation menu"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation (Only 4 Primary Pages) */}
        <nav className="sidebar-nav">
          <span className="nav-section-title">Navigation</span>

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
                  handleNavClick(item.id);
                }}
                title={collapsed ? item.label : undefined}
              >
                <Icon className="nav-icon" />
                <span className="nav-label">{item.label}</span>
              </a>
            );
          })}
        </nav>

        {/* Sidebar Footer: Connection Indicator */}
        <div className="sidebar-footer">
          <div className="connection-status-pill" title={deviceConnected ? "ESP32 Sensor Active" : "ESP32 Awaiting Connection"}>
            <span className={`status-dot ${deviceConnected ? 'online' : 'offline'}`} />
            <span>{deviceConnected ? 'ESP32 Online' : 'ESP32 Offline'}</span>
          </div>
        </div>
      </aside>
    </>
  );
}

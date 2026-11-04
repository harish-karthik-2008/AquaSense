import React, { useState, useRef, useEffect } from 'react';
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  Check,
  CheckCheck,
  Trash2,
  Filter,
  X,
  ExternalLink,
  Clock,
  Sparkles,
  Layers,
  Droplet
} from 'lucide-react';

export default function NotificationPanel({
  notifications = [],
  unreadCount = 0,
  isOpen = false,
  onClose = () => {},
  onMarkAsRead = () => {},
  onMarkAllAsRead = () => {},
  onAcknowledge = () => {},
  onAcknowledgeAll = () => {},
  onClearAcknowledged = () => {},
  onViewAllAlerts = () => {},
  isLoading = false
}) {
  const [severityFilter, setSeverityFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'unread' | 'acknowledged'
  const panelRef = useRef(null);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        // Check if click was on the bell button itself
        const bellBtn = document.querySelector('.notification-bell-btn');
        if (bellBtn && bellBtn.contains(e.target)) return;
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Format relative timestamp
  const formatTime = (ts) => {
    if (!ts) return 'Just now';
    try {
      const date = new Date(ts);
      const now = new Date();
      const diffSec = Math.floor((now - date) / 1000);

      if (diffSec < 10) return 'Just now';
      if (diffSec < 60) return `${diffSec}s ago`;
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'Recently';
    }
  };

  // Filtered notifications
  const filtered = notifications.filter((item) => {
    // Severity
    if (severityFilter !== 'All' && item.severity !== severityFilter) return false;
    // Category
    if (categoryFilter !== 'All' && item.category !== categoryFilter) return false;
    // Status
    if (statusFilter === 'unread' && item.is_read) return false;
    if (statusFilter === 'acknowledged' && !item.is_acknowledged) return false;
    return true;
  });

  if (!isOpen) return null;

  return (
    <div
      ref={panelRef}
      className="notification-dropdown-panel"
      style={{
        position: 'absolute',
        top: 'calc(100% + 10px)',
        right: '0',
        width: '420px',
        maxWidth: '92vw',
        maxHeight: '82vh',
        backgroundColor: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-light)',
        boxShadow: '0 12px 36px rgba(46, 8, 84, 0.16)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 100,
        overflow: 'hidden',
        animation: 'fadeInSlideDown 0.18s ease-out'
      }}
    >
      <style>{`
        @keyframes fadeInSlideDown {
          from { opacity: 0; transform: translateY(-6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .notification-item-card:hover {
          background-color: #F8FAFC !important;
        }
      `}</style>
      {/* PANEL HEADER */}
      <div style={{
        padding: '1rem 1.25rem',
        borderBottom: '1px solid var(--border-light)',
        backgroundColor: 'var(--brand-purple-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            width: 32,
            height: 32,
            borderRadius: 'var(--radius-sm)',
            background: 'var(--brand-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}>
            <Bell size={16} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h3 style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--brand-primary)', margin: 0 }}>
                Notifications
              </h3>
              {unreadCount > 0 && (
                <span style={{
                  backgroundColor: 'var(--status-critical)',
                  color: '#FFFFFF',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  padding: '0.1rem 0.45rem',
                  borderRadius: 'var(--radius-full)'
                }}>
                  {unreadCount} new
                </span>
              )}
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Real-time events & system alerts
            </span>
          </div>
        </div>

        {/* Global Batch Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {unreadCount > 0 && (
            <button
              onClick={onMarkAllAsRead}
              className="atom-btn atom-btn-secondary"
              style={{ padding: '0.3rem 0.6rem', fontSize: '0.72rem' }}
              title="Mark all notifications as read"
            >
              <Check size={13} />
              <span>Mark all read</span>
            </button>
          )}

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 'var(--radius-xs)'
            }}
            title="Close notifications"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* FILTERS BAR */}
      <div style={{
        padding: '0.65rem 1rem',
        borderBottom: '1px solid var(--border-subtle)',
        backgroundColor: '#FAFBFF',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem'
      }}>
        {/* Severity Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', overflowX: 'auto' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: '0.25rem' }}>
            Severity:
          </span>
          {['All', 'Critical', 'Warning', 'Informational'].map((sev) => {
            const isActive = severityFilter === sev;
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                style={{
                  fontSize: '0.72rem',
                  fontWeight: isActive ? 700 : 500,
                  padding: '0.2rem 0.55rem',
                  borderRadius: 'var(--radius-full)',
                  border: '1px solid',
                  borderColor: isActive ? 'var(--brand-primary)' : 'var(--border-light)',
                  backgroundColor: isActive ? 'var(--brand-primary)' : '#FFFFFF',
                  color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease'
                }}
              >
                {sev}
              </button>
            );
          })}
        </div>

        {/* Category & Status Filter Row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              fontSize: '0.74rem',
              padding: '0.25rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-light)',
              backgroundColor: '#FFFFFF',
              color: 'var(--text-primary)',
              cursor: 'pointer'
            }}
          >
            <option value="All">All Categories</option>
            <option value="Water Quality">Water Quality</option>
            <option value="AI Anomaly">AI Anomaly</option>
            <option value="Filter Maintenance">Filter Maintenance</option>
            <option value="System">System</option>
          </select>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <button
              onClick={() => setStatusFilter(statusFilter === 'unread' ? 'all' : 'unread')}
              style={{
                fontSize: '0.72rem',
                fontWeight: statusFilter === 'unread' ? 700 : 500,
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid',
                borderColor: statusFilter === 'unread' ? 'var(--brand-accent)' : 'var(--border-light)',
                backgroundColor: statusFilter === 'unread' ? 'var(--brand-purple-subtle)' : '#FFFFFF',
                color: statusFilter === 'unread' ? 'var(--brand-accent)' : 'var(--text-muted)',
                cursor: 'pointer'
              }}
            >
              Unread only
            </button>
          </div>
        </div>
      </div>

      {/* NOTIFICATION LIST BODY */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        maxHeight: '380px',
        padding: '0.5rem 0'
      }}>
        {isLoading ? (
          <div style={{ padding: '2.5rem 1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            Loading notification events...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '2.5rem 1rem', textAlign: 'center' }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-full)',
              backgroundColor: 'var(--bg-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 0.75rem auto',
              color: 'var(--text-muted)'
            }}>
              <CheckCheck size={22} />
            </div>
            <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 0.25rem 0' }}>
              No notifications found
            </p>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              All systems operating within calibrated baseline parameters.
            </span>
          </div>
        ) : (
          filtered.map((item) => {
            const isCrit = item.severity === 'Critical';
            const isWarn = item.severity === 'Warning';
            const isInfo = item.severity === 'Informational';

            // Severity styling
            const iconBg = isCrit
              ? 'rgba(239, 68, 68, 0.12)'
              : isWarn
              ? 'rgba(245, 158, 11, 0.12)'
              : 'rgba(59, 130, 246, 0.12)';
            const iconColor = isCrit
              ? 'var(--status-critical)'
              : isWarn
              ? 'var(--status-warning)'
              : 'var(--status-info)';
            const IconComponent = isCrit ? AlertCircle : isWarn ? AlertTriangle : Info;

            return (
              <div
                key={item.id}
                style={{
                  padding: '0.85rem 1.15rem',
                  borderBottom: '1px solid var(--border-subtle)',
                  backgroundColor: !item.is_read ? 'rgba(123, 44, 191, 0.03)' : '#FFFFFF',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem',
                  transition: 'background-color 0.15s ease',
                  position: 'relative'
                }}
                className="notification-item-card"
              >
                {/* Unread Indicator Dot */}
                {!item.is_read && (
                  <span
                    style={{
                      position: 'absolute',
                      left: '6px',
                      top: '16px',
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--brand-accent)'
                    }}
                    title="Unread notification"
                  />
                )}

                {/* Severity Icon */}
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: iconBg,
                  color: iconColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '2px'
                }}>
                  <IconComponent size={16} />
                </div>

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.4rem', marginBottom: '0.2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        padding: '0.1rem 0.35rem',
                        borderRadius: 'var(--radius-xs)',
                        backgroundColor: iconBg,
                        color: iconColor
                      }}>
                        {item.severity}
                      </span>

                      {item.parameter && (
                        <span style={{
                          fontSize: '0.68rem',
                          fontWeight: 600,
                          backgroundColor: 'var(--bg-subtle)',
                          color: 'var(--text-secondary)',
                          padding: '0.1rem 0.35rem',
                          borderRadius: 'var(--radius-xs)'
                        }}>
                          {item.parameter}
                        </span>
                      )}

                      {item.occurrence_count > 1 && (
                        <span style={{
                          fontSize: '0.65rem',
                          fontWeight: 700,
                          backgroundColor: 'var(--brand-purple-subtle)',
                          color: 'var(--brand-primary)',
                          padding: '0.1rem 0.35rem',
                          borderRadius: 'var(--radius-xs)'
                        }}>
                          ×{item.occurrence_count}
                        </span>
                      )}
                    </div>

                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {formatTime(item.created_at)}
                    </span>
                  </div>

                  <h4 style={{
                    fontSize: '0.84rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    margin: '0 0 0.2rem 0',
                    lineHeight: 1.3
                  }}>
                    {item.title}
                  </h4>

                  <p style={{
                    fontSize: '0.76rem',
                    color: 'var(--text-secondary)',
                    margin: '0 0 0.4rem 0',
                    lineHeight: 1.4
                  }}>
                    {item.message}
                  </p>

                  {/* Telemetry metrics & Action */}
                  {item.suggested_action && (
                    <div style={{
                      fontSize: '0.72rem',
                      color: 'var(--brand-primary)',
                      backgroundColor: 'var(--brand-purple-subtle)',
                      padding: '0.3rem 0.5rem',
                      borderRadius: 'var(--radius-xs)',
                      marginBottom: '0.4rem',
                      lineHeight: 1.3
                    }}>
                      <b>Action:</b> {item.suggested_action}
                    </div>
                  )}

                  {/* Item Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.35rem' }}>
                    {!item.is_read && (
                      <button
                        onClick={() => onMarkAsRead(item.id)}
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          color: 'var(--brand-accent)',
                          background: 'none',
                          border: 'none',
                          padding: 0,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.2rem'
                        }}
                      >
                        <Check size={12} />
                        <span>Mark as read</span>
                      </button>
                    )}

                    {!item.is_acknowledged ? (
                      <button
                        onClick={() => onAcknowledge(item.id)}
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          color: 'var(--text-muted)',
                          background: 'none',
                          border: 'none',
                          padding: 0,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.2rem'
                        }}
                      >
                        <CheckCheck size={12} />
                        <span>Acknowledge</span>
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.68rem', color: 'var(--status-normal)', fontWeight: 600 }}>
                        ✓ Acknowledged
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* FOOTER ACTIONS */}
      <div style={{
        padding: '0.75rem 1.15rem',
        borderTop: '1px solid var(--border-light)',
        backgroundColor: '#FFFFFF',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.74rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={onAcknowledgeAll}
            className="atom-btn atom-btn-secondary"
            style={{ padding: '0.3rem 0.6rem', fontSize: '0.72rem' }}
            title="Acknowledge all notifications"
          >
            <CheckCheck size={13} />
            <span>Acknowledge All</span>
          </button>

          <button
            onClick={onClearAcknowledged}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.2rem',
              fontSize: '0.72rem'
            }}
            title="Clear acknowledged events"
          >
            <Trash2 size={13} />
            <span>Clear</span>
          </button>
        </div>

        <button
          onClick={() => {
            onClose();
            onViewAllAlerts();
          }}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--brand-primary)',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem'
          }}
        >
          <span>View Alerts Hub</span>
          <ExternalLink size={12} />
        </button>
      </div>
    </div>
  );
}

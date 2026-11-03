import React, { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  Filter,
  ShieldAlert,
  ArrowRight,
  Info,
  Clock,
  Sparkles
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

export default function Alerts({
  alerts = [],
  onAcknowledge = () => {},
  onAcknowledgeAll = () => {},
  onClearAcknowledged = () => {}
}) {
  const [filterTab, setFilterTab] = useState('all'); // 'all' | 'active' | 'acknowledged'

  const activeCount = alerts.filter((a) => !a.acknowledged).length;
  const acknowledgedCount = alerts.filter((a) => a.acknowledged).length;

  const filteredAlerts = alerts.filter((a) => {
    if (filterTab === 'active') return !a.acknowledged;
    if (filterTab === 'acknowledged') return a.acknowledged;
    return true;
  });

  return (
    <div>
      {/* Header Bar */}
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem 1.75rem',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-card)',
        marginBottom: '1.75rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: 42,
            height: 42,
            borderRadius: 'var(--radius-md)',
            background: activeCount > 0 ? 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)' : 'var(--brand-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff'
          }}>
            <Bell size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                Smart Alerts & Incident Response
              </h2>
              {activeCount > 0 && (
                <span className="status-pill critical" style={{ fontSize: '0.72rem' }}>
                  {activeCount} Active Issues
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Intelligent threshold monitoring, AI multivariate anomaly alarms, and purifier maintenance triggers.
            </p>
          </div>
        </div>

        {/* Global Alert Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            className="atom-btn atom-btn-secondary atom-btn-sm"
            onClick={onAcknowledgeAll}
            disabled={activeCount === 0}
            title="Mark all active alerts as acknowledged"
          >
            <CheckCircle2 size={15} />
            <span>Acknowledge All</span>
          </button>

          <button
            className="atom-btn atom-btn-outline atom-btn-sm"
            onClick={onClearAcknowledged}
            disabled={acknowledgedCount === 0}
            title="Clear all previously acknowledged alerts"
          >
            <Trash2 size={15} />
            <span>Clear History</span>
          </button>
        </div>
      </div>

      {/* Tabs & Deduplication Notice */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.25rem'
      }}>
        {/* Filter Tabs */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          backgroundColor: 'var(--bg-subtle)',
          padding: '0.25rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)'
        }}>
          {[
            { id: 'all', label: `All Alerts (${alerts.length})` },
            { id: 'active', label: `Active (${activeCount})` },
            { id: 'acknowledged', label: `Acknowledged (${acknowledgedCount})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterTab(tab.id)}
              style={{
                padding: '0.35rem 0.85rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.78rem',
                fontWeight: 600,
                color: filterTab === tab.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                backgroundColor: filterTab === tab.id ? '#FFFFFF' : 'transparent',
                boxShadow: filterTab === tab.id ? '0 1px 4px rgba(0,0,0,0.06)' : 'none',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Deduplication & Debounce Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          fontSize: '0.75rem',
          color: 'var(--text-muted)'
        }}>
          <Info size={14} />
          <span>Smart Deduplication: Repeated identical alerts are debounced to prevent clutter.</span>
        </div>
      </div>

      {/* ALERTS LIST */}
      {filteredAlerts.length === 0 ? (
        <div className="empty-state-box">
          <div className="empty-state-icon" style={{ backgroundColor: 'var(--status-normal-bg)', color: 'var(--status-normal)' }}>
            <CheckCircle2 size={32} />
          </div>
          <h3 className="empty-state-title">No Alerts in this Category</h3>
          <p className="empty-state-desc">
            {filterTab === 'active' 
              ? 'Great news! There are currently no unresolved water quality or purifier alert conditions.'
              : 'Alert list is clean and operational.'}
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filteredAlerts.map((alert) => {
            const isCrit = alert.severity === 'Critical';
            const isWarn = alert.severity === 'Warning';
            const isAnomaly = alert.alert_type === 'Anomaly';

            return (
              <div
                key={alert.id}
                className={`alert-card ${isCrit ? 'critical' : isWarn ? 'warning' : 'info'} ${alert.acknowledged ? 'acknowledged' : ''}`}
              >
                <div className="alert-icon-box">
                  {isAnomaly ? <Sparkles size={20} /> : <AlertTriangle size={20} />}
                </div>

                <div className="alert-content">
                  <div className="alert-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span className="alert-title">{alert.title}</span>
                      <StatusBadge status={alert.severity} />
                      <span style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        backgroundColor: 'var(--bg-subtle)',
                        padding: '0.15rem 0.45rem',
                        borderRadius: 'var(--radius-xs)',
                        color: 'var(--text-secondary)'
                      }}>
                        {alert.alert_type} • {alert.parameter}
                      </span>
                    </div>

                    <span className="alert-time">
                      {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>

                  <p className="alert-msg">{alert.message}</p>

                  {/* Telemetry Comparison Baseline */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1.5rem',
                    fontSize: '0.76rem',
                    color: 'var(--text-secondary)',
                    marginBottom: '0.65rem'
                  }}>
                    {alert.reading_value !== null && alert.reading_value !== undefined && (
                      <span>
                        Current Reading: <b style={{ color: 'var(--text-primary)' }}>{alert.reading_value}</b>
                      </span>
                    )}
                    {alert.threshold_value && (
                      <span>
                        Configured Limit: <b style={{ color: 'var(--text-primary)' }}>{alert.threshold_value}</b>
                      </span>
                    )}
                  </div>

                  {/* Suggested Action Box */}
                  {alert.suggested_action && (
                    <div className="alert-action-box">
                      <span style={{ fontWeight: 700 }}>Recommended Action:</span>
                      <span>{alert.suggested_action}</span>
                    </div>
                  )}

                  {/* Acknowledge Button */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                    {!alert.acknowledged ? (
                      <button
                        className="atom-btn atom-btn-outline atom-btn-sm"
                        onClick={() => onAcknowledge(alert.id)}
                      >
                        <CheckCircle2 size={13} />
                        <span>Acknowledge Alert</span>
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.72rem', color: 'var(--status-normal)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <CheckCircle2 size={13} /> Acknowledged by User
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


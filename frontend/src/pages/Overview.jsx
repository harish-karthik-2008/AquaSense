import React from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Clock,
  Layers,
  Cpu,
  CheckCircle2
} from 'lucide-react';
import SensorCard from '../components/SensorCard';
import LiveLineChart from '../charts/LiveLineChart';
import StatusBadge from '../components/StatusBadge';

export default function Overview({
  latestReading = null,
  previousReading = null,
  recentReadings = [],
  activeAlerts = [],
  deviceStatus = {},
  filterHealth = {},
  settings = {},
  onNavigate = () => {},
  onAcknowledgeAlert = () => {}
}) {
  const currentTds = latestReading?.tds ?? 165.0;
  const currentPh = latestReading?.ph ?? 7.35;
  const currentTurbidity = latestReading?.turbidity ?? 1.4;

  const prevTds = previousReading?.tds ?? null;
  const prevPh = previousReading?.ph ?? null;
  const prevTurbidity = previousReading?.turbidity ?? null;

  const overallStatus = latestReading?.overall_status ?? 'Normal';
  const isOnline = deviceStatus?.is_online ?? false;
  const lastSeen = latestReading?.timestamp || deviceStatus?.last_seen;

  const formatTime = (ts) => {
    if (!ts) return 'Awaiting data';
    try {
      const dt = new Date(ts);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return ts;
    }
  };

  // Threshold labels
  const tdsThresholdText = `Threshold: < ${settings?.tds_warning_threshold || 300} ppm`;
  const phThresholdText = `Range: ${settings?.ph_min_acceptable || 6.5} - ${settings?.ph_max_acceptable || 8.5}`;
  const turbThresholdText = `Threshold: < ${settings?.turbidity_warning_threshold || 5.0} (sim)`;

  return (
    <div>
      {/* 1. Header Overview Bar */}
      <div className="dashboard-header-card">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#000000', letterSpacing: '-0.02em' }}>
              Water Quality Overview
            </h2>
            <StatusBadge status={overallStatus} />
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Real-time water quality monitoring powered by AquaSense AI.
          </p>
        </div>

        {/* Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          {/* Device Connection Status */}
          <div className="topbar-device-pill">
            <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
            <span>{isOnline ? 'ESP32 Connected' : 'ESP32 Offline'}</span>
          </div>

          {/* Simulation Mode Indicator */}
          <div className="simulation-mode-badge">
            <Layers className="simulation-icon" />
            <span>Simulation Mode (Wokwi)</span>
          </div>

          {/* Last Updated Timestamp */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.76rem',
            color: 'var(--text-secondary)',
            padding: '0.3rem 0.65rem',
            backgroundColor: '#FAFAFA',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-xs)'
          }}>
            <Clock size={12} />
            <span>Updated: {formatTime(lastSeen)}</span>
          </div>
        </div>
      </div>

      {/* 2. Three Sensor Summary Cards */}
      <div className="sensor-card-grid">
        <SensorCard
          type="tds"
          title="TDS – Total Dissolved Solids"
          value={currentTds}
          unit="ppm"
          status={latestReading?.tds_status || 'Normal'}
          previousValue={prevTds}
          thresholdText={tdsThresholdText}
          settings={settings}
        />

        <SensorCard
          type="ph"
          title="pH – Acidity & Alkalinity"
          value={currentPh}
          unit="pH"
          status={latestReading?.ph_status || 'Normal'}
          previousValue={prevPh}
          thresholdText={phThresholdText}
          settings={settings}
        />

        <SensorCard
          type="turbidity"
          title="Turbidity (Simulated Scale)"
          value={currentTurbidity}
          unit=""
          status={latestReading?.turbidity_status || 'Normal'}
          previousValue={prevTurbidity}
          thresholdText={turbThresholdText}
          settings={settings}
          isSimulated={true}
        />
      </div>

      {/* 3. Small Water-Quality Trend Chart & Latest Alerts Section */}
      <div className="overview-grid-split">
        {/* Small Water Quality Trend Chart */}
        <div className="atom-card">
          <div className="atom-card-header">
            <div>
              <h3 className="card-title">Water Quality Trend</h3>
              <p className="card-subtitle">Real-time incoming telemetry from ESP32</p>
            </div>
            <button 
              className="atom-btn atom-btn-secondary atom-btn-sm"
              onClick={() => onNavigate('live')}
            >
              Live Telemetry <ArrowRight size={13} />
            </button>
          </div>

          <LiveLineChart data={recentReadings.slice(-15)} activeMetric="all" height={260} />
        </div>

        {/* Latest Alerts Section (Integrated directly on Overview) */}
        <div className="atom-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="atom-card-header">
            <div className="card-title-group">
              <div className="card-icon-bubble" style={{ 
                backgroundColor: activeAlerts.length > 0 ? 'var(--status-critical-bg)' : 'var(--status-normal-bg)',
                borderColor: activeAlerts.length > 0 ? 'var(--status-critical-border)' : 'var(--status-normal-border)'
              }}>
                <AlertTriangle size={18} color={activeAlerts.length > 0 ? 'var(--status-critical)' : 'var(--status-normal)'} />
              </div>
              <div>
                <h3 className="card-title">Latest Alerts</h3>
                <span className="card-subtitle">
                  {activeAlerts.length > 0 ? `${activeAlerts.length} active notification(s)` : 'System normal'}
                </span>
              </div>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', maxHeight: '290px' }}>
            {activeAlerts.length === 0 ? (
              <div className="empty-state-box" style={{ padding: '2rem 1rem' }}>
                <div className="empty-state-icon" style={{ backgroundColor: 'var(--status-normal-bg)', color: 'var(--status-normal)', width: 40, height: 40 }}>
                  <ShieldCheck size={24} />
                </div>
                <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#065f46', marginBottom: '0.2rem' }}>
                  All Parameters Normal
                </h4>
                <p style={{ fontSize: '0.76rem', color: '#047857' }}>
                  TDS, pH, and turbidity values are within safe acceptable drinking thresholds.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {activeAlerts.slice(0, 3).map((alert) => (
                  <div
                    key={alert.id}
                    className={`alert-item-card ${alert.severity === 'Critical' ? 'critical' : 'warning'}`}
                    style={{ padding: '0.75rem 0.95rem', marginBottom: 0 }}
                  >
                    <div className="alert-body">
                      <div className="alert-top">
                        <div className="alert-headline">
                          <span className="alert-title-text">{alert.title}</span>
                          <StatusBadge status={alert.severity} />
                        </div>
                        <span className="alert-time-text">
                          {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>

                      <p className="alert-desc-text" style={{ marginBottom: '0.35rem' }}>
                        {alert.message}
                      </p>

                      <div className="alert-metrics-line" style={{ marginBottom: '0.35rem' }}>
                        <span>Parameter: <b>{alert.parameter}</b></span>
                        {alert.reading_value !== null && alert.reading_value !== undefined && (
                          <span>Reading: <b>{alert.reading_value}</b></span>
                        )}
                        {alert.threshold_value && (
                          <span>Limit: <b>{alert.threshold_value}</b></span>
                        )}
                      </div>

                      {alert.suggested_action && (
                        <div className="alert-action-line" style={{ marginBottom: '0.45rem' }}>
                          <b>Action:</b> {alert.suggested_action}
                        </div>
                      )}

                      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                          className="atom-btn atom-btn-outline atom-btn-sm"
                          onClick={() => onAcknowledgeAlert(alert.id)}
                          style={{ padding: '0.2rem 0.55rem', fontSize: '0.7rem' }}
                        >
                          <CheckCircle2 size={12} />
                          <span>Acknowledge</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

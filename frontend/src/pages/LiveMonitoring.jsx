import React, { useState } from 'react';
import {
  Activity,
  Play,
  Pause,
  RotateCcw,
  Clock,
  Layers,
  AlertTriangle,
  CheckCircle2,
  ShieldCheck
} from 'lucide-react';
import LiveLineChart from '../charts/LiveLineChart';
import SensorCard from '../components/SensorCard';
import StatusBadge from '../components/StatusBadge';

export default function LiveMonitoring({
  latestReading = null,
  previousReading = null,
  recentReadings = [],
  activeAlerts = [],
  deviceStatus = {},
  settings = {},
  isPaused = false,
  onTogglePause = () => {},
  onClearBuffer = () => {},
  onAcknowledgeAlert = () => {}
}) {
  const currentTds = latestReading?.tds ?? 165.0;
  const currentPh = latestReading?.ph ?? 7.35;
  const currentTurbidity = latestReading?.turbidity ?? 1.4;

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

  return (
    <div>
      {/* 1. Header Bar */}
      <div className="dashboard-header-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
          <div className="brand-logo-icon" style={{ width: 36, height: 36, borderRadius: 'var(--radius-xs)' }}>
            <Activity size={20} color="#000000" />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#000000' }}>
                Live Sensor Telemetry
              </h2>
              <span className={`status-pill ${isOnline ? 'normal' : 'critical'}`}>
                <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
                {isOnline ? 'Live WebSocket' : 'Disconnected'}
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Real-time data streaming directly from simulated Wokwi ESP32 potentiometers.
            </p>
          </div>
        </div>

        {/* Timestamp & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.76rem',
            color: 'var(--text-secondary)',
            padding: '0.35rem 0.65rem',
            backgroundColor: '#FAFAFA',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-xs)'
          }}>
            <Clock size={12} />
            <span>Latest: {formatTime(lastSeen)}</span>
          </div>

          <button
            className={`atom-btn ${isPaused ? 'atom-btn-primary' : 'atom-btn-secondary'} atom-btn-sm`}
            onClick={onTogglePause}
            title={isPaused ? "Resume real-time data plotting" : "Pause incoming plot updates"}
          >
            {isPaused ? <Play size={13} /> : <Pause size={13} />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          <button
            className="atom-btn atom-btn-secondary atom-btn-sm"
            onClick={onClearBuffer}
            title="Clear live chart data points buffer"
          >
            <RotateCcw size={13} />
            <span>Clear Buffer</span>
          </button>
        </div>
      </div>

      {/* 2. Three Live Sensor Cards */}
      <div className="sensor-card-grid">
        <SensorCard
          type="tds"
          title="Live TDS"
          value={currentTds}
          unit="ppm"
          status={latestReading?.tds_status || 'Normal'}
          previousValue={previousReading?.tds}
          thresholdText={`Warning: > ${settings?.tds_warning_threshold || 300} ppm`}
          settings={settings}
        />

        <SensorCard
          type="ph"
          title="Live pH"
          value={currentPh}
          unit="pH"
          status={latestReading?.ph_status || 'Normal'}
          previousValue={previousReading?.ph}
          thresholdText={`Range: ${settings?.ph_min_acceptable || 6.5} - ${settings?.ph_max_acceptable || 8.5}`}
          settings={settings}
        />

        <SensorCard
          type="turbidity"
          title="Live Turbidity (Simulated)"
          value={currentTurbidity}
          unit=""
          status={latestReading?.turbidity_status || 'Normal'}
          previousValue={previousReading?.turbidity}
          thresholdText={`Warning: > ${settings?.turbidity_warning_threshold || 5.0} (sim)`}
          settings={settings}
          isSimulated={true}
        />
      </div>

      {/* 3. Three Dynamically Updating Charts */}
      <div className="live-charts-grid">
        {/* Chart 1: TDS Live */}
        <div className="atom-card">
          <div className="atom-card-header" style={{ marginBottom: '0.5rem' }}>
            <div>
              <h4 className="card-title" style={{ fontSize: '0.9rem' }}>TDS Waveform (ppm)</h4>
              <span className="card-subtitle">Real-time salt & mineral rejection</span>
            </div>
            <span style={{ fontWeight: 800, color: '#000000', fontSize: '1rem' }}>
              {Number(currentTds).toFixed(1)} <small style={{ fontSize: '0.7rem', color: '#666' }}>ppm</small>
            </span>
          </div>
          <LiveLineChart data={recentReadings} activeMetric="tds" height={210} showLegend={false} />
        </div>

        {/* Chart 2: pH Live */}
        <div className="atom-card">
          <div className="atom-card-header" style={{ marginBottom: '0.5rem' }}>
            <div>
              <h4 className="card-title" style={{ fontSize: '0.9rem' }}>pH Level Waveform</h4>
              <span className="card-subtitle">Acidity & alkalinity monitoring</span>
            </div>
            <span style={{ fontWeight: 800, color: '#10B981', fontSize: '1rem' }}>
              {Number(currentPh).toFixed(2)} <small style={{ fontSize: '0.7rem', color: '#666' }}>pH</small>
            </span>
          </div>
          <LiveLineChart data={recentReadings} activeMetric="ph" height={210} showLegend={false} />
        </div>

        {/* Chart 3: Turbidity Live */}
        <div className="atom-card">
          <div className="atom-card-header" style={{ marginBottom: '0.5rem' }}>
            <div>
              <h4 className="card-title" style={{ fontSize: '0.9rem' }}>Turbidity (Simulated)</h4>
              <span className="card-subtitle">Suspended particle clarity index</span>
            </div>
            <span style={{ fontWeight: 800, color: '#D97706', fontSize: '1rem' }}>
              {Number(currentTurbidity).toFixed(1)} <small style={{ fontSize: '0.7rem', color: '#666' }}>(sim)</small>
            </span>
          </div>
          <LiveLineChart data={recentReadings} activeMetric="turbidity" height={210} showLegend={false} />
        </div>
      </div>

      {/* 4. Bottom Section: Latest Readings Table & Live Active Alerts */}
      <div className="live-bottom-grid">
        {/* Latest Sensor Readings Table */}
        <div className="atom-card">
          <div className="atom-card-header">
            <div>
              <h3 className="card-title">Latest Sensor Stream Log</h3>
              <p className="card-subtitle">Incoming packets received from ESP32</p>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Last {Math.min(recentReadings.length, 8)} samples
            </span>
          </div>

          <div className="atom-table-wrapper">
            <table className="atom-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>TDS (ppm)</th>
                  <th>pH</th>
                  <th>Turbidity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentReadings.slice(-8).reverse().map((r, i) => {
                  const time = new Date(r.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  });
                  return (
                    <tr key={r.id || r._id || i}>
                      <td style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{time}</td>
                      <td style={{ fontWeight: 700, color: '#000000' }}>{Number(r.tds).toFixed(1)}</td>
                      <td style={{ fontWeight: 700, color: '#10B981' }}>{Number(r.ph).toFixed(2)}</td>
                      <td style={{ fontWeight: 700, color: '#D97706' }}>{Number(r.turbidity).toFixed(1)}</td>
                      <td><StatusBadge status={r.overall_status || 'Normal'} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Active Alerts Panel (Requested for Live Monitoring page too!) */}
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
                <h3 className="card-title">Active Alerts</h3>
                <span className="card-subtitle">
                  {activeAlerts.length} unresolved condition(s)
                </span>
              </div>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', maxHeight: '280px' }}>
            {activeAlerts.length === 0 ? (
              <div className="empty-state-box" style={{ padding: '2rem 1rem' }}>
                <div className="empty-state-icon" style={{ backgroundColor: 'var(--status-normal-bg)', color: 'var(--status-normal)', width: 40, height: 40 }}>
                  <ShieldCheck size={24} />
                </div>
                <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#065f46', marginBottom: '0.2rem' }}>
                  No Active Alerts
                </h4>
                <p style={{ fontSize: '0.76rem', color: '#047857' }}>
                  All simulated water parameters are within acceptable thresholds.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                {activeAlerts.map((alert) => (
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

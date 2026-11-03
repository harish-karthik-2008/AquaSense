import React, { useState } from 'react';
import {
  Activity,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  Radio,
  Clock,
  Layers,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import LiveLineChart from '../charts/LiveLineChart';
import SensorCard from '../components/SensorCard';
import StatusBadge from '../components/StatusBadge';

export default function LiveMonitoring({
  latestReading = null,
  previousReading = null,
  recentReadings = [],
  deviceStatus = {},
  settings = {},
  isPaused = false,
  onTogglePause = () => {},
  onClearBuffer = () => {}
}) {
  const [activeMetric, setActiveMetric] = useState('all'); // 'all' | 'tds' | 'ph' | 'turbidity'

  const currentTds = latestReading?.tds ?? 165.0;
  const currentPh = latestReading?.ph ?? 7.35;
  const currentTurbidity = latestReading?.turbidity ?? 1.4;

  const isOnline = deviceStatus?.is_online ?? false;

  return (
    <div>
      {/* Page Header Bar */}
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
            background: 'var(--brand-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff'
          }}>
            <Activity size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                Live Water Quality Cockpit
              </h2>
              <span className={`status-pill ${isOnline ? 'normal' : 'critical'}`}>
                <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
                {isOnline ? 'Live Socket Stream' : 'Disconnected'}
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Direct WebSocket stream receiving simulated potentiometer inputs from ESP32.
            </p>
          </div>
        </div>

        {/* Streaming Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            className={`atom-btn ${isPaused ? 'atom-btn-primary' : 'atom-btn-secondary'} atom-btn-sm`}
            onClick={onTogglePause}
            title={isPaused ? "Resume real-time data plotting" : "Pause incoming plot updates"}
          >
            {isPaused ? <Play size={14} /> : <Pause size={14} />}
            <span>{isPaused ? 'Resume Stream' : 'Pause Stream'}</span>
          </button>

          <button
            className="atom-btn atom-btn-outline atom-btn-sm"
            onClick={onClearBuffer}
            title="Clear live chart data points buffer"
          >
            <RotateCcw size={14} />
            <span>Reset Buffer</span>
          </button>
        </div>
      </div>

      {/* THREE LIVE SENSOR CARDS */}
      <div className="sensor-card-grid">
        <SensorCard
          type="tds"
          title="TDS – Total Dissolved Solids"
          value={currentTds}
          unit="ppm"
          status={latestReading?.tds_status || 'Normal'}
          previousValue={previousReading?.tds}
          thresholdText={`Warning: > ${settings?.tds_warning_threshold || 300} ppm`}
          settings={settings}
        />

        <SensorCard
          type="ph"
          title="pH – Acidity & Alkalinity"
          value={currentPh}
          unit="pH"
          status={latestReading?.ph_status || 'Normal'}
          previousValue={previousReading?.ph}
          thresholdText={`Safe: ${settings?.ph_min_acceptable || 6.5} - ${settings?.ph_max_acceptable || 8.5}`}
          settings={settings}
        />

        <SensorCard
          type="turbidity"
          title="Turbidity (Simulated Scale)"
          value={currentTurbidity}
          unit=""
          status={latestReading?.turbidity_status || 'Normal'}
          previousValue={previousReading?.turbidity}
          thresholdText={`Warning: > ${settings?.turbidity_warning_threshold || 5.0} (sim)`}
          settings={settings}
          isSimulated={true}
        />
      </div>

      {/* LIVE INTERACTIVE CHART SECTION */}
      <div className="atom-card" style={{ marginBottom: '2rem' }}>
        <div className="atom-card-header" style={{ flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 className="card-title">Real-Time Waveform Monitor</h3>
            <p className="card-subtitle">
              Displaying last {recentReadings.length} readings received over WebSocket
            </p>
          </div>

          {/* Metric Selector Tabs */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'var(--bg-subtle)',
            padding: '0.25rem',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)'
          }}>
            {[
              { id: 'all', label: 'All Parameters' },
              { id: 'tds', label: 'TDS Only' },
              { id: 'ph', label: 'pH Only' },
              { id: 'turbidity', label: 'Turbidity Only' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveMetric(tab.id)}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: activeMetric === tab.id ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  backgroundColor: activeMetric === tab.id ? '#FFFFFF' : 'transparent',
                  boxShadow: activeMetric === tab.id ? '0 1px 4px rgba(0,0,0,0.06)' : 'none',
                  transition: 'all 0.15s ease'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <LiveLineChart data={recentReadings} activeMetric={activeMetric} />
      </div>

      {/* LIVE EVENT FEED & RAW DATA LOG */}
      <div className="atom-card">
        <div className="atom-card-header">
          <div>
            <h3 className="card-title">Live Sensor Ingestion Stream</h3>
            <p className="card-subtitle">
              Raw telemetry packets logged in MongoDB as received from ESP32
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Showing latest {Math.min(recentReadings.length, 12)} events
          </span>
        </div>

        <div className="atom-table-wrapper">
          <table className="atom-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Device ID</th>
                <th>TDS (ppm)</th>
                <th>pH</th>
                <th>Turbidity (Simulated)</th>
                <th>Water Purity</th>
                <th>AI Anomaly</th>
                <th>Overall Status</th>
              </tr>
            </thead>
            <tbody>
              {recentReadings.slice(-12).reverse().map((reading, index) => {
                const tsFormatted = new Date(reading.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                });

                return (
                  <tr key={reading.id || reading._id || index}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {tsFormatted}
                    </td>
                    <td>
                      <span style={{
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        backgroundColor: 'var(--bg-subtle)',
                        padding: '0.2rem 0.5rem',
                        borderRadius: 'var(--radius-xs)',
                        color: 'var(--brand-primary)'
                      }}>
                        {reading.device_id || 'AquaSense-ESP32'}
                      </span>
                    </td>
                    <td style={{ fontWeight: 700, color: '#7B2CBF' }}>
                      {Number(reading.tds).toFixed(1)}
                    </td>
                    <td style={{ fontWeight: 700, color: '#059669' }}>
                      {Number(reading.ph).toFixed(2)}
                    </td>
                    <td style={{ fontWeight: 700, color: '#D97706' }}>
                      {Number(reading.turbidity).toFixed(1)}
                    </td>
                    <td style={{ fontWeight: 700 }}>
                      {reading.water_quality_score || 95}%
                    </td>
                    <td>
                      {reading.anomaly_detected ? (
                        <span className="status-pill warning" style={{ fontSize: '0.68rem', padding: '0.2rem 0.45rem' }}>
                          Deviation
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Normal</span>
                      )}
                    </td>
                    <td>
                      <StatusBadge status={reading.overall_status || 'Normal'} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


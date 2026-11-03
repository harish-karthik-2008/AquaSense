import React from 'react';
import {
  Droplet,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Cpu
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
  onNavigate = () => {}
}) {
  const currentTds = latestReading?.tds ?? 165.0;
  const currentPh = latestReading?.ph ?? 7.35;
  const currentTurbidity = latestReading?.turbidity ?? 1.4;

  const prevTds = previousReading?.tds ?? null;
  const prevPh = previousReading?.ph ?? null;
  const prevTurbidity = previousReading?.turbidity ?? null;

  const wqi = latestReading?.water_quality_score ?? 96.0;
  const overallStatus = latestReading?.overall_status ?? 'Normal';
  const isOnline = deviceStatus?.is_online ?? false;

  // Threshold labels
  const tdsThresholdText = `Threshold: < ${settings?.tds_warning_threshold || 300} ppm`;
  const phThresholdText = `Range: ${settings?.ph_min_acceptable || 6.5} - ${settings?.ph_max_acceptable || 8.5}`;
  const turbThresholdText = `Threshold: < ${settings?.turbidity_warning_threshold || 5.0} (sim)`;

  // Filter overall condition
  const filterCondition = filterHealth?.overall_condition_pct ?? 78.0;

  return (
    <div>
      {/* Welcome & System Summary Bar */}
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: 'var(--radius-lg)',
        padding: '1.5rem 1.75rem',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-card)',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1.25rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--brand-primary)', letterSpacing: '-0.02em' }}>
              Water Quality Overview
            </h2>
            <StatusBadge status={overallStatus} />
          </div>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            Real-time multi-stage purifier telemetry monitored by AquaSense AI ecosystem.
          </p>
        </div>

        {/* Quick Summary Metrics */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.75rem', flexWrap: 'wrap' }}>
          {/* Water Quality Index */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-md)',
              background: 'var(--brand-gradient-purple)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff'
            }}>
              <ShieldCheck size={24} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.3rem' }}>
                <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                  {wqi}
                </span>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>/ 100</span>
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Water Purity Index
              </span>
            </div>
          </div>

          {/* Purifier Filter Health */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-md)',
              background: 'var(--brand-purple-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--brand-accent)'
            }}>
              <Droplet size={22} />
            </div>
            <div>
              <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                {filterCondition}%
              </span>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                Filter Health Condition
              </div>
            </div>
          </div>

          {/* Device Connectivity */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: 44,
              height: 44,
              borderRadius: 'var(--radius-md)',
              background: isOnline ? 'var(--status-normal-bg)' : 'var(--status-critical-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isOnline ? 'var(--status-normal)' : 'var(--status-critical)'
            }}>
              <Cpu size={22} />
            </div>
            <div>
              <span style={{ fontSize: '1rem', fontWeight: 700, color: isOnline ? '#065f46' : '#991b1b' }}>
                {isOnline ? 'Online (ESP32)' : 'Offline'}
              </span>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                {isOnline ? 'Active Stream' : 'Awaiting Heartbeat'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* THREE LARGE SENSOR CARDS */}
      <div className="sensor-card-grid">
        {/* CARD 1: TDS */}
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

        {/* CARD 2: pH */}
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

        {/* CARD 3: TURBIDITY */}
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

      {/* QUICK TRENDS & LIVE PREVIEW */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Real-time Mini Trend Chart */}
        <div className="atom-card">
          <div className="atom-card-header">
            <div>
              <h3 className="card-title">Live Water Quality Trend</h3>
              <p className="card-subtitle">Real-time incoming readings from ESP32 simulator</p>
            </div>
            <button 
              className="atom-btn atom-btn-outline atom-btn-sm"
              onClick={() => onNavigate('live')}
            >
              Full Live View <ArrowRight size={13} />
            </button>
          </div>
          <LiveLineChart data={recentReadings.slice(-15)} activeMetric="all" />
        </div>

        {/* Active Alerts & System Health Quick Widget */}
        <div className="atom-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="atom-card-header">
              <div className="card-title-group">
                <div className="card-icon-bubble" style={{ color: activeAlerts.length > 0 ? 'var(--status-critical)' : 'var(--status-normal)' }}>
                  <AlertTriangle size={20} />
                </div>
                <div>
                  <h3 className="card-title">Active Alerts</h3>
                  <span className="card-subtitle">{activeAlerts.length} requires attention</span>
                </div>
              </div>
              <button 
                className="atom-btn atom-btn-outline atom-btn-sm"
                onClick={() => onNavigate('alerts')}
              >
                View All
              </button>
            </div>

            {activeAlerts.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '2rem 1rem',
                backgroundColor: 'var(--status-normal-bg)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--status-normal-border)',
                marginTop: '0.5rem'
              }}>
                <ShieldCheck size={36} color="var(--status-normal)" style={{ margin: '0 auto 0.5rem' }} />
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#065f46', marginBottom: '0.2rem' }}>
                  All Parameters Normal
                </h4>
                <p style={{ fontSize: '0.78rem', color: '#047857' }}>
                  TDS, pH, and simulated turbidity are within safe drinking guidelines.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
                {activeAlerts.slice(0, 2).map((alert) => (
                  <div key={alert.id} style={{
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: alert.severity === 'Critical' ? 'var(--status-critical-bg)' : 'var(--status-warning-bg)',
                    border: `1px solid ${alert.severity === 'Critical' ? 'var(--status-critical-border)' : 'var(--status-warning-border)'}`,
                    fontSize: '0.8rem'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 700, color: alert.severity === 'Critical' ? '#991b1b' : '#92400e' }}>
                        {alert.title}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', lineHeight: 1.3 }}>
                      {alert.message}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Purifier Action Prompt */}
          <div style={{
            marginTop: '1.25rem',
            padding: '0.85rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--brand-purple-subtle)',
            border: '1px solid var(--brand-purple-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--brand-primary)' }}>
                Filter Health Status: {filterHealth?.overall_status || 'Optimal'}
              </span>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                Stage 3 RO Membrane at {filterHealth?.stages?.[2]?.condition_pct || 89}% condition.
              </p>
            </div>
            <button 
              className="atom-btn atom-btn-primary atom-btn-sm"
              onClick={() => onNavigate('filter')}
            >
              Details
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


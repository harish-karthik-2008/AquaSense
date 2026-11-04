import React, { useState } from 'react';
import {
  Filter,
  RefreshCw,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Sparkles,
  Info,
  Droplet
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

export default function FilterHealth({
  filterData = null,
  onResetFilters = () => {}
}) {
  const [isResetting, setIsResetting] = useState(false);

  const data = filterData || {
    overall_condition_pct: 78.0,
    overall_status: 'Good',
    operating_hours: 1420.5,
    processed_volume_liters: 4850.0,
    last_serviced_date: '2026-08-15',
    next_scheduled_service: '2027-02-15',
    stages: []
  };

  const handleReset = async () => {
    if (window.confirm("Simulate cartridge replacement? This resets all filter stages to 100% optimal condition.")) {
      setIsResetting(true);
      await onResetFilters();
      setIsResetting(false);
    }
  };

  const overall = data.overall_condition_pct;

  return (
    <div>
      {/* 1. Top Header Card */}
      <div className="dashboard-header-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
          <div className="brand-logo-icon" style={{ width: 38, height: 38, borderRadius: 'var(--radius-xs)' }}>
            <Filter size={20} color="#000000" />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#000000' }}>
                Predictive Purifier Filter Health
              </h2>
              <StatusBadge status={data.overall_status} />
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Multi-stage filtration lifecycle modeling & consumable maintenance management.
            </p>
          </div>
        </div>

        <button
          className="atom-btn atom-btn-primary atom-btn-sm"
          onClick={handleReset}
          disabled={isResetting}
          title="Simulate service technician cartridge replacement"
        >
          <RefreshCw size={13} className={isResetting ? 'spin' : ''} />
          <span>Simulate Cartridge Service</span>
        </button>
      </div>

      {/* 2. Demonstration & Telemetry Notice */}
      <div style={{
        backgroundColor: 'var(--brand-yellow-light)',
        border: '1px solid var(--brand-yellow-border)',
        borderRadius: 'var(--radius-xs)',
        padding: '0.85rem 1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem'
      }}>
        <Info size={18} color="#000000" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.78rem', color: '#1a1a1a', lineHeight: 1.5 }}>
          <b style={{ color: '#000000' }}>Demonstration & Predictive Telemetry Model:</b> Filter health is currently calculated via demonstration runtime and processed water volume metrics rather than physical membrane fouling. The system architecture is fully prepared for physical differential pressure and cartridge telemetry integration.
        </div>
      </div>

      {/* 3. Purifier Telemetry Summary Cards */}
      <div className="filter-telemetry-grid">
        {/* Overall Condition */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#000000', textTransform: 'uppercase' }}>
            Overall Purifier Health
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.85rem', fontWeight: 800, color: '#000000' }}>
              {overall}%
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--status-normal)' }}>
              {data.overall_status}
            </span>
          </div>
          <div className="gauge-track" style={{ height: 6 }}>
            <div
              className={`gauge-fill ${overall > 70 ? 'normal' : overall > 40 ? 'warning' : 'critical'}`}
              style={{ width: `${overall}%` }}
            />
          </div>
        </div>

        {/* Operating Hours */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#000000', textTransform: 'uppercase' }}>
            Operating Hours
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.85rem', fontWeight: 800, color: '#000000' }}>
              {data.operating_hours}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>hours</span>
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Active booster pump runtime
          </span>
        </div>

        {/* Processed Volume */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#000000', textTransform: 'uppercase' }}>
            Processed Volume
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.85rem', fontWeight: 800, color: '#000000' }}>
              {data.processed_volume_liters}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Liters</span>
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            Purified drinking water dispensed
          </span>
        </div>

        {/* Next Scheduled Maintenance */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#000000', textTransform: 'uppercase' }}>
            Next Routine Service
          </span>
          <div style={{ marginTop: '0.35rem', marginBottom: '0.45rem' }}>
            <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#000000' }}>
              {data.next_scheduled_service}
            </span>
          </div>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
            Last serviced: {data.last_serviced_date}
          </span>
        </div>
      </div>

      {/* 4. Multi-Stage Purifier Breakdown */}
      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#000000', marginBottom: '1rem' }}>
        Multi-Stage Filtration Telemetry Breakdown
      </h3>

      <div className="filter-stages-grid">
        {(data.stages || []).map((stage) => {
          const isGood = stage.condition_pct > 70;
          const isFair = stage.condition_pct > 40 && stage.condition_pct <= 70;

          return (
            <div key={stage.id} className="atom-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div className="atom-card-header">
                  <div className="card-title-group">
                    <div style={{
                      width: 28,
                      height: 28,
                      borderRadius: 'var(--radius-xs)',
                      background: '#000000',
                      color: '#FDB813',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '0.8rem'
                    }}>
                      {stage.stage_number}
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#000000' }}>
                        {stage.name}
                      </h4>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {stage.type}
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={stage.status} />
                </div>

                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.85rem', lineHeight: 1.4 }}>
                  {stage.description}
                </p>

                {/* Progress Bar */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Remaining Cartridge Life:</span>
                    <span style={{ color: '#000000', fontWeight: 800 }}>{stage.condition_pct}%</span>
                  </div>
                  <div className="gauge-track">
                    <div
                      className={`gauge-fill ${isGood ? 'normal' : isFair ? 'warning' : 'critical'}`}
                      style={{ width: `${stage.condition_pct}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Stage Meta Information */}
              <div style={{
                backgroundColor: 'var(--bg-app)',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-light)',
                padding: '0.6rem 0.8rem',
                fontSize: '0.74rem',
                display: 'flex',
                justifyContent: 'space-between',
                color: 'var(--text-secondary)',
                marginTop: '0.75rem'
              }}>
                <span>Target: <b style={{ color: '#000000' }}>{stage.target_contaminants}</b></span>
                <span>Est. Remaining: <b style={{ color: '#000000' }}>{stage.days_remaining} days</b></span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

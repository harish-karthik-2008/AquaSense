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
      {/* Top Header Card */}
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
            <Filter size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
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
          <RefreshCw size={14} className={isResetting ? 'spin' : ''} />
          <span>Simulate Cartridge Service</span>
        </button>
      </div>

      {/* DEMONSTRATION NOTICE (CRITICAL HACKATHON REQUIREMENT) */}
      <div style={{
        backgroundColor: 'var(--brand-purple-subtle)',
        border: '1px solid var(--brand-purple-border)',
        borderRadius: 'var(--radius-md)',
        padding: '0.85rem 1.25rem',
        marginBottom: '1.75rem',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem'
      }}>
        <Info size={20} color="var(--brand-primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '0.78rem', color: 'var(--brand-primary)', lineHeight: 1.5 }}>
          <b>Demonstration & Predictive Telemetry Model:</b> Purifier filter condition is computed via simulated operational runtime and water volume metrics. The current physical potentiometers in Wokwi simulate water quality inputs (TDS, pH, turbidity) and not physical membrane fouling. The architecture is ready for direct drop-in telemetry integration with Atomberg's IoT purifier hardware.
        </div>
      </div>

      {/* PURIFIER TELEMETRY SUMMARY CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '1.25rem',
        marginBottom: '2rem'
      }}>
        {/* Overall Condition */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase' }}>
            Overall Purifier Health
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
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
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7B2CBF', textTransform: 'uppercase' }}>
            Operating Hours
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
              {data.operating_hours}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>hours</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Total active booster pump runtime
          </span>
        </div>

        {/* Processed Volume */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>
            Processed Volume
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
              {data.processed_volume_liters}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Liters</span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Purified drinking water dispensed
          </span>
        </div>

        {/* Next Scheduled Maintenance */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#D97706', textTransform: 'uppercase' }}>
            Next Routine Service
          </span>
          <div style={{ marginTop: '0.4rem', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
              {data.next_scheduled_service}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Last serviced on {data.last_serviced_date}
          </span>
        </div>
      </div>

      {/* MULTI-STAGE PURIFIER BREAKDOWN */}
      <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--brand-primary)', marginBottom: '1rem' }}>
        Multi-Stage Filtration Telemetry Breakdown
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {(data.stages || []).map((stage) => {
          const isGood = stage.condition_pct > 70;
          const isFair = stage.condition_pct > 40 && stage.condition_pct <= 70;

          return (
            <div key={stage.id} className="atom-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div className="atom-card-header">
                  <div className="card-title-group">
                    <div style={{
                      width: 32,
                      height: 32,
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--brand-gradient-card)',
                      border: '1px solid var(--brand-purple-border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      color: 'var(--brand-primary)',
                      fontSize: '0.85rem'
                    }}>
                      {stage.stage_number}
                    </div>
                    <div>
                      <h4 style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {stage.name}
                      </h4>
                      <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        {stage.type}
                      </span>
                    </div>
                  </div>
                  <StatusBadge status={stage.status} />
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.4 }}>
                  {stage.description}
                </p>

                {/* Progress Bar */}
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Remaining Cartridge Life:</span>
                    <span style={{ color: 'var(--brand-primary)' }}>{stage.condition_pct}%</span>
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
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.65rem 0.85rem',
                fontSize: '0.75rem',
                display: 'flex',
                justifyContent: 'space-between',
                color: 'var(--text-secondary)',
                marginTop: '0.75rem'
              }}>
                <span>Target: <b>{stage.target_contaminants}</b></span>
                <span>Est. Remaining: <b>{stage.days_remaining} days</b></span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


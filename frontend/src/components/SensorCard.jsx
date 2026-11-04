import React from 'react';
import { Droplet, Activity, Wind, ArrowUp, ArrowDown, Minus, Info } from 'lucide-react';
import StatusBadge from './StatusBadge';
import PhScaleGauge from './PhScaleGauge';
import CircularGauge from './CircularGauge';

export default function SensorCard({
  type = 'tds', // 'tds' | 'ph' | 'turbidity'
  title = 'Sensor Parameter',
  value = 0,
  unit = '',
  status = 'Normal',
  previousValue = null,
  thresholdText = '',
  settings = {},
  isSimulated = false
}) {
  // Compute previous difference
  let diff = null;
  let diffClass = 'neutral';
  if (previousValue !== null && previousValue !== undefined && !isNaN(previousValue)) {
    const rawDiff = Number(value) - Number(previousValue);
    diff = rawDiff.toFixed(type === 'ph' ? 2 : 1);
    if (Math.abs(rawDiff) > 0.05) {
      diffClass = rawDiff > 0 ? 'up' : 'down';
    }
  }

  // Icons
  let Icon = Droplet;
  if (type === 'ph') Icon = Activity;
  if (type === 'turbidity') Icon = Wind;

  return (
    <div className="atom-card sensor-card">
      <div className="atom-card-header">
        <div className="card-title-group">
          <div className="card-icon-bubble">
            <Icon size={18} />
          </div>
          <div>
            <h3 className="card-title">{title}</h3>
            <span className="card-subtitle">
              {type === 'turbidity' ? 'Simulated Scale' : 'Continuous Stream'}
            </span>
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      <div className="sensor-card-body">
        {type === 'tds' && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ minWidth: 0 }}>
              <div className="sensor-value-row">
                <span className="sensor-value">{Number(value).toFixed(1)}</span>
                <span className="sensor-unit">{unit}</span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Target: &lt; 300 ppm (Drinking Standard)
              </p>
            </div>
            <div style={{ flexShrink: 0 }}>
              <CircularGauge
                value={Number(value)}
                max={800}
                unit={unit}
                label="TDS"
                status={status}
                size={84}
              />
            </div>
          </div>
        )}

        {type === 'ph' && (
          <div>
            <div className="sensor-value-row">
              <span className="sensor-value">{Number(value).toFixed(2)}</span>
              <span className="sensor-unit">{unit}</span>
            </div>
            {/* Visual 0-14 pH Scale */}
            <PhScaleGauge
              value={Number(value)}
              minAcceptable={settings?.ph_min_acceptable || 6.5}
              maxAcceptable={settings?.ph_max_acceptable || 8.5}
            />
          </div>
        )}

        {type === 'turbidity' && (
          <div>
            <div className="sensor-value-row">
              <span className="sensor-value">{Number(value).toFixed(1)}</span>
              <span className="sensor-unit" style={{ fontSize: '0.85rem' }}>
                Simulated Scale
              </span>
            </div>

            {/* Horizontal Gauge Bar */}
            <div className="gauge-bar-wrapper">
              <div className="gauge-track">
                <div
                  className={`gauge-fill ${status.toLowerCase()}`}
                  style={{ width: `${Math.min(100, (Number(value) / 25) * 100)}%` }}
                />
              </div>
              <div className="gauge-limits">
                <span>0.0 (Clear)</span>
                <span>5.0 (Warning)</span>
                <span>25.0+ (Murky)</span>
              </div>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.35rem',
              backgroundColor: 'var(--brand-yellow-light)',
              border: '1px solid var(--brand-yellow-border)',
              padding: '0.45rem 0.65rem',
              borderRadius: 'var(--radius-xs)',
              fontSize: '0.72rem',
              color: '#855d00',
              marginTop: '0.5rem'
            }}>
              <Info size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>
                Simulated turbidity from Wokwi potentiometer; not scientifically calibrated NTU.
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="sensor-meta-row">
        <div className="sensor-diff">
          {diff !== null ? (
            <>
              {diffClass === 'up' && <ArrowUp size={13} className="sensor-diff up" />}
              {diffClass === 'down' && <ArrowDown size={13} className="sensor-diff down" />}
              {diffClass === 'neutral' && <Minus size={13} className="sensor-diff neutral" />}
              <span className={`sensor-diff ${diffClass}`}>
                {diff > 0 ? `+${diff}` : diff} {unit} vs previous
              </span>
            </>
          ) : (
            <span style={{ color: 'var(--text-muted)' }}>Initial Reading</span>
          )}
        </div>
        <span className="sensor-threshold-tag">{thresholdText}</span>
      </div>
    </div>
  );
}

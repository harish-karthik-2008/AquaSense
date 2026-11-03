import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Save,
  RotateCcw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Info
} from 'lucide-react';
import { api } from '../services/api';

export default function Settings({ settings = {}, onSaveSettings = () => {} }) {
  const [formData, setFormData] = useState({
    tds_warning_threshold: 300.0,
    tds_critical_threshold: 500.0,
    ph_min_acceptable: 6.5,
    ph_max_acceptable: 8.5,
    turbidity_warning_threshold: 5.0,
    turbidity_critical_threshold: 10.0,
    anomaly_sensitivity: 'medium',
    heartbeat_timeout_seconds: 25
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (settings && Object.keys(settings).length > 0) {
      setFormData((prev) => ({ ...prev, ...settings }));
    }
  }, [settings]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: field === 'anomaly_sensitivity' ? value : Number(value)
    }));
  };

  const handleResetDefaults = () => {
    setFormData({
      tds_warning_threshold: 300.0,
      tds_critical_threshold: 500.0,
      ph_min_acceptable: 6.5,
      ph_max_acceptable: 8.5,
      turbidity_warning_threshold: 5.0,
      turbidity_critical_threshold: 10.0,
      anomaly_sensitivity: 'medium',
      heartbeat_timeout_seconds: 25
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await onSaveSettings(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert(`Failed to save settings: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

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
            background: 'var(--brand-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff'
          }}>
            <SettingsIcon size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
              Threshold & Sensitivity Configurations
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Tune acceptable drinking water standards and machine-learning anomaly detection sensitivity.
            </p>
          </div>
        </div>

        {saveSuccess && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--status-normal-bg)',
            color: '#065f46',
            padding: '0.4rem 0.85rem',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--status-normal-border)',
            fontSize: '0.8rem',
            fontWeight: 600
          }}>
            <CheckCircle2 size={16} />
            <span>Settings saved successfully!</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
          {/* TDS Thresholds */}
          <div className="atom-card">
            <h3 className="card-title" style={{ marginBottom: '1rem', color: '#7B2CBF' }}>
              TDS – Total Dissolved Solids (ppm)
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Warning Threshold (ppm)
                </label>
                <input
                  type="number"
                  min="50"
                  max="1000"
                  step="10"
                  value={formData.tds_warning_threshold}
                  onChange={(e) => handleChange('tds_warning_threshold', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Standard BIS/WHO drinking upper recommended limit: ~300 ppm
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Critical Threshold (ppm)
                </label>
                <input
                  type="number"
                  min="100"
                  max="2000"
                  step="10"
                  value={formData.tds_critical_threshold}
                  onChange={(e) => handleChange('tds_critical_threshold', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Triggers critical membrane failure alert: 500 ppm
                </span>
              </div>
            </div>
          </div>

          {/* pH Thresholds */}
          <div className="atom-card">
            <h3 className="card-title" style={{ marginBottom: '1rem', color: '#059669' }}>
              pH – Acidity & Alkalinity
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Minimum Acceptable pH (Acidic Limit)
                </label>
                <input
                  type="number"
                  min="4.0"
                  max="7.5"
                  step="0.1"
                  value={formData.ph_min_acceptable}
                  onChange={(e) => handleChange('ph_min_acceptable', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Safe drinking minimum: 6.5 pH
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Maximum Acceptable pH (Alkaline Limit)
                </label>
                <input
                  type="number"
                  min="7.5"
                  max="11.0"
                  step="0.1"
                  value={formData.ph_max_acceptable}
                  onChange={(e) => handleChange('ph_max_acceptable', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Safe drinking maximum: 8.5 pH
                </span>
              </div>
            </div>
          </div>

          {/* Turbidity Thresholds */}
          <div className="atom-card">
            <h3 className="card-title" style={{ marginBottom: '1rem', color: '#D97706' }}>
              Turbidity (Simulated Scale)
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Warning Threshold (Simulated Scale)
                </label>
                <input
                  type="number"
                  min="1.0"
                  max="20.0"
                  step="0.5"
                  value={formData.turbidity_warning_threshold}
                  onChange={(e) => handleChange('turbidity_warning_threshold', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Warning threshold: 5.0 (simulated)
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Critical Threshold (Simulated Scale)
                </label>
                <input
                  type="number"
                  min="5.0"
                  max="50.0"
                  step="0.5"
                  value={formData.turbidity_critical_threshold}
                  onChange={(e) => handleChange('turbidity_critical_threshold', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Critical sediment breakthrough: 10.0 (simulated)
                </span>
              </div>
            </div>
          </div>

          {/* AI Anomaly Sensitivity & System Settings */}
          <div className="atom-card">
            <h3 className="card-title" style={{ marginBottom: '1rem', color: 'var(--brand-primary)' }}>
              AI Anomaly & System Telemetry
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Scikit-Learn Anomaly Sensitivity
                </label>
                <select
                  value={formData.anomaly_sensitivity}
                  onChange={(e) => handleChange('anomaly_sensitivity', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem',
                    backgroundColor: '#fff'
                  }}
                >
                  <option value="low">Low (Fewer alerts, flags only extreme outlier spikes)</option>
                  <option value="medium">Medium (Balanced Isolation Forest & 2.5σ Z-score)</option>
                  <option value="high">High (Strict monitoring, flags subtle correlation drift)</option>
                </select>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Evaluates statistical pattern deviations relative to historical baseline.
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Heartbeat Timeout (Seconds)
                </label>
                <input
                  type="number"
                  min="5"
                  max="120"
                  step="5"
                  value={formData.heartbeat_timeout_seconds}
                  onChange={(e) => handleChange('heartbeat_timeout_seconds', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Time without data before marking ESP32 offline: 25s
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '1rem' }}>
          <button
            type="button"
            className="atom-btn atom-btn-secondary"
            onClick={handleResetDefaults}
          >
            <RotateCcw size={15} />
            <span>Reset to Defaults</span>
          </button>

          <button
            type="submit"
            className="atom-btn atom-btn-primary"
            disabled={isSaving}
          >
            <Save size={15} />
            <span>{isSaving ? 'Saving Configurations...' : 'Save Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}


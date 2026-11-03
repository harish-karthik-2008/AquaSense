import React, { useState } from 'react';
import {
  Cpu,
  Wifi,
  Radio,
  Server,
  Layers,
  Sliders,
  Send,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Copy,
  ExternalLink,
  Code
} from 'lucide-react';
import { api } from '../services/api';

export default function DeviceManagement({ deviceStatus = {} }) {
  // Simulator test sender state
  const [testTds, setTestTds] = useState(165.0);
  const [testPh, setTestPh] = useState(7.35);
  const [testTurbidity, setTestTurbidity] = useState(1.4);
  const [isSending, setIsSending] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [copiedCode, setCopiedCode] = useState(false);

  // Send test packet directly from dashboard UI
  const handleSendTestPacket = async () => {
    setIsSending(true);
    setTestResult(null);
    try {
      const res = await api.sendSensorData({
        tds: Number(testTds),
        ph: Number(testPh),
        turbidity: Number(testTurbidity),
        device_id: 'AquaSense-ESP32'
      });
      setTestResult({
        success: true,
        data: res.data,
        message: 'Packet ingested by backend, evaluated by AI, and broadcast to WebSocket clients!'
      });
    } catch (err) {
      setTestResult({
        success: false,
        message: `Error sending to backend: ${err.message}`
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleApplyPreset = (tds, ph, turb) => {
    setTestTds(tds);
    setTestPh(ph);
    setTestTurbidity(turb);
  };

  const isOnline = deviceStatus?.is_online ?? false;
  const dbInfo = deviceStatus?.database || { type: 'MongoDB / Persistent Fallback', connected: true };

  const esp32Snippet = `// In Wokwi sketch.ino:
const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* serverUrl = "${api.getBaseUrl()}/api/sensor-data";`;

  const copySnippet = () => {
    navigator.clipboard.writeText(esp32Snippet);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
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
            <Cpu size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)' }}>
                Device Telemetry & Hardware Node
              </h2>
              <span className={`status-pill ${isOnline ? 'normal' : 'critical'}`}>
                <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Hardware specifications, Wokwi IoT networking gateway configuration, and live simulator harness.
            </p>
          </div>
        </div>

        <div className="simulation-mode-badge">
          <Layers className="simulation-icon" />
          <span>Wokwi Simulation Node</span>
        </div>
      </div>

      {/* HARDWARE TELEMETRY CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {/* Device Specifications */}
        <div className="atom-card">
          <div className="atom-card-header">
            <h3 className="card-title">ESP32 Hardware Node</h3>
            <Cpu size={18} color="var(--brand-primary)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Device Identifier:</span>
              <span style={{ fontWeight: 700 }}>{deviceStatus?.device_id || 'AquaSense-ESP32'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Microcontroller:</span>
              <span style={{ fontWeight: 600 }}>ESP32 DevKit V1 (Xtensa Dual-Core)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Firmware:</span>
              <span style={{ fontWeight: 600, color: 'var(--brand-accent)' }}>
                {deviceStatus?.firmware_version || 'v1.2.4-atomQUEST'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>ADC Resolution:</span>
              <span style={{ fontWeight: 600 }}>12-bit (0 – 4095)</span>
            </div>
          </div>
        </div>

        {/* Pin Mapping */}
        <div className="atom-card">
          <div className="atom-card-header">
            <h3 className="card-title">Sensors & Pin Mapping</h3>
            <Sliders size={18} color="var(--brand-primary)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>TDS Potentiometer:</span>
              <span style={{ fontWeight: 700, color: '#7B2CBF' }}>GPIO 34 (ADC1_CH6)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>pH Potentiometer:</span>
              <span style={{ fontWeight: 700, color: '#059669' }}>GPIO 35 (ADC1_CH7)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Turbidity (Simulated):</span>
              <span style={{ fontWeight: 700, color: '#D97706' }}>GPIO 32 (ADC1_CH4)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Status Activity LED:</span>
              <span style={{ fontWeight: 600 }}>GPIO 2</span>
            </div>
          </div>
        </div>

        {/* Network & Protocol */}
        <div className="atom-card">
          <div className="atom-card-header">
            <h3 className="card-title">Networking & Database</h3>
            <Radio size={18} color="var(--brand-primary)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.82rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>WiFi Network:</span>
              <span style={{ fontWeight: 600 }}>{deviceStatus?.wifi_network || 'Wokwi-GUEST'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Ingestion Protocol:</span>
              <span style={{ fontWeight: 600 }}>HTTP POST + WebSocket</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Storage Engine:</span>
              <span style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>
                {dbInfo.type || 'MongoDB'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Heartbeat Timeout:</span>
              <span style={{ fontWeight: 600 }}>25 seconds</span>
            </div>
          </div>
        </div>
      </div>

      {/* BUILT-IN HARDWARE SENSOR SIMULATOR (EVALUATION / TEST WIDGET) */}
      <div className="atom-card" style={{ marginBottom: '2rem' }}>
        <div className="atom-card-header">
          <div className="card-title-group">
            <div className="card-icon-bubble">
              <Sliders size={20} />
            </div>
            <div>
              <h3 className="card-title">Interactive Potentiometer Simulator</h3>
              <p className="card-subtitle">
                Test potentiometer input changes directly from the dashboard to observe real-time round-trip updates
              </p>
            </div>
          </div>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--brand-accent)' }}>
            Hackathon Judge Testing Utility
          </span>
        </div>

        {/* 1-Click Preset Buttons */}
        <div style={{ marginBottom: '1.5rem' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '0.5rem' }}>
            Quick Condition Presets:
          </span>
          <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
            <button
              className="atom-btn atom-btn-secondary atom-btn-sm"
              onClick={() => handleApplyPreset(165.0, 7.35, 1.4)}
            >
              🟢 Normal Pure Water (TDS 165, pH 7.35)
            </button>
            <button
              className="atom-btn atom-btn-secondary atom-btn-sm"
              onClick={() => handleApplyPreset(580.0, 7.45, 2.0)}
            >
              🔴 High TDS Breach (&gt;500 ppm)
            </button>
            <button
              className="atom-btn atom-btn-secondary atom-btn-sm"
              onClick={() => handleApplyPreset(140.0, 5.20, 1.5)}
            >
              🟡 Acidic Water Breach (&lt;6.5 pH)
            </button>
            <button
              className="atom-btn atom-btn-secondary atom-btn-sm"
              onClick={() => handleApplyPreset(210.0, 7.20, 14.5)}
            >
              🔴 High Turbidity Breach (&gt;10 sim)
            </button>
            <button
              className="atom-btn atom-btn-secondary atom-btn-sm"
              onClick={() => handleApplyPreset(390.0, 8.90, 12.0)}
            >
              ✨ AI Anomaly Spike (Pattern Divergence)
            </button>
          </div>
        </div>

        {/* Sliders Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1.5rem',
          backgroundColor: 'var(--bg-subtle)',
          padding: '1.25rem',
          borderRadius: 'var(--radius-md)',
          marginBottom: '1.25rem'
        }}>
          {/* TDS Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
              <span style={{ fontWeight: 700, color: '#7B2CBF' }}>TDS Potentiometer (GPIO 34):</span>
              <span style={{ fontWeight: 800 }}>{testTds} ppm</span>
            </div>
            <input
              type="range"
              min="0"
              max="900"
              step="5"
              value={testTds}
              onChange={(e) => setTestTds(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#7B2CBF' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span>0 ppm</span>
              <span>300 (Warning)</span>
              <span>500 (Critical)</span>
              <span>900 ppm</span>
            </div>
          </div>

          {/* pH Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
              <span style={{ fontWeight: 700, color: '#059669' }}>pH Potentiometer (GPIO 35):</span>
              <span style={{ fontWeight: 800 }}>{testPh} pH</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="14.0"
              step="0.05"
              value={testPh}
              onChange={(e) => setTestPh(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#059669' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span>0 (Acidic)</span>
              <span>6.5 – 8.5 (Safe)</span>
              <span>14 (Alkaline)</span>
            </div>
          </div>

          {/* Turbidity Slider */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.82rem' }}>
              <span style={{ fontWeight: 700, color: '#D97706' }}>Turbidity (GPIO 32):</span>
              <span style={{ fontWeight: 800 }}>{testTurbidity} (sim)</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="30.0"
              step="0.2"
              value={testTurbidity}
              onChange={(e) => setTestTurbidity(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#D97706' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span>0.0 (Clear)</span>
              <span>5.0 (Warning)</span>
              <span>30.0 (Murky)</span>
            </div>
          </div>
        </div>

        {/* Send Action & Feedback */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <button
            className="atom-btn atom-btn-primary"
            onClick={handleSendTestPacket}
            disabled={isSending}
          >
            <Send size={15} />
            <span>{isSending ? 'Sending to Backend...' : 'Transmit Simulated ESP32 Reading'}</span>
          </button>

          {testResult && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.8rem',
              color: testResult.success ? '#065f46' : '#991b1b',
              backgroundColor: testResult.success ? 'var(--status-normal-bg)' : 'var(--status-critical-bg)',
              padding: '0.4rem 0.85rem',
              borderRadius: 'var(--radius-sm)',
              border: `1px solid ${testResult.success ? 'var(--status-normal-border)' : 'var(--status-critical-border)'}`
            }}>
              {testResult.success ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
              <span>{testResult.message}</span>
            </div>
          )}
        </div>
      </div>

      {/* WOKWI SETUP INSTRUCTIONS */}
      <div className="atom-card">
        <div className="atom-card-header">
          <div className="card-title-group">
            <div className="card-icon-bubble">
              <Code size={20} />
            </div>
            <div>
              <h3 className="card-title">Wokwi Simulator Setup Guide</h3>
              <p className="card-subtitle">Connecting Wokwi web/desktop to this AquaSense AI instance</p>
            </div>
          </div>
          <button 
            className="atom-btn atom-btn-outline atom-btn-sm"
            onClick={copySnippet}
          >
            <Copy size={13} />
            <span>{copiedCode ? 'Copied!' : 'Copy Code Snippet'}</span>
          </button>
        </div>

        <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          <ol style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <li>
              <b>Open Wokwi:</b> Open the <a href="https://wokwi.com/projects/new/esp32" target="_blank" rel="noreferrer" style={{ color: 'var(--brand-accent)', fontWeight: 600 }}>Wokwi ESP32 Simulator</a>.
            </li>
            <li>
              <b>Paste Code:</b> Copy the C++ code from <code>esp32/sketch.ino</code> into the Wokwi code tab.
            </li>
            <li>
              <b>Import Wiring:</b> Switch to the <code>diagram.json</code> tab in Wokwi and paste the contents of <code>esp32/diagram.json</code>.
            </li>
            <li>
              <b>Configure Server URL:</b> Set <code>serverUrl</code> in <code>sketch.ino</code> to your reachable backend URL (e.g. using ngrok or localtunnel: <code>npx localtunnel --port 8000</code>).
            </li>
            <li>
              <b>Start Simulation:</b> Click the Play button in Wokwi. As you rotate the three potentiometers, readings will stream directly into this dashboard!
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}


import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Download,
  Search,
  AlertCircle
} from 'lucide-react';
import AnalyticsChart from '../charts/AnalyticsChart';
import StatusBadge from '../components/StatusBadge';
import { api } from '../services/api';

export default function Analytics({ settings = {} }) {
  const [timeframe, setTimeframe] = useState('24h'); // 'today' | '24h' | '7d' | 'all'
  const [activeParam, setActiveParam] = useState('tds'); // 'tds' | 'ph' | 'turbidity'
  const [historyData, setHistoryData] = useState([]);
  const [analyticsSummary, setAnalyticsSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Fetch actual data from backend
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [histRes, summaryRes] = await Promise.all([
        api.getHistory(300, timeframe),
        api.getAnalytics(timeframe)
      ]);
      setHistoryData(histRes?.data || []);
      setAnalyticsSummary(summaryRes?.data || null);
    } catch (err) {
      console.error('[Analytics] Failed to fetch historical data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [timeframe]);

  // Export to CSV
  const handleExportCSV = () => {
    if (!historyData.length) return;
    const headers = ['Timestamp', 'Device ID', 'TDS (ppm)', 'pH', 'Turbidity (simulated)', 'Status'];
    const rows = historyData.map((d) => [
      d.timestamp,
      d.device_id || 'AquaSense-ESP32',
      d.tds,
      d.ph,
      d.turbidity,
      d.overall_status
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `aquasense_analytics_${timeframe}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filtered rows for table
  const filteredRows = historyData.filter((r) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (r.timestamp && r.timestamp.toLowerCase().includes(term)) ||
      (r.overall_status && r.overall_status.toLowerCase().includes(term)) ||
      String(r.tds).includes(term) ||
      String(r.ph).includes(term)
    );
  });

  const totalPages = Math.ceil(filteredRows.length / itemsPerPage) || 1;
  const paginatedRows = filteredRows.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const stats = analyticsSummary || {
    tds: { min: 0, max: 0, avg: 0 },
    ph: { min: 0, max: 0, avg: 0 },
    turbidity: { min: 0, max: 0, avg: 0 }
  };

  return (
    <div>
      {/* 1. Header Bar with Timeframe & CSV Export */}
      <div className="dashboard-header-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
          <div className="brand-logo-icon" style={{ width: 36, height: 36, borderRadius: 'var(--radius-xs)' }}>
            <BarChart3 size={20} color="#000000" />
          </div>
          <div style={{ minWidth: 0 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#000000' }}>
              Water Quality Analytics
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Historical trends and statistical parameters computed from database records.
            </p>
          </div>
        </div>

        {/* Timeframe Filters and CSV Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#F0F0F0',
            padding: '0.2rem',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--border-light)',
            flexWrap: 'wrap'
          }}>
            {[
              { id: 'today', label: 'Today' },
              { id: '24h', label: '24 Hours' },
              { id: '7d', label: '7 Days' },
              { id: 'all', label: 'All Time' },
            ].map((tf) => (
              <button
                key={tf.id}
                onClick={() => { setTimeframe(tf.id); setCurrentPage(1); }}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '0.76rem',
                  fontWeight: 700,
                  color: timeframe === tf.id ? '#000000' : '#666666',
                  backgroundColor: timeframe === tf.id ? '#FFFFFF' : 'transparent',
                  boxShadow: timeframe === tf.id ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                  transition: 'all 0.15s ease'
                }}
              >
                {tf.label}
              </button>
            ))}
          </div>

          <button
            className="atom-btn atom-btn-primary atom-btn-sm"
            onClick={handleExportCSV}
            disabled={!historyData.length}
            title="Download records as CSV"
          >
            <Download size={13} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* 2. Statistical Summary Cards: Min, Max, Average */}
      <div className="analytics-stats-grid">
        {/* TDS Stats */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#000000', textTransform: 'uppercase' }}>
            TDS Summary (ppm)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '1.85rem', fontWeight: 800, color: '#000000' }}>
              {stats.tds.avg}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>ppm average</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
            <span>Min: <b>{stats.tds.min} ppm</b></span>
            <span>Max: <b>{stats.tds.max} ppm</b></span>
          </div>
        </div>

        {/* pH Stats */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#10B981', textTransform: 'uppercase' }}>
            pH Level Summary
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '1.85rem', fontWeight: 800, color: '#000000' }}>
              {stats.ph.avg}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>pH average</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
            <span>Min: <b>{stats.ph.min}</b></span>
            <span>Max: <b>{stats.ph.max}</b></span>
          </div>
        </div>

        {/* Turbidity Stats */}
        <div className="atom-card" style={{ padding: '1.25rem' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#D97706', textTransform: 'uppercase' }}>
            Turbidity (Simulated)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.25rem', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '1.85rem', fontWeight: 800, color: '#000000' }}>
              {stats.turbidity.avg}
            </span>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>(sim) average</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.5rem' }}>
            <span>Min: <b>{stats.turbidity.min}</b></span>
            <span>Max: <b>{stats.turbidity.max}</b></span>
          </div>
        </div>
      </div>

      {/* 3. Historical Graphs (TDS, pH, Turbidity) */}
      <div className="atom-card" style={{ marginBottom: '1.5rem' }}>
        <div className="atom-card-header" style={{ flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 className="card-title">Parameter Historical Trends</h3>
            <p className="card-subtitle">
              Visualizing water quality evolution for selected parameter
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            {[
              { id: 'tds', label: 'TDS Trend' },
              { id: 'ph', label: 'pH Trend' },
              { id: 'turbidity', label: 'Turbidity Trend' },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setActiveParam(p.id)}
                className={`atom-btn atom-btn-sm ${activeParam === p.id ? 'atom-btn-primary' : 'atom-btn-secondary'}`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {historyData.length === 0 ? (
          <div className="empty-state-box">
            <div className="empty-state-icon">
              <AlertCircle size={24} />
            </div>
            <h3 className="empty-state-title">No Historical Records Found</h3>
            <p className="empty-state-desc">
              Connect the ESP32 simulator in Wokwi or execute the simulation script to record water quality telemetry.
            </p>
          </div>
        ) : (
          <AnalyticsChart data={historyData} parameter={activeParam} thresholds={settings} />
        )}
      </div>

      {/* 4. Recent Sensor Readings Table */}
      <div className="atom-card">
        <div className="atom-card-header" style={{ flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 className="card-title">Recent Sensor Readings Table</h3>
            <p className="card-subtitle">
              Measurement log from backend database
            </p>
          </div>

          <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%', maxWidth: '240px' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search readings..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              style={{
                padding: '0.45rem 0.65rem 0.45rem 1.85rem',
                fontSize: '0.78rem',
                borderRadius: 'var(--radius-xs)',
                border: '1px solid var(--border-light)',
                backgroundColor: '#FFFFFF',
                width: '100%'
              }}
            />
          </div>
        </div>

        <div className="atom-table-wrapper">
          <table className="atom-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>TDS (ppm)</th>
                <th>pH</th>
                <th>Turbidity (Simulated)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {paginatedRows.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No matching records found.
                  </td>
                </tr>
              ) : (
                paginatedRows.map((r, i) => (
                  <tr key={r.id || r._id || i}>
                    <td style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                      {new Date(r.timestamp).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </td>
                    <td style={{ fontWeight: 700, color: '#000000' }}>
                      {Number(r.tds).toFixed(1)}
                    </td>
                    <td style={{ fontWeight: 700, color: '#10B981' }}>
                      {Number(r.ph).toFixed(2)}
                    </td>
                    <td style={{ fontWeight: 700, color: '#D97706' }}>
                      {Number(r.turbidity).toFixed(1)}
                    </td>
                    <td>
                      <StatusBadge status={r.overall_status || 'Normal'} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '1rem',
            paddingTop: '0.65rem',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.76rem',
            color: 'var(--text-secondary)'
          }}>
            <span>Page {currentPage} of {totalPages} ({filteredRows.length} total records)</span>
            <div style={{ display: 'flex', gap: '0.45rem' }}>
              <button
                className="atom-btn atom-btn-secondary atom-btn-sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <button
                className="atom-btn atom-btn-secondary atom-btn-sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

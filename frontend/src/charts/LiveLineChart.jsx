import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

export default function LiveLineChart({ data = [], activeMetric = 'all' }) {
  // Format timestamp for X-Axis (e.g. "14:23:10")
  const formattedData = data.map((item) => {
    let timeLabel = '';
    try {
      const dt = new Date(item.timestamp);
      timeLabel = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      timeLabel = item.timestamp || '';
    }
    return {
      ...item,
      timeLabel
    };
  });

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: '#FFFFFF',
          padding: '0.85rem 1rem',
          borderRadius: '10px',
          boxShadow: '0 8px 24px rgba(46, 8, 84, 0.12)',
          border: '1px solid #E5E8F0',
          fontSize: '0.8rem'
        }}>
          <p style={{ fontWeight: 700, color: '#191C24', marginBottom: '0.4rem' }}>
            Time: {label}
          </p>
          {payload.map((entry, index) => (
            <div key={`item-${index}`} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0.2rem 0' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: entry.color }} />
              <span style={{ color: '#586074' }}>{entry.name}:</span>
              <span style={{ fontWeight: 700, color: '#191C24' }}>
                {entry.value} {entry.name === 'TDS' ? 'ppm' : entry.name === 'Turbidity' ? '(sim)' : ''}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const showTds = activeMetric === 'all' || activeMetric === 'tds';
  const showPh = activeMetric === 'all' || activeMetric === 'ph';
  const showTurb = activeMetric === 'all' || activeMetric === 'turbidity';

  return (
    <div style={{ width: '100%', height: 340 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F7" vertical={false} />
          <XAxis 
            dataKey="timeLabel" 
            stroke="#8A92A6" 
            fontSize={11} 
            tickLine={false}
            dy={8}
          />

          {/* Left Y Axis for TDS (0 - 800) */}
          {showTds && (
            <YAxis
              yAxisId="tdsAxis"
              stroke="#7B2CBF"
              fontSize={11}
              domain={[0, 'auto']}
              tickLine={false}
              dx={-5}
              label={{ value: 'TDS (ppm)', angle: -90, position: 'insideLeft', fill: '#7B2CBF', fontSize: 10, dy: 30 }}
            />
          )}

          {/* Right Y Axis for pH (0 - 14) and Turbidity (0 - 25) */}
          {(showPh || showTurb) && (
            <YAxis
              yAxisId="ratioAxis"
              orientation="right"
              stroke="#059669"
              fontSize={11}
              domain={[0, showPh ? 14 : 25]}
              tickLine={false}
              dx={5}
              label={{ value: 'pH / Turbidity', angle: 90, position: 'insideRight', fill: '#059669', fontSize: 10, dy: -30 }}
            />
          )}

          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '0.8rem' }} />

          {showTds && (
            <Line
              yAxisId="tdsAxis"
              type="monotone"
              dataKey="tds"
              name="TDS"
              stroke="#7B2CBF"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#7B2CBF' }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
          )}

          {showPh && (
            <Line
              yAxisId="ratioAxis"
              type="monotone"
              dataKey="ph"
              name="pH"
              stroke="#059669"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#059669' }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
          )}

          {showTurb && (
            <Line
              yAxisId="ratioAxis"
              type="monotone"
              dataKey="turbidity"
              name="Turbidity (sim)"
              stroke="#D97706"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#D97706' }}
              activeDot={{ r: 6 }}
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}


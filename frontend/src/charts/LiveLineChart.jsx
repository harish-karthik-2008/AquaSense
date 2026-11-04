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

export default function LiveLineChart({ 
  data = [], 
  activeMetric = 'all', 
  height = 300,
  showLegend = true 
}) {
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
          padding: '0.65rem 0.85rem',
          borderRadius: '6px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
          border: '1px solid #E5E5E5',
          fontSize: '0.78rem'
        }}>
          <p style={{ fontWeight: 700, color: '#000000', marginBottom: '0.3rem' }}>
            {label}
          </p>
          {payload.map((entry, index) => (
            <div key={`item-${index}`} style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', margin: '0.15rem 0' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: entry.color }} />
              <span style={{ color: '#666666' }}>{entry.name}:</span>
              <span style={{ fontWeight: 700, color: '#000000' }}>
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

  // If rendering a single metric chart
  if (activeMetric === 'tds') {
    return (
      <div style={{ width: '100%', height, minWidth: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="#EEEEEE" vertical={false} />
            <XAxis dataKey="timeLabel" stroke="#888888" fontSize={10} tickLine={false} dy={5} />
            <YAxis stroke="#666666" fontSize={10} domain={[0, 'auto']} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="tds"
              name="TDS"
              stroke="#000000"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#FDB813', stroke: '#000000' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (activeMetric === 'ph') {
    return (
      <div style={{ width: '100%', height, minWidth: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="#EEEEEE" vertical={false} />
            <XAxis dataKey="timeLabel" stroke="#888888" fontSize={10} tickLine={false} dy={5} />
            <YAxis stroke="#666666" fontSize={10} domain={[4, 10]} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="ph"
              name="pH"
              stroke="#10B981"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#10B981' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (activeMetric === 'turbidity') {
    return (
      <div style={{ width: '100%', height, minWidth: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="#EEEEEE" vertical={false} />
            <XAxis dataKey="timeLabel" stroke="#888888" fontSize={10} tickLine={false} dy={5} />
            <YAxis stroke="#666666" fontSize={10} domain={[0, 'auto']} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="turbidity"
              name="Turbidity (sim)"
              stroke="#FDB813"
              strokeWidth={2}
              dot={{ r: 2.5, fill: '#000000', stroke: '#FDB813' }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // Combined chart
  return (
    <div style={{ width: '100%', height, minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#EEEEEE" vertical={false} />
          <XAxis dataKey="timeLabel" stroke="#888888" fontSize={10} tickLine={false} dy={5} />
          
          <YAxis
            yAxisId="left"
            stroke="#000000"
            fontSize={10}
            domain={[0, 'auto']}
            tickLine={false}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#666666"
            fontSize={10}
            domain={[0, 20]}
            tickLine={false}
          />

          <Tooltip content={<CustomTooltip />} />
          {showLegend && <Legend wrapperStyle={{ paddingTop: '8px', fontSize: '0.76rem' }} />}

          <Line
            yAxisId="left"
            type="monotone"
            dataKey="tds"
            name="TDS"
            stroke="#000000"
            strokeWidth={2}
            dot={{ r: 2.5, fill: '#FDB813', stroke: '#000000' }}
            isAnimationActive={false}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="ph"
            name="pH"
            stroke="#10B981"
            strokeWidth={2}
            dot={{ r: 2.5, fill: '#10B981' }}
            isAnimationActive={false}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="turbidity"
            name="Turbidity (sim)"
            stroke="#FDB813"
            strokeWidth={2}
            dot={{ r: 2.5, fill: '#000000', stroke: '#FDB813' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

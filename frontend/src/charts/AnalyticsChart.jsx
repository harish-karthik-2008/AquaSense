import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

export default function AnalyticsChart({
  data = [],
  parameter = 'tds', // 'tds' | 'ph' | 'turbidity' | 'combined'
  thresholds = {}
}) {
  const formattedData = data.map((item) => {
    let dateStr = '';
    try {
      const dt = new Date(item.timestamp);
      dateStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      dateStr = item.timestamp || '';
    }
    return {
      ...item,
      dateStr
    };
  });

  const config = {
    tds: {
      key: 'tds',
      name: 'TDS (ppm)',
      color: '#7B2CBF',
      unit: 'ppm',
      domain: [0, 'auto']
    },
    ph: {
      key: 'ph',
      name: 'pH Level',
      color: '#059669',
      unit: 'pH',
      domain: [0, 14]
    },
    turbidity: {
      key: 'turbidity',
      name: 'Simulated Turbidity',
      color: '#D97706',
      unit: '(sim)',
      domain: [0, 'auto']
    }
  };

  const curr = config[parameter] || config.tds;

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`color-${curr.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={curr.color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={curr.color} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0F2F7" vertical={false} />
          <XAxis dataKey="dateStr" stroke="#8A92A6" fontSize={11} dy={6} />
          <YAxis stroke="#8A92A6" fontSize={11} domain={curr.domain} dx={-4} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderRadius: '10px',
              border: '1px solid #E5E8F0',
              boxShadow: '0 8px 24px rgba(46, 8, 84, 0.1)',
              fontSize: '0.8rem'
            }}
            formatter={(val) => [`${val} ${curr.unit}`, curr.name]}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
          <Area
            type="monotone"
            dataKey={curr.key}
            name={curr.name}
            stroke={curr.color}
            strokeWidth={2.5}
            fillOpacity={1}
            fill={`url(#color-${curr.key})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}


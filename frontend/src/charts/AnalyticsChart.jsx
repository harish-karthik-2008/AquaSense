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
  parameter = 'tds', // 'tds' | 'ph' | 'turbidity'
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
      stroke: '#000000',
      fill: '#fdb813',
      unit: 'ppm',
      domain: [0, 'auto']
    },
    ph: {
      key: 'ph',
      name: 'pH Level',
      stroke: '#10b981',
      fill: '#a7f3d0',
      unit: 'pH',
      domain: [0, 14]
    },
    turbidity: {
      key: 'turbidity',
      name: 'Simulated Turbidity',
      stroke: '#fdb813',
      fill: '#fef3c7',
      unit: '(sim)',
      domain: [0, 'auto']
    }
  };

  const curr = config[parameter] || config.tds;

  return (
    <div style={{ width: '100%', height: 300, minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id={`color-${curr.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={curr.fill} stopOpacity={0.4} />
              <stop offset="95%" stopColor={curr.fill} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 2" stroke="#EEEEEE" vertical={false} />
          <XAxis dataKey="dateStr" stroke="#888888" fontSize={10} dy={5} />
          <YAxis stroke="#666666" fontSize={10} domain={curr.domain} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              borderRadius: '6px',
              border: '1px solid #E5E5E5',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              fontSize: '0.78rem'
            }}
            formatter={(val) => [`${val} ${curr.unit}`, curr.name]}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend wrapperStyle={{ fontSize: '0.76rem', paddingTop: '6px' }} />
          <Area
            type="monotone"
            dataKey={curr.key}
            name={curr.name}
            stroke={curr.stroke}
            strokeWidth={2}
            fillOpacity={1}
            fill={`url(#color-${curr.key})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

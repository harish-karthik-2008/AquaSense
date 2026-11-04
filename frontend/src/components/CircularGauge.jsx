import React from 'react';

export default function CircularGauge({ 
  value = 0, 
  max = 1000, 
  unit = 'ppm', 
  label = 'TDS', 
  status = 'Normal',
  size = 96 
}) {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  
  const clamped = Math.max(0, Math.min(max, Number(value) || 0));
  const progress = (clamped / max) * circumference;
  const strokeDashoffset = circumference - progress;

  let strokeColor = '#10B981'; // normal subtle green
  if (status.toLowerCase() === 'warning') strokeColor = '#F59E0B'; // amber
  if (status.toLowerCase() === 'critical') strokeColor = '#EF4444'; // red

  return (
    <div style={{ position: 'relative', width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E5E5"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
          style={{ transition: 'stroke-dashoffset 0.4s ease' }}
        />
      </svg>
      <div style={{ position: 'absolute', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#000000', lineHeight: 1 }}>
          {typeof value === 'number' ? (value % 1 === 0 ? value : value.toFixed(1)) : value}
        </span>
        <span style={{ fontSize: '0.65rem', fontWeight: 600, color: '#666666', marginTop: '2px' }}>
          {unit}
        </span>
      </div>
    </div>
  );
}

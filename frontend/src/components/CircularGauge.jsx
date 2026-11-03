import React from 'react';

export default function CircularGauge({ 
  value = 0, 
  max = 1000, 
  unit = 'ppm', 
  label = 'TDS', 
  status = 'Normal',
  size = 110 
}) {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  
  const clamped = Math.max(0, Math.min(max, Number(value) || 0));
  const progress = (clamped / max) * circumference;
  const strokeDashoffset = circumference - progress;

  let strokeColor = '#10B981'; // normal
  if (status.toLowerCase() === 'warning') strokeColor = '#F59E0B';
  if (status.toLowerCase() === 'critical') strokeColor = '#EF4444';

  return (
    <div style={{ position: 'relative', width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E8F0"
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
          style={{ transition: 'stroke-dashoffset 0.5s ease, stroke 0.3s ease' }}
        />
      </svg>
      <div style={{ position: 'absolute', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--brand-primary)', lineHeight: 1 }}>
          {typeof value === 'number' ? (value % 1 === 0 ? value : value.toFixed(1)) : value}
        </span>
        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {unit}
        </span>
      </div>
    </div>
  );
}


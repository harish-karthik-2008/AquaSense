import React from 'react';

export default function PhScaleGauge({ value = 7.0, minAcceptable = 6.5, maxAcceptable = 8.5 }) {
  // Clamped between 0 and 14
  const numericVal = Math.max(0, Math.min(14, Number(value) || 7.0));
  const markerPercent = (numericVal / 14) * 100;

  return (
    <div className="ph-scale-wrapper">
      <div className="ph-track">
        {/* Pointer Pin pointing to exact pH */}
        <div 
          className="ph-marker-pointer" 
          style={{ left: `${markerPercent}%` }}
          title={`Current pH: ${numericVal.toFixed(2)}`}
        >
          <div className="ph-marker-dot" />
        </div>
      </div>

      <div className="ph-scale-labels">
        <span>0 (Acidic)</span>
        <span>7 (Neutral)</span>
        <span>14 (Alkaline)</span>
      </div>

      <div className="ph-range-indicator">
        <span style={{ color: '#059669', fontWeight: 600 }}>
          Safe Range: {minAcceptable} – {maxAcceptable} pH
        </span>
        <span style={{ color: '#000000', fontWeight: 700 }}>
          Current: {numericVal.toFixed(2)}
        </span>
      </div>
    </div>
  );
}

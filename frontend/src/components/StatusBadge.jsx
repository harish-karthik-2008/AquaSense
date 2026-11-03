import React from 'react';

export default function StatusBadge({ status = 'Normal', size = 'md' }) {
  const normStatus = (status || 'Normal').toLowerCase();
  
  let label = status;
  let className = 'status-pill normal';

  if (normStatus === 'critical') {
    className = 'status-pill critical';
  } else if (normStatus === 'warning') {
    className = 'status-pill warning';
  } else if (normStatus === 'info') {
    className = 'status-pill info';
  }

  return (
    <span className={className}>
      <span className={`status-dot ${normStatus === 'normal' ? 'online' : 'offline'}`} />
      {label}
    </span>
  );
}


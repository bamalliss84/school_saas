import React from 'react';

export const PageSkeleton: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header skeleton */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div className="skeleton" style={{ width: '220px', height: '28px' }} />
          <div className="skeleton" style={{ width: '340px', height: '18px' }} />
        </div>
        <div className="skeleton" style={{ width: '120px', height: '40px' }} />
      </div>

      {/* Metric cards skeleton */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="card"
            style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className="skeleton" style={{ width: '100px', height: '16px' }} />
              <div className="skeleton" style={{ width: '32px', height: '32px', borderRadius: '50%' }} />
            </div>
            <div className="skeleton" style={{ width: '80px', height: '32px' }} />
            <div className="skeleton" style={{ width: '140px', height: '14px' }} />
          </div>
        ))}
      </div>

      {/* Main card skeleton */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div className="skeleton" style={{ width: '180px', height: '24px', marginBottom: '1.5rem' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="skeleton"
              style={{ width: '100%', height: '48px', borderRadius: 'var(--radius-md)' }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

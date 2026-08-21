import React, { useState } from 'react';
import { TrendingUp } from 'lucide-react';
import { AttendanceTrendPoint } from '../../types/dashboard';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';

interface AttendanceTrendCardProps {
  trend: AttendanceTrendPoint[];
  isLoading?: boolean;
}

export const AttendanceTrendCard: React.FC<AttendanceTrendCardProps> = ({ trend, isLoading }) => {
  const [hoveredPoint, setHoveredPoint] = useState<AttendanceTrendPoint | null>(null);

  if (isLoading) {
    return <div className="skeleton" style={{ height: '220px', borderRadius: 'var(--radius-xl)' }} />;
  }

  // SVG Chart Geometry
  const width = 500;
  const height = 180;
  const padding = { top: 20, right: 30, bottom: 35, left: 40 };

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Calculate coordinates for points
  const points = trend.map((p, idx) => {
    const x = padding.left + (idx / Math.max(1, trend.length - 1)) * chartWidth;
    const y = padding.top + chartHeight - (p.rate / 100) * chartHeight;
    return { ...p, x, y };
  });

  // Construct SVG Path
  const linePath = points.reduce((acc, curr, idx) => {
    if (idx === 0) return `M ${curr.x} ${curr.y}`;
    const prev = points[idx - 1];
    const cpX1 = prev.x + (curr.x - prev.x) / 2;
    const cpY1 = prev.y;
    const cpX2 = prev.x + (curr.x - prev.x) / 2;
    const cpY2 = curr.y;
    return `${acc} C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${curr.x} ${curr.y}`;
  }, '');

  const areaPath = points.length > 0
    ? `${linePath} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`
    : '';

  const yTicks = [0, 25, 50, 75, 100];

  return (
    <Card className="dashboard-operational-card">
      <CardHeader style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <TrendingUp size={16} />
            </div>
            <CardTitle style={{ fontSize: '0.9375rem', fontWeight: 800 }}>اتجاه الحضور خلال آخر 7 أيام</CardTitle>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {hoveredPoint ? (
              <Badge variant="primary">
                {hoveredPoint.day}: {hoveredPoint.rate}%
              </Badge>
            ) : (
              <Badge variant="success">مستقر (متوسط 74%)</Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardBody style={{ padding: '0.5rem 0.75rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ width: '100%', height: '170px', position: 'relative' }}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            style={{ width: '100%', height: '100%', overflow: 'visible' }}
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="attendanceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Horizontal Grid lines and Y-axis labels */}
            {yTicks.map((tick) => {
              const y = padding.top + chartHeight - (tick / 100) * chartHeight;
              return (
                <g key={tick}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke="#e2e8f0"
                    strokeDasharray={tick === 0 ? 'none' : '3 3'}
                    strokeWidth="1"
                  />
                  <text
                    x={padding.left - 8}
                    y={y + 3}
                    textAnchor="end"
                    fontSize="10"
                    fill="#94a3b8"
                    fontFamily="Cairo, sans-serif"
                  >
                    {tick}%
                  </text>
                </g>
              );
            })}

            {/* Area Fill */}
            {areaPath && <path d={areaPath} fill="url(#attendanceGradient)" />}

            {/* Line Path */}
            {linePath && <path d={linePath} fill="none" stroke="#2563eb" strokeWidth="2.5" strokeLinecap="round" />}

            {/* Data Points and X-Axis Labels */}
            {points.map((pt, idx) => (
              <g key={idx}>
                {/* Vertical tick lines */}
                <line
                  x1={pt.x}
                  y1={padding.top + chartHeight}
                  x2={pt.x}
                  y2={padding.top + chartHeight + 4}
                  stroke="#cbd5e1"
                  strokeWidth="1"
                />

                {/* X-axis label */}
                <text
                  x={pt.x}
                  y={padding.top + chartHeight + 18}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#64748b"
                  fontWeight="600"
                  fontFamily="Cairo, sans-serif"
                >
                  {pt.dayShort || pt.day}
                </text>

                {/* Point circle */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={hoveredPoint?.date === pt.date ? 5.5 : 3.5}
                  fill="#ffffff"
                  stroke="#2563eb"
                  strokeWidth={hoveredPoint?.date === pt.date ? 3 : 2}
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                  onMouseEnter={() => setHoveredPoint(pt)}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
              </g>
            ))}
          </svg>
        </div>
      </CardBody>
    </Card>
  );
};

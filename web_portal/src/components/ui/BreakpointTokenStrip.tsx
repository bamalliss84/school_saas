import React from 'react';
import { Monitor, Laptop, Tablet, Smartphone } from 'lucide-react';

export interface BreakpointTokenStripProps {
  activeBreakpoint?: 'desktop' | 'laptop' | 'tablet' | 'mobile';
  onSelectBreakpoint?: (bp: 'desktop' | 'laptop' | 'tablet' | 'mobile') => void;
  className?: string;
}

export const BreakpointTokenStrip: React.FC<BreakpointTokenStripProps> = ({
  activeBreakpoint,
  onSelectBreakpoint,
  className = '',
}) => {
  const breakpoints = [
    {
      id: 'desktop' as const,
      label: 'Desktop (1440px+)',
      icon: Monitor,
      desc: 'المساحة الإدارية الكاملة',
    },
    {
      id: 'laptop' as const,
      label: 'Laptop (1024–1439px)',
      icon: Laptop,
      desc: 'اللوحة التكيفية',
    },
    {
      id: 'tablet' as const,
      label: 'Tablet (768–1023px)',
      icon: Tablet,
      desc: 'المساحة المدمجة',
    },
    {
      id: 'mobile' as const,
      label: 'Mobile (360–767px)',
      icon: Smartphone,
      desc: 'الواجهة المتجاوبة الميدانية',
    },
  ];

  return (
    <div className={`breakpoint-token-strip ${className}`.trim()} aria-label="شريط أبعاد الشاشات المتجاوبة">
      {breakpoints.map((bp) => {
        const Icon = bp.icon;
        const isActive = activeBreakpoint === bp.id;

        if (onSelectBreakpoint) {
          return (
            <button
              key={bp.id}
              type="button"
              className={`breakpoint-token-pill ${isActive ? 'active' : ''}`}
              onClick={() => onSelectBreakpoint(bp.id)}
              style={{ cursor: 'pointer', border: 'none' }}
              title={bp.desc}
            >
              <Icon size={14} />
              <span>{bp.label}</span>
            </button>
          );
        }

        return (
          <span
            key={bp.id}
            className={`breakpoint-token-pill ${isActive ? 'active' : ''}`}
            title={bp.desc}
          >
            <Icon size={14} />
            <span>{bp.label}</span>
          </span>
        );
      })}
    </div>
  );
};

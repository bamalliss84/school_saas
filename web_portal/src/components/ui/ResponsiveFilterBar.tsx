import React, { useState } from 'react';
import { Search, Filter, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './Button';

export interface ResponsiveFilterBarProps {
  searchValue: string;
  onSearchChange: (val: string) => void;
  searchPlaceholder?: string;
  filtersContent?: React.ReactNode;
  activeFilterCount?: number;
  onResetFilters?: () => void;
  actionsContent?: React.ReactNode;
  className?: string;
}

export const ResponsiveFilterBar: React.FC<ResponsiveFilterBarProps> = ({
  searchValue,
  onSearchChange,
  searchPlaceholder = 'بحث...',
  filtersContent,
  activeFilterCount = 0,
  onResetFilters,
  actionsContent,
  className = '',
}) => {
  const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false);

  return (
    <div className={`responsive-filter-bar ${className}`.trim()} role="search" aria-label="شريط البحث والتصفية">
      <div className="filter-desktop-row">
        {/* Search input */}
        <div style={{ position: 'relative', minWidth: '220px', flex: 1 }}>
          <Search
            size={14}
            style={{
              position: 'absolute',
              right: '0.625rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--neutral-400)',
              pointerEvents: 'none',
            }}
          />
          <input
            type="search"
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="form-input"
            style={{ paddingRight: '2rem', height: '36px', fontSize: '0.8125rem' }}
          />
        </div>

        {/* Mobile Filter Toggle Button */}
        {filtersContent && (
          <Button
            variant="outline"
            size="sm"
            className="filter-mobile-toggle"
            onClick={() => setIsMobileFiltersOpen(!isMobileFiltersOpen)}
            leftIcon={<Filter size={14} />}
            rightIcon={isMobileFiltersOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          >
            <span>الفلاتر {activeFilterCount > 0 ? `(${activeFilterCount})` : ''}</span>
          </Button>
        )}

        {/* Desktop Inline Filters */}
        {filtersContent && (
          <div className="filter-inline-controls">
            {filtersContent}
            {onResetFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={onResetFilters}
                leftIcon={<RotateCcw size={13} />}
                title="إعادة تعيين الفلاتر"
              >
                إعادة تعيين
              </Button>
            )}
          </div>
        )}

        {/* Primary/Secondary Actions (e.g. Export / Add) */}
        {actionsContent && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {actionsContent}
          </div>
        )}
      </div>

      {/* Mobile Collapsible Filters Panel */}
      {filtersContent && isMobileFiltersOpen && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.625rem',
            paddingTop: '0.75rem',
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          {filtersContent}
          {onResetFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                onResetFilters();
                setIsMobileFiltersOpen(false);
              }}
              leftIcon={<RotateCcw size={13} />}
              style={{ alignSelf: 'flex-start' }}
            >
              إعادة تعيين الفلاتر
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

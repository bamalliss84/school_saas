import React from 'react';

export interface ResponsiveTableColumn<T> {
  key: string;
  header: string;
  render?: (item: T, index: number) => React.ReactNode;
  width?: string;
  align?: 'right' | 'center' | 'left';
}

export interface ResponsiveTableProps<T> {
  columns: ResponsiveTableColumn<T>[];
  data: T[];
  keyExtractor: (item: T, index: number) => string | number;
  mobileCardRender?: (item: T, index: number) => React.ReactNode;
  enableMobileCardView?: boolean;
  className?: string;
  emptyMessage?: string;
}

export function ResponsiveTable<T>({
  columns,
  data,
  keyExtractor,
  mobileCardRender,
  enableMobileCardView = true,
  className = '',
  emptyMessage = 'لا توجد بيانات متاحة',
}: ResponsiveTableProps<T>) {
  if (data.length === 0) {
    return (
      <div
        className="responsive-table-container"
        style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div
      className={`responsive-table-container ${enableMobileCardView && mobileCardRender ? 'has-mobile-card-view' : ''} ${className}`.trim()}
    >
      {/* Desktop & Tablet Table */}
      <table className="responsive-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                style={{
                  width: col.width,
                  textAlign: col.align || 'right',
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr key={keyExtractor(item, idx)}>
              {columns.map((col) => (
                <td
                  key={col.key}
                  style={{
                    textAlign: col.align || 'right',
                  }}
                >
                  {col.render ? col.render(item, idx) : (item as Record<string, unknown>)[col.key] as React.ReactNode}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Mobile Card List (When enableMobileCardView is active) */}
      {enableMobileCardView && mobileCardRender && (
        <div className="table-mobile-card-list">
          {data.map((item, idx) => (
            <div key={keyExtractor(item, idx)} className="table-mobile-card">
              {mobileCardRender(item, idx)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { HistoricalBanner } from './HistoricalBanner';
import { ContextSelectorModal } from '../feedback/ContextSelectorModal';

export const AppShell: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />
      <div className="main-wrapper">
        <Topbar />
        <HistoricalBanner />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
      <ContextSelectorModal />
    </div>
  );
};

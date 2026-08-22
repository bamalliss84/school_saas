import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { HistoricalBanner } from './HistoricalBanner';
import { ContextSelectorModal } from '../feedback/ContextSelectorModal';
import { OfflineBanner } from '../feedback/OfflineState';
import { useNetworkStatus } from '../../hooks/useNetworkStatus';

export const AppShell: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { isOffline } = useNetworkStatus();

  return (
    <div className="app-shell">
      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />
      <div className="main-wrapper">
        {isOffline && <OfflineBanner />}
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


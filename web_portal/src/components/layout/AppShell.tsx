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
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const { isOffline } = useNetworkStatus();

  return (
    <div className="app-shell">
      {/* Mobile Drawer Backdrop */}
      <div
        className={`mobile-nav-backdrop ${isMobileSidebarOpen ? 'show' : ''}`}
        onClick={() => setIsMobileSidebarOpen(false)}
        aria-hidden="true"
      />

      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />
      <div className="main-wrapper">
        {isOffline && <OfflineBanner />}
        <Topbar onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)} />
        <HistoricalBanner />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
      <ContextSelectorModal />
    </div>
  );
};



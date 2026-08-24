import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Building2,
  LayoutDashboard,
  GraduationCap,
  Users,
  Layers,
  BookOpen,
  Calendar,
  Clock,
  FileText,
  Award,
  MessageSquare,
  Bell,
  BarChart3,
  Database,
  Settings,
  ChevronRight,
  ChevronLeft,
  X,
} from 'lucide-react';
import { useAuth } from '../../context';
import { isRouteActive } from '../../utils/navigation';

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggleCollapse,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const { activeMembership } = useAuth();
  const location = useLocation();

  const unreadConversations = activeMembership?.unread_conversations_count || 0;
  const unreadNotifications = activeMembership?.unread_notifications_count || 0;

  const navItems = [
    { to: '/dashboard', label: 'الرئيسية', icon: LayoutDashboard },
    { to: '/students', label: 'الطلاب', icon: GraduationCap },
    { to: '/teachers', label: 'المعلمون', icon: Users },
    { to: '/classes', label: 'الفصول والشعب', icon: Layers },
    { to: '/subjects', label: 'المواد الدراسية', icon: BookOpen },
    { to: '/timetable', label: 'الجداول', icon: Calendar },
    { to: '/attendance', label: 'الحضور والانصراف', icon: Clock },
    { to: '/homework', label: 'الواجبات', icon: FileText },
    { to: '/exams', label: 'الاختبارات والنتائج', icon: Award },
    {
      to: '/messages',
      label: 'الرسائل',
      icon: MessageSquare,
      badge: unreadConversations > 0 ? unreadConversations : undefined,
    },
    {
      to: '/announcements',
      label: 'الإعلانات والإشعارات',
      icon: Bell,
      badge: unreadNotifications > 0 ? unreadNotifications : undefined,
    },
    { to: '/reports', label: 'التقارير', icon: BarChart3 },
    { to: '/data', label: 'الاستيراد والتصدير', icon: Database },
    { to: '/settings', label: 'الإعدادات', icon: Settings },
  ];

  const handleLinkClick = () => {
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  return (
    <aside
      className={`sidebar ${collapsed ? 'collapsed' : ''} ${isMobileOpen ? 'mobile-open' : ''}`}
      aria-label="القائمة الجانبية"
    >
      <div className="sidebar-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          {!collapsed ? (
            <div className="sidebar-brand">
              <div className="sidebar-brand-icon">
                <Building2 size={18} />
              </div>
              <span>منصة المدرسة</span>
            </div>
          ) : (
            <div className="sidebar-brand-icon" title="منصة المدرسة">
              <Building2 size={18} />
            </div>
          )}

          {/* Close button on mobile */}
          {onCloseMobile && (
            <button
              type="button"
              className="sidebar-mobile-close-btn"
              onClick={onCloseMobile}
              aria-label="إغلاق القائمة الجانبية"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {!collapsed && (
          <div className="sidebar-school-info">
            <span className="sidebar-school-label">اسم المدرسة:</span>
            <span className="sidebar-school-name" title={activeMembership?.school?.name || 'مدرسة النور الأهلية'}>
              {activeMembership?.school?.name || 'مدرسة النور الأهلية'}
            </span>
            <span className="sidebar-academic-year">
              {activeMembership?.academic_year?.name
                ? `العام الدراسي ${activeMembership.academic_year.name}`
                : 'العام الدراسي 2026/2027'}
            </span>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = isRouteActive(location.pathname, item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={`sidebar-link ${isActive ? 'active' : ''}`}
              title={collapsed ? item.label : undefined}
              onClick={handleLinkClick}
            >
              <Icon className="sidebar-link-icon" size={18} />
              {(!collapsed || isMobileOpen) && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flex: 1, minWidth: 0 }}>
                  <span className="text-truncate">{item.label}</span>
                  {item.badge !== undefined && (
                    <span className="sidebar-badge">{item.badge}</span>
                  )}
                </div>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          onClick={onToggleCollapse}
          className="sidebar-collapse-btn"
          title={collapsed ? 'توسيع القائمة' : 'طي القائمة'}
          aria-label={collapsed ? 'توسيع القائمة' : 'طي القائمة'}
        >
          {!collapsed && <span>طي القائمة</span>}
          {collapsed ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
        </button>
      </div>
    </aside>
  );
};


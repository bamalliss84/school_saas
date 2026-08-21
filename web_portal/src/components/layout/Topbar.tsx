import React, { useState, useRef, useEffect } from 'react';
import {
  Bell,
  MessageSquare,
  LogOut,
  ChevronDown,
  Search,
  User as UserIcon,
} from 'lucide-react';
import { useAuth } from '../../context';

export const Topbar: React.FC = () => {
  const {
    user,
    activeMembership,
    logout,
    setShowContextModal,
  } = useAuth();

  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const totalUnreadNotifications = activeMembership?.unread_notifications_count || 2;
  const totalUnreadConversations = activeMembership?.unread_conversations_count || 2;

  const schoolName = activeMembership?.school?.name || 'مدرسة النور الأهلية';
  const academicYear = activeMembership?.academic_year?.name || '2026 / 2027';
  const userFullName = user?.full_name || 'أحمد محمد';
  const userRoleText = user?.role === 'super_admin' ? 'مدير عام النظام' : 'مدير المدرسة';

  return (
    <header className="topbar">
      {/* Right side (RTL): Active School & Academic Year Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <button
          onClick={() => setShowContextModal(true)}
          className="topbar-context-btn"
          title="انقر لتغيير المدرسة أو العام الدراسي"
          aria-label="تغيير سياق المدرسة والعام الدراسي"
        >
          <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--neutral-900)' }}>
              {schoolName} / {academicYear}
            </span>
            <span style={{ fontSize: '0.625rem', color: 'var(--primary-600)', display: 'flex', alignItems: 'center', gap: '0.1875rem', fontWeight: 600 }}>
              <span>تغيير السياق</span>
              <ChevronDown size={10} />
            </span>
          </div>
        </button>
      </div>

      {/* Center: Global Search affordance */}
      <div className="topbar-search-wrap" role="search">
        <Search size={14} className="topbar-search-icon" aria-hidden="true" />
        <input
          type="search"
          placeholder="ابحث..."
          className="topbar-search-input"
          aria-label="البحث في لوحة التحكم"
          readOnly
        />
      </div>

      {/* Left side (RTL): Badges, Notifications, User Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {/* Messages */}
        <button
          className="topbar-icon-btn"
          title="المحادثات والرسائل"
          aria-label="المحادثات والرسائل"
          type="button"
        >
          <MessageSquare size={16} />
          {totalUnreadConversations > 0 && (
            <span className="topbar-badge-count">
              {totalUnreadConversations}
            </span>
          )}
        </button>

        {/* Notifications */}
        <button
          className="topbar-icon-btn"
          title="الإشعارات"
          aria-label="الإشعارات"
          type="button"
        >
          <Bell size={16} />
          {totalUnreadNotifications > 0 && (
            <span className="topbar-badge-count">
              {totalUnreadNotifications}
            </span>
          )}
        </button>

        <div style={{ height: '16px', width: '1px', backgroundColor: 'var(--border-subtle)' }} />

        {/* User Profile Area */}
        <div ref={menuRef} style={{ position: 'relative' }}>
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '0.1875rem 0.25rem',
              borderRadius: 'var(--radius-md)',
            }}
            aria-expanded={isUserMenuOpen}
            aria-haspopup="true"
            aria-label="قائمة المستخدم"
          >
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                backgroundColor: 'var(--primary-700)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.75rem',
              }}
            >
              {userFullName.charAt(0)}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--neutral-900)' }}>
                {userFullName}
              </span>
              <span style={{ fontSize: '0.625rem', color: 'var(--neutral-500)' }}>
                {userRoleText}
              </span>
            </div>

            <ChevronDown size={12} style={{ color: 'var(--neutral-400)' }} />
          </button>

          {/* User Menu Dropdown (Section D) */}
          {isUserMenuOpen && (
            <div className="topbar-user-menu" role="menu">
              <button
                className="topbar-user-menu-item"
                role="menuitem"
                onClick={() => setIsUserMenuOpen(false)}
              >
                <UserIcon size={16} />
                <span>الملف الشخصي</span>
              </button>

              <button
                className="topbar-user-menu-item danger"
                role="menuitem"
                onClick={() => {
                  setIsUserMenuOpen(false);
                  logout();
                }}
              >
                <LogOut size={16} />
                <span>تسجيل الخروج</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

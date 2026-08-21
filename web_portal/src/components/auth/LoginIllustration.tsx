import React from 'react';
import {
  Users,
  Calendar,
  ClipboardList,
  FileText,
  PieChart,
  BarChart3,
  User,
  GraduationCap,
  Sparkles,
} from 'lucide-react';

export const LoginIllustration: React.FC = () => {
  return (
    <div className="login-illustration-container" aria-hidden="true">
      <div className="login-hub-diagram">
        {/* Background connecting spoke lines */}
        <svg className="hub-spokes" viewBox="0 0 260 190" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Central hub center is at (130, 95) */}
          <path d="M130 95 L130 30" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L200 46" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L218 99" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L195 152" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L130 162" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L65 152" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L42 99" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M130 95 L60 46" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
        </svg>

        {/* Central Hub Node */}
        <div className="hub-node hub-node-center">
          <div className="hub-center-avatar">
            <User size={22} strokeWidth={2.2} />
            <span className="hub-center-badge">
              <Sparkles size={8} />
            </span>
          </div>
        </div>

        {/* Outer Nodes */}
        {/* 1. Top - Students / Classes */}
        <div className="hub-node hub-node-top">
          <Users size={14} />
        </div>

        {/* 2. Top Right - Schedule / Calendar */}
        <div className="hub-node hub-node-tr">
          <Calendar size={14} />
        </div>

        {/* 3. Right - Assignments / Grades */}
        <div className="hub-node hub-node-r">
          <ClipboardList size={14} />
        </div>

        {/* 4. Bottom Right - Reports / Files */}
        <div className="hub-node hub-node-br">
          <FileText size={14} />
        </div>

        {/* 5. Bottom - Analytics / Pie */}
        <div className="hub-node hub-node-b">
          <PieChart size={14} />
        </div>

        {/* 6. Bottom Left - Stats / Performance */}
        <div className="hub-node hub-node-bl">
          <BarChart3 size={14} />
        </div>

        {/* 7. Left - Teachers */}
        <div className="hub-node hub-node-l">
          <User size={14} />
        </div>

        {/* 8. Top Left - School / Graduation */}
        <div className="hub-node hub-node-tl">
          <GraduationCap size={14} />
        </div>
      </div>
    </div>
  );
};

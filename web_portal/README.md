# School Admin Web Portal (بوابة مدير المدرسة)

بوابة إدارة المدرسة (Web Portal) لنظام School SaaS متعدد المدارس (Multi-Tenant)، مبنية باستخدام React وTypeScript وVite مع دعم كامل للغة العربية (RTL) وتصميم مكتبي ولوحي متجاوب.

---

## 1. التقنيات المستخدمة (Tech Stack)

- **Frontend Framework:** React 18
- **Language:** TypeScript 5
- **Build Tool / Bundler:** Vite 5
- **Routing:** React Router v6
- **Server State Management:** TanStack Query v5
- **Forms & Validation:** React Hook Form
- **Icons:** Lucide React
- **Styling:** Centralized CSS Tokens & Design System (Arabic RTL First)
- **Unit & Integration Testing:** Vitest + React Testing Library

---

## 2. هيكل المشروع (Project Structure)

```text
web_portal/
├── docs/
│   ├── ROADMAP.md
│   ├── API_CAPABILITY_MATRIX.md
│   ├── API_GAP_REPORT.md
│   ├── ARCHITECTURE.md
│   ├── prompts/
│   └── acceptance/
│       └── PHASE_W1_ACCEPTANCE.md
├── design/
│   ├── nano/
│   └── references/
├── src/
│   ├── __tests__/           # اختبارات الوحدة والتكامل
│   ├── components/
│   │   ├── feedback/        # مكونات التفاعل (Spinner, Skeletons, Modals, ErrorAlert)
│   │   ├── layout/          # الهيكل العام (AppShell, Sidebar, Topbar, HistoricalBanner)
│   │   └── ui/              # المكونات الأساسية (Button, Card, Badge, Input)
│   ├── context/             # سياق المصادقة وعزل المدارس (AuthContext)
│   ├── pages/               # الصفحات الرئيسية (Login, ContextSelection, Dashboard, Unauthorized, 404)
│   ├── routes/              # المسارات وحراس الصلاحيات (AuthGuard, SchoolAdminGuard, ContextGuard)
│   ├── services/            # عميل API وخدمات المصادقة والسياق (apiClient, authService, contextService)
│   ├── styles/              # نظام التصميم والمتغيرات (tokens.css, globals.css, components.css)
│   ├── types/               # النماذج والواجهات (auth, context, api)
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 3. التشغيل والتطوير (Getting Started)

### تثبيت الاعتماديات
```bash
cd web_portal
npm install
```

### تشغيل خادم التطوير (Dev Server)
خادم التطوير مهيأ ببروكسي تلقائي للـ Backend على `http://127.0.0.1:8000`:
```bash
npm run dev
```

### الفحص والاختبارات
```bash
# فحص الأنواع (Typecheck)
npm run typecheck

# فحص التنسيق والجودة (Lint)
npm run lint

# تشغيل اختبارات Vitest
npm run test

# بناء حزمة الإنتاج (Production Build)
npm run build
```

---

## 4. سياسات الأمان وتعدد المدارس (Security & Multi-Tenancy)

1. **عزل المستأجرين (Tenant Isolation):** يتم إرسال رأس `X-School-Membership-ID` تلقائياً مع كل طلب مدرسي، ولا يعتمد النظام أبداً على معرف مرسل من العميل في نص الطلب.
2. **سياق الأرشيف (Historical Context):** يتم حظر جميع عمليات الإضافة والتعديل تلقائياً عند تصفح سياق تاريخي، مع إظهار شريط تنبيه بارز في الواجهة.
3. **حماية الأدوار (Role Guards):** البوابة مخصصة حصراً لمديري المدارس (`school_admin`) والمسؤولين العامين (`super_admin`). الأدوار الأخرى (المعلمون، أولياء الأمور، الطلاب) يتم حظرها وتوجيهها لصفحة غير مصرح.
4. **تخزين الرموز (Token Storage):** الرموز تدار في الذاكرة ومرتبطة بآلية تجديد أحادية المسار (Single-Flight Refresh) وحذف فوري عند تسجيل الخروج.

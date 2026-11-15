import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Starter legal texts. They must be reviewed by a lawyer for the target market
 * before commercial launch; the version date is shown so schools can track changes.
 */
const VERSION = '2026-11-15';

type Section = { title: string; body: string[] };

const LegalLayout: React.FC<{ title: string; sections: Section[] }> = ({ title, sections }) => (
  <div dir="rtl" style={{ minHeight: '100vh', background: 'var(--color-bg, #f8fafc)', padding: '2rem 1rem' }}>
    <article style={{ maxWidth: 820, margin: '0 auto', background: 'var(--color-surface, #fff)', borderRadius: 16, padding: '2rem', lineHeight: 1.9, boxShadow: '0 1px 3px rgba(15,23,42,.08)' }}>
      <header style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>{title}</h1>
        <small>آخر تحديث: {VERSION}</small>
      </header>
      {sections.map((section) => (
        <section key={section.title} style={{ marginBottom: '1.25rem' }}>
          <h2 style={{ fontSize: '1.15rem' }}>{section.title}</h2>
          {section.body.map((paragraph) => <p key={paragraph} style={{ margin: '.4rem 0' }}>{paragraph}</p>)}
        </section>
      ))}
      <footer style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
        <Link to="/terms">شروط الاستخدام</Link>
        <Link to="/privacy">سياسة الخصوصية</Link>
        <Link to="/login">تسجيل الدخول</Link>
      </footer>
    </article>
  </div>
);

const TERMS: Section[] = [
  { title: '1. التعريفات', body: ['"المنصة" هي نظام إدارة المدارس وتطبيقاته. "المدرسة" هي الجهة المشتركة. "المستخدم" هو كل من يدخل المنصة من إداريين ومعلمين وطلاب وأولياء أمور.'] },
  { title: '2. الاشتراك والحساب', body: [
    'تشترك المدرسة في المنصة وفق الباقة المتفق عليها، وتكون مسؤولة عن إنشاء حسابات مستخدميها وصحة بياناتهم.',
    'يلتزم كل مستخدم بالحفاظ على سرية كلمة المرور، وعدم مشاركة حسابه مع غيره.',
  ] },
  { title: '3. الاستخدام المقبول', body: [
    'يُستخدم النظام لأغراض تعليمية وإدارية مشروعة فقط.',
    'يُمنع محاولة الوصول إلى بيانات مدرسة أخرى أو مستخدم آخر، أو تعطيل الخدمة، أو رفع محتوى مخالف أو ضار.',
  ] },
  { title: '4. ملكية البيانات', body: ['بيانات المدرسة وطلابها ملك للمدرسة. تعالجها المنصة نيابة عنها لتقديم الخدمة فقط، ويمكن للمدرسة تصدير بياناتها في أي وقت.'] },
  { title: '5. الرسوم والدفع', body: ['تُحدد رسوم الاشتراك حسب الباقة وعدد الطلاب. رسوم المدرسة على أولياء الأمور تحددها المدرسة، والمنصة أداة لعرضها وتسجيلها فقط.'] },
  { title: '6. توفر الخدمة', body: ['نسعى لتوفير الخدمة باستمرار، مع صيانة مجدولة يُعلن عنها مسبقًا قدر الإمكان، ونسخ احتياطي دوري للبيانات.'] },
  { title: '7. إنهاء الاشتراك', body: ['عند انتهاء الاشتراك تبقى بيانات المدرسة متاحة للتصدير لمدة محددة في العقد، ثم تُحذف بشكل آمن.'] },
  { title: '8. التواصل', body: ['للاستفسارات تواصل مع إدارة مدرستك أولًا، أو مع دعم المنصة عبر قنوات الدعم الرسمية.'] },
];

const PRIVACY: Section[] = [
  { title: '1. ما البيانات التي نجمعها', body: [
    'بيانات الحساب: الاسم، اسم المستخدم، البريد أو رقم الجوال.',
    'البيانات المدرسية: التسجيل في الصفوف، الحضور، الواجبات، النتائج، الرسائل والإعلانات، والرسوم والمدفوعات.',
  ] },
  { title: '2. لماذا نستخدمها', body: ['لتشغيل الخدمة للمدرسة فقط: عرض البيانات للمستخدم المصرّح له، وإرسال الإشعارات، وإعداد التقارير. لا نبيع البيانات ولا نستخدمها للإعلانات.'] },
  { title: '3. بيانات الأطفال', body: ['بيانات الطلاب حساسة. يرى ولي الأمر بيانات أبنائه فقط، والمعلم طلاب فصوله فقط، والمدرسة طلابها فقط. لا تُكشف بيانات مدرسة لمدرسة أخرى.'] },
  { title: '4. الحماية', body: ['نستخدم اتصالًا مشفرًا، وصلاحيات حسب الدور، وفصلًا صارمًا بين المدارس، وسجلًا للتعديلات الحساسة، ونسخًا احتياطيًا دوريًا.'] },
  { title: '5. المشاركة مع أطراف أخرى', body: ['لا نشارك البيانات إلا مع مزودي الخدمة اللازمين للتشغيل (مثل الاستضافة والبريد)، وبالقدر اللازم، أو عند وجود إلزام قانوني.'] },
  { title: '6. الاحتفاظ والحذف', body: ['نحتفظ بالبيانات طوال مدة اشتراك المدرسة، ويحفظ السجل الأكاديمي التاريخي للطالب. عند إنهاء الاشتراك تُحذف البيانات بعد مدة التصدير المتفق عليها.'] },
  { title: '7. حقوقك', body: ['يمكنك طلب الاطلاع على بياناتك أو تصحيحها عبر إدارة مدرستك.'] },
];

export const TermsPage: React.FC = () => <LegalLayout title="شروط الاستخدام" sections={TERMS} />;
export const PrivacyPage: React.FC = () => <LegalLayout title="سياسة الخصوصية" sections={PRIVACY} />;

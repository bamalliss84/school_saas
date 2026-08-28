import React, { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  Search,
  Layers,
  Users,
  BookOpen,
  Edit2,
  Trash2,
  CheckCircle,
  XCircle,
  RotateCw,
  Clock,
} from 'lucide-react';
import { useAuth } from '../context/useAuth';
import { useToast } from '../context/useToast';
import { academicService } from '../services/academicService';
import {
  Classroom,
  ClassroomCreateInput,
  ClassroomUpdateInput,
  Section,
  SectionCreateInput,
  SectionUpdateInput,
  ClassSubject,
  Subject,
} from '../types/academic';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';
import { ConfirmationModal } from '../components/feedback/ConfirmationModal';
import { ClassroomModal } from '../components/academic/ClassroomModal';
import { SectionModal } from '../components/academic/SectionModal';
import { ClassSubjectModal } from '../components/academic/ClassSubjectModal';

export const ClassesPage: React.FC = () => {
  const { activeMembership, isReadOnly } = useAuth();
  const { success, error } = useToast();

  // State: Classrooms
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [selectedClassroomId, setSelectedClassroomId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoadingClasses, setIsLoadingClasses] = useState(true);
  const [classesError, setClassesError] = useState<string | null>(null);

  // State: Sections for selected classroom
  const [sections, setSections] = useState<Section[]>([]);
  const [isLoadingSections, setIsLoadingSections] = useState(false);

  // State: ClassSubjects for selected classroom
  const [classSubjects, setClassSubjects] = useState<ClassSubject[]>([]);
  const [isLoadingClassSubjects, setIsLoadingClassSubjects] = useState(false);

  // State: Available School Subjects
  const [schoolSubjects, setSchoolSubjects] = useState<Subject[]>([]);

  // Active Detail Tab: 'sections' | 'subjects'
  const [activeTab, setActiveTab] = useState<'sections' | 'subjects'>('sections');

  // Modals state
  const [isClassModalOpen, setIsClassModalOpen] = useState(false);
  const [editingClassroom, setEditingClassroom] = useState<Classroom | null>(null);

  const [isSectionModalOpen, setIsSectionModalOpen] = useState(false);
  const [editingSection, setEditingSection] = useState<Section | null>(null);

  const [isClassSubjectModalOpen, setIsClassSubjectModalOpen] = useState(false);
  const [editingClassSubject, setEditingClassSubject] = useState<ClassSubject | null>(null);

  // Delete Confirmations
  const [deletingItem, setDeletingItem] = useState<{
    type: 'classroom' | 'section' | 'class_subject';
    id: number;
    name: string;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const selectedClassroom = classrooms.find((c) => c.id === selectedClassroomId) || null;

  // 1. Fetch Classrooms
  const fetchClassrooms = useCallback(async () => {
    setIsLoadingClasses(true);
    setClassesError(null);
    try {
      const res = await academicService.getClassrooms({ search: searchQuery });
      setClassrooms(res.results);
      if (res.results.length > 0) {
        setSelectedClassroomId((prev) => {
          const exists = res.results.some((c) => c.id === prev);
          return exists ? prev : res.results[0].id;
        });
      } else {
        setSelectedClassroomId(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'تعذر تحميل الصفوف الدراسية';
      setClassesError(msg);
      error(msg);
    } finally {
      setIsLoadingClasses(false);
    }
  }, [searchQuery, error]);

  // 2. Fetch School Subjects (for curriculum assignment)
  const fetchSchoolSubjects = useCallback(async () => {
    try {
      const res = await academicService.getSubjects({ is_active: true });
      setSchoolSubjects(res.results);
    } catch {
      // Silent catch or fallback
    }
  }, []);

  // 3. Fetch Sections for Selected Classroom
  const fetchSections = useCallback(async (classroomId: number) => {
    setIsLoadingSections(true);
    try {
      const res = await academicService.getSections({ classroom_id: classroomId });
      setSections(res.results);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'تعذر تحميل الشعب الدراسية';
      error(msg);
    } finally {
      setIsLoadingSections(false);
    }
  }, [error]);

  // 4. Fetch ClassSubjects for Selected Classroom
  const fetchClassSubjects = useCallback(async (classroomId: number) => {
    setIsLoadingClassSubjects(true);
    try {
      const res = await academicService.getClassSubjects({ classroom_id: classroomId });
      setClassSubjects(res.results);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'تعذر تحميل مواد الصف';
      error(msg);
    } finally {
      setIsLoadingClassSubjects(false);
    }
  }, [error]);

  // Trigger load on context or search change
  useEffect(() => {
    fetchClassrooms();
    fetchSchoolSubjects();
  }, [activeMembership?.membership_id, activeMembership?.academic_year?.id, fetchClassrooms, fetchSchoolSubjects]);

  // Trigger sections & class-subjects load when selected classroom changes
  useEffect(() => {
    if (selectedClassroomId) {
      fetchSections(selectedClassroomId);
      fetchClassSubjects(selectedClassroomId);
    } else {
      setSections([]);
      setClassSubjects([]);
    }
  }, [selectedClassroomId, fetchSections, fetchClassSubjects]);

  // Handlers: Classroom Create/Edit
  const handleSaveClassroom = async (data: ClassroomCreateInput | ClassroomUpdateInput) => {
    if (editingClassroom) {
      const updated = await academicService.updateClassroom(editingClassroom.id, data);
      setClassrooms((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      success(`تم تحديث بيانات الصف "${updated.name}" بنجاح`);
    } else {
      const created = await academicService.createClassroom(data as ClassroomCreateInput);
      setClassrooms((prev) => [...prev, created]);
      setSelectedClassroomId(created.id);
      success(`تم إنشاء الصف الدراسي "${created.name}" بنجاح`);
    }
  };

  // Handlers: Section Create/Edit
  const handleSaveSection = async (data: SectionCreateInput | SectionUpdateInput) => {
    if (editingSection) {
      const updated = await academicService.updateSection(editingSection.id, data);
      setSections((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
      success(`تم تحديث الشعبة "${updated.name}" بنجاح`);
    } else {
      const created = await academicService.createSection(data as SectionCreateInput);
      setSections((prev) => [...prev, created]);
      if (selectedClassroomId) {
        setClassrooms((prev) =>
          prev.map((c) => (c.id === selectedClassroomId ? { ...c, sections_count: c.sections_count + 1 } : c))
        );
      }
      success(`تم إنشاء الشعبة "${created.name}" بنجاح`);
    }
  };

  // Handlers: ClassSubject Create/Edit
  const handleSaveClassSubject = async (data: { classroom: number; subject: number; weekly_periods: number }) => {
    if (editingClassSubject) {
      const updated = await academicService.updateClassSubject(editingClassSubject.id, {
        weekly_periods: data.weekly_periods,
      });
      setClassSubjects((prev) => prev.map((cs) => (cs.id === updated.id ? updated : cs)));
      success(`تم تحديث نصاب الحصص لمادة "${updated.subject_detail.name}"`);
    } else {
      const created = await academicService.createClassSubject(data);
      setClassSubjects((prev) => [...prev, created]);
      success(`تم إدراج المادة "${created.subject_detail.name}" في المنهج بنجاح`);
    }
  };

  // Delete Action Dispatcher
  const handleConfirmDelete = async () => {
    if (!deletingItem) return;
    setIsDeleting(true);
    try {
      if (deletingItem.type === 'classroom') {
        await academicService.deleteClassroom(deletingItem.id);
        setClassrooms((prev) => prev.filter((c) => c.id !== deletingItem.id));
        if (selectedClassroomId === deletingItem.id) {
          const remaining = classrooms.filter((c) => c.id !== deletingItem.id);
          setSelectedClassroomId(remaining[0]?.id || null);
        }
        success(`تم حذف الصف "${deletingItem.name}" بنجاح`);
      } else if (deletingItem.type === 'section') {
        await academicService.deleteSection(deletingItem.id);
        setSections((prev) => prev.filter((s) => s.id !== deletingItem.id));
        if (selectedClassroomId) {
          setClassrooms((prev) =>
            prev.map((c) => (c.id === selectedClassroomId ? { ...c, sections_count: Math.max(0, c.sections_count - 1) } : c))
          );
        }
        success(`تم حذف الشعبة "${deletingItem.name}" بنجاح`);
      } else if (deletingItem.type === 'class_subject') {
        await academicService.deleteClassSubject(deletingItem.id);
        setClassSubjects((prev) => prev.filter((cs) => cs.id !== deletingItem.id));
        success(`تم استبعاد مادة "${deletingItem.name}" من المنهج`);
      }
      setDeletingItem(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'تعذر تنفيذ الحذف نظراً لارتباط سجلات أكاديمية به.';
      error(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              الصفوف والشعب
            </h1>
            <Badge variant="primary" icon={<Layers size={13} />}>
              {activeMembership?.academic_year?.name || 'العام الدراسي الحالي'}
            </Badge>
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>
            إدارة الهيكل الدراسي، المستويات التعليمية، الشعب، ومناهج الفصول
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchClassrooms}
            disabled={isLoadingClasses}
            leftIcon={<RotateCw size={14} className={isLoadingClasses ? 'animate-spin' : ''} />}
          >
            تحديث
          </Button>

          {!isReadOnly && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setEditingClassroom(null);
                setIsClassModalOpen(true);
              }}
              leftIcon={<Plus size={16} />}
            >
              إضافة صف دراسي
            </Button>
          )}
        </div>
      </div>

      {/* Main Content Layout: Master / Detail */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.5rem',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Classrooms Master List */}
        <Card>
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                قائمة الصفوف ({classrooms.length})
              </h2>
            </div>
            <Input
              placeholder="بحث في الصفوف (الاسم أو الرمز)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              rightIcon={<Search size={16} />}
              style={{ fontSize: '0.8125rem' }}
            />
          </div>

          <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
            {isLoadingClasses ? (
              <div style={{ padding: '3rem', textAlign: 'center' }}>
                <LoadingSpinner size={32} text="جاري تحميل الصفوف الدراسية..." />
              </div>
            ) : classesError ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--danger-600)' }}>
                <p>{classesError}</p>
                <Button variant="outline" size="sm" onClick={fetchClassrooms} style={{ marginTop: '0.75rem' }}>
                  إعادة المحاولة
                </Button>
              </div>
            ) : classrooms.length === 0 ? (
              <div style={{ padding: '2.5rem 1rem' }}>
                <EmptyState
                  variant={searchQuery ? 'filtered' : 'default'}
                  title={searchQuery ? 'لا توجد صفوف مطابقة للبحث' : 'لا توجد صفوف دراسية'}
                  description={
                    searchQuery
                      ? 'جرّب البحث باسم أو رمز آخر'
                      : 'ابدأ بإنشاء أول مستوى دراسي لهذا العام الأكاديمي.'
                  }
                  actionLabel={!isReadOnly && !searchQuery ? 'إضافة صف' : undefined}
                  onAction={() => {
                    setEditingClassroom(null);
                    setIsClassModalOpen(true);
                  }}
                  secondaryActionLabel={searchQuery ? 'مسح البحث' : undefined}
                  onSecondaryAction={() => setSearchQuery('')}
                />
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {classrooms.map((c) => {
                  const isSelected = c.id === selectedClassroomId;
                  return (
                    <div
                      key={c.id}
                      onClick={() => setSelectedClassroomId(c.id)}
                      style={{
                        padding: '1rem 1.25rem',
                        borderBottom: '1px solid var(--border-subtle)',
                        backgroundColor: isSelected ? 'var(--primary-50)' : 'transparent',
                        borderRight: isSelected ? '3px solid var(--primary-600)' : '3px solid transparent',
                        cursor: 'pointer',
                        transition: 'background-color var(--transition-fast)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--neutral-50)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: isSelected ? 'var(--primary-900)' : 'var(--text-primary)' }}>
                            {c.name}
                          </span>
                          <span
                            style={{
                              fontSize: '0.6875rem',
                              fontWeight: 600,
                              padding: '0.125rem 0.375rem',
                              borderRadius: 'var(--radius-sm)',
                              backgroundColor: 'var(--neutral-100)',
                              color: 'var(--text-muted)',
                            }}
                          >
                            {c.code}
                          </span>
                          {!c.is_active && (
                            <Badge variant="neutral" style={{ fontSize: '0.625rem' }}>غير نشط</Badge>
                          )}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          <span>{c.sections_count} شُعب</span>
                          <span>•</span>
                          <span>{c.students_count} طالب</span>
                        </div>
                      </div>

                      {!isReadOnly && (
                        <div
                          style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            type="button"
                            title="تعديل الصف"
                            onClick={() => {
                              setEditingClassroom(c);
                              setIsClassModalOpen(true);
                            }}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'var(--text-muted)',
                              cursor: 'pointer',
                              padding: '0.375rem',
                              borderRadius: 'var(--radius-sm)',
                            }}
                          >
                            <Edit2 size={15} />
                          </button>
                          <button
                            type="button"
                            title="حذف الصف"
                            onClick={() => {
                              setDeletingItem({
                                type: 'classroom',
                                id: c.id,
                                name: c.name,
                              });
                            }}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'var(--danger-500)',
                              cursor: 'pointer',
                              padding: '0.375rem',
                              borderRadius: 'var(--radius-sm)',
                            }}
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </Card>

        {/* Right Column: Selected Classroom Detail Workspace */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {selectedClassroom ? (
            <Card>
              {/* Classroom Detail Banner */}
              <div
                style={{
                  padding: '1.25rem 1.5rem',
                  borderBottom: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '1rem',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                      {selectedClassroom.name}
                    </h2>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '0.125rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--neutral-100)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {selectedClassroom.code}
                    </span>
                    {selectedClassroom.is_active ? (
                      <Badge variant="success" icon={<CheckCircle size={11} />}>نشط</Badge>
                    ) : (
                      <Badge variant="neutral" icon={<XCircle size={11} />}>معطل</Badge>
                    )}
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>
                    إجمالي الشعب: <strong>{sections.length}</strong> | إجمالي المواد بالمنهج: <strong>{classSubjects.length}</strong>
                  </p>
                </div>

                {/* Tabs Switcher */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    backgroundColor: 'var(--neutral-100)',
                    padding: '0.25rem',
                    borderRadius: 'var(--radius-lg)',
                    gap: '0.25rem',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setActiveTab('sections')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      padding: '0.375rem 0.875rem',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      border: 'none',
                      cursor: 'pointer',
                      backgroundColor: activeTab === 'sections' ? '#ffffff' : 'transparent',
                      color: activeTab === 'sections' ? 'var(--primary-700)' : 'var(--text-secondary)',
                      boxShadow: activeTab === 'sections' ? 'var(--shadow-sm)' : 'none',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <Users size={14} />
                    <span>الشعب الدراسية ({sections.length})</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab('subjects')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      padding: '0.375rem 0.875rem',
                      borderRadius: 'var(--radius-md)',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      border: 'none',
                      cursor: 'pointer',
                      backgroundColor: activeTab === 'subjects' ? '#ffffff' : 'transparent',
                      color: activeTab === 'subjects' ? 'var(--primary-700)' : 'var(--text-secondary)',
                      boxShadow: activeTab === 'subjects' ? 'var(--shadow-sm)' : 'none',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <BookOpen size={14} />
                    <span>المنهج والمواد ({classSubjects.length})</span>
                  </button>
                </div>
              </div>

              {/* Tab 1: Sections Workspace */}
              {activeTab === 'sections' && (
                <div style={{ padding: '1.25rem' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '1rem',
                    }}
                  >
                    <div>
                      <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        شعب الصف الدراسي
                      </h3>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.125rem 0 0 0' }}>
                        الفصول الميدانية المتاحة لتوزيع الطلاب وجدولة الحصص
                      </p>
                    </div>

                    {!isReadOnly && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setEditingSection(null);
                          setIsSectionModalOpen(true);
                        }}
                        leftIcon={<Plus size={14} />}
                      >
                        إضافة شعبة
                      </Button>
                    )}
                  </div>

                  {isLoadingSections ? (
                    <div style={{ padding: '3rem', textAlign: 'center' }}>
                      <LoadingSpinner size={32} text="جاري تحميل الشعب..." />
                    </div>
                  ) : sections.length === 0 ? (
                    <EmptyState
                      title="لا توجد شُعب لهذا الصف حتى الآن"
                      description="أضف الشعب الدراسية (مثل: أ، ب، ج) لتتمكن من تسجيل الطلاب وتعيين المعلمين."
                      actionLabel={!isReadOnly ? 'إضافة أول شعبة' : undefined}
                      onAction={() => {
                        setEditingSection(null);
                        setIsSectionModalOpen(true);
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                        gap: '1rem',
                      }}
                    >
                      {sections.map((sec) => (
                        <div
                          key={sec.id}
                          style={{
                            padding: '1rem',
                            border: '1px solid var(--border-subtle)',
                            borderRadius: 'var(--radius-lg)',
                            backgroundColor: 'var(--neutral-50)',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'space-between',
                            gap: '0.75rem',
                          }}
                        >
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span style={{ fontWeight: 800, fontSize: '1.0625rem', color: 'var(--text-primary)' }}>
                                شعبة {sec.name}
                              </span>
                              <span
                                style={{
                                  fontSize: '0.6875rem',
                                  fontWeight: 600,
                                  padding: '0.125rem 0.375rem',
                                  borderRadius: 'var(--radius-sm)',
                                  backgroundColor: 'var(--neutral-200)',
                                  color: 'var(--text-secondary)',
                                }}
                              >
                                {sec.code}
                              </span>
                            </div>
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.25rem 0 0 0' }}>
                              عدد الطلاب: <strong>{sec.students_count}</strong>
                            </p>
                          </div>

                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              paddingTop: '0.5rem',
                              borderTop: '1px solid var(--border-subtle)',
                            }}
                          >
                            <Badge variant={sec.is_active ? 'success' : 'neutral'} style={{ fontSize: '0.625rem' }}>
                              {sec.is_active ? 'نشطة' : 'معطلة'}
                            </Badge>

                            {!isReadOnly && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <button
                                  type="button"
                                  title="تعديل الشعبة"
                                  onClick={() => {
                                    setEditingSection(sec);
                                    setIsSectionModalOpen(true);
                                  }}
                                  style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--text-muted)',
                                    cursor: 'pointer',
                                    padding: '0.25rem',
                                  }}
                                >
                                  <Edit2 size={14} />
                                </button>
                                <button
                                  type="button"
                                  title="حذف الشعبة"
                                  onClick={() => {
                                    setDeletingItem({
                                      type: 'section',
                                      id: sec.id,
                                      name: sec.name,
                                    });
                                  }}
                                  style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--danger-500)',
                                    cursor: 'pointer',
                                    padding: '0.25rem',
                                  }}
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Curriculum & Subjects Workspace */}
              {activeTab === 'subjects' && (
                <div style={{ padding: '1.25rem' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '1rem',
                    }}
                  >
                    <div>
                      <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                        المناهج والمواد المخصصة لهذا الصف
                      </h3>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '0.125rem 0 0 0' }}>
                        المواد المقررة لهذا المستوى مع النصاب الأسبوعي لكل مادة
                      </p>
                    </div>

                    {!isReadOnly && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setEditingClassSubject(null);
                          setIsClassSubjectModalOpen(true);
                        }}
                        leftIcon={<Plus size={14} />}
                      >
                        إدراج مادة في المنهج
                      </Button>
                    )}
                  </div>

                  {isLoadingClassSubjects ? (
                    <div style={{ padding: '3rem', textAlign: 'center' }}>
                      <LoadingSpinner size={32} text="جاري تحميل مناهج الصف..." />
                    </div>
                  ) : classSubjects.length === 0 ? (
                    <EmptyState
                      title="لم يتم تخصيص مواد لهذا الصف بعد"
                      description="أدرج المواد الدراسية المقررة من قائمة مواد المدرسة وحدد نصاب الحصص الأسبوعي."
                      actionLabel={!isReadOnly ? 'إدراج مادة' : undefined}
                      onAction={() => {
                        setEditingClassSubject(null);
                        setIsClassSubjectModalOpen(true);
                      }}
                    />
                  ) : (
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right' }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                            <th style={{ padding: '0.75rem 1rem' }}>المادة الدراسية</th>
                            <th style={{ padding: '0.75rem 1rem' }}>الرمز</th>
                            <th style={{ padding: '0.75rem 1rem' }}>الحصص الأسبوعية</th>
                            {!isReadOnly && <th style={{ padding: '0.75rem 1rem', width: '80px' }}>الإجراءات</th>}
                          </tr>
                        </thead>
                        <tbody>
                          {classSubjects.map((cs) => (
                            <tr key={cs.id} style={{ borderBottom: '1px solid var(--border-subtle)', fontSize: '0.875rem' }}>
                              <td style={{ padding: '0.875rem 1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <BookOpen size={16} color="var(--primary-600)" />
                                  <span>{cs.subject_detail.name}</span>
                                </div>
                              </td>
                              <td style={{ padding: '0.875rem 1rem' }}>
                                <span
                                  style={{
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    padding: '0.125rem 0.375rem',
                                    borderRadius: 'var(--radius-sm)',
                                    backgroundColor: 'var(--neutral-100)',
                                    color: 'var(--text-secondary)',
                                  }}
                                >
                                  {cs.subject_detail.code}
                                </span>
                              </td>
                              <td style={{ padding: '0.875rem 1rem' }}>
                                <Badge variant="primary" icon={<Clock size={11} />}>
                                  {cs.weekly_periods} حصص / أسبوع
                                </Badge>
                              </td>
                              {!isReadOnly && (
                                <td style={{ padding: '0.875rem 1rem' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <button
                                      type="button"
                                      title="تعديل الحصص الأسبوعية"
                                      onClick={() => {
                                        setEditingClassSubject(cs);
                                        setIsClassSubjectModalOpen(true);
                                      }}
                                      style={{
                                        background: 'none',
                                        border: 'none',
                                        color: 'var(--text-muted)',
                                        cursor: 'pointer',
                                        padding: '0.25rem',
                                      }}
                                    >
                                      <Edit2 size={14} />
                                    </button>
                                    <button
                                      type="button"
                                      title="استبعاد المادة من المنهج"
                                      onClick={() => {
                                        setDeletingItem({
                                          type: 'class_subject',
                                          id: cs.id,
                                          name: cs.subject_detail.name,
                                        });
                                      }}
                                      style={{
                                        background: 'none',
                                        border: 'none',
                                        color: 'var(--danger-500)',
                                        cursor: 'pointer',
                                        padding: '0.25rem',
                                      }}
                                    >
                                      <Trash2 size={14} />
                                    </button>
                                  </div>
                                </td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ) : (
            <Card>
              <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
                <EmptyState
                  title="اختر صفاً دراسياً من القائمة"
                  description="حدد مستوى دراسياً لعرض وإدارة شعبه الدراسية ومنهج مواده المقررة."
                />
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Classroom Modal */}
      <ClassroomModal
        isOpen={isClassModalOpen}
        onClose={() => setIsClassModalOpen(false)}
        onSubmit={handleSaveClassroom}
        classroom={editingClassroom}
      />

      {/* Section Modal */}
      {selectedClassroom && (
        <SectionModal
          isOpen={isSectionModalOpen}
          onClose={() => setIsSectionModalOpen(false)}
          onSubmit={handleSaveSection}
          classroom={selectedClassroom}
          section={editingSection}
        />
      )}

      {/* ClassSubject Modal */}
      {selectedClassroom && (
        <ClassSubjectModal
          isOpen={isClassSubjectModalOpen}
          onClose={() => setIsClassSubjectModalOpen(false)}
          onSubmit={handleSaveClassSubject}
          classroom={selectedClassroom}
          availableSubjects={schoolSubjects}
          assignedSubjects={classSubjects}
          editingItem={editingClassSubject}
        />
      )}

      {/* Controlled Protected Delete Modal */}
      <ConfirmationModal
        isOpen={Boolean(deletingItem)}
        onClose={() => setDeletingItem(null)}
        onConfirm={handleConfirmDelete}
        isLoading={isDeleting}
        title={
          deletingItem?.type === 'classroom'
            ? 'تأكيد حذف الصف الدراسي'
            : deletingItem?.type === 'section'
            ? 'تأكيد حذف الشعبة الدراسية'
            : 'تأكيد استبعاد المادة من المنهج'
        }
        message={
          deletingItem?.type === 'classroom'
            ? `هل أنت متأكد من حذف الصف "${deletingItem?.name}"؟ سيتم التحقق من عدم وجود شُعب أو طلاب أو تكليفات مرتبطة به.`
            : deletingItem?.type === 'section'
            ? `هل أنت متأكد من حذف الشعبة "${deletingItem?.name}"؟ لا يمكن حذف شعبة مرتبطة بطلاب أو تكليفات.`
            : `هل أنت متأكد من استبعاد المادة "${deletingItem?.name}" من منهج هذا الصف؟`
        }
        confirmLabel="تأكيد الحذف"
        cancelLabel="إلغاء"
        variant="danger"
      />
    </div>
  );
};

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastContainer } from '../components/feedback/Toast';
import { ToastProvider } from '../context/ToastContext';
import { AuthContextType } from '../context/authContextDef';
import * as UseAuthModule from '../context/useAuth';
import { TeachersPage } from '../pages/TeachersPage';
import { academicService } from '../services/academicService';
import { ApiError } from '../services/apiClient';
import { teacherService } from '../services/teacherService';

vi.mock('../services/teacherService', () => ({ teacherService: {
  getTeachers: vi.fn(), getTeacher: vi.fn(), createTeacher: vi.fn(), updateTeacher: vi.fn(),
  getAssignments: vi.fn(), createAssignment: vi.fn(), updateAssignment: vi.fn(), deleteAssignment: vi.fn(),
} }));
vi.mock('../services/academicService', () => ({ academicService: {
  getAcademicYears: vi.fn(), getClassrooms: vi.fn(), getSections: vi.fn(), getSubjects: vi.fn(),
} }));

const auth = { user:{id:1,username:'admin',email:'',full_name:'Admin',role:'school_admin'}, activeMembership:{membership_id:1,school:{id:1,name:'School A'},role:'school_admin',academic_year:{id:11,name:'2026'},access_mode:'read_write',status:'active',is_default:true,is_current_school:true,can_write:true,start_date:'',end_date:'',last_used_at:null,unread_notifications_count:0,unread_conversations_count:0}, allMemberships:[],isLoading:false,isAuthenticated:true,isHistorical:false,isReadOnly:false,isSchoolAdmin:true,showContextModal:false,login:vi.fn(),logout:vi.fn(),switchContext:vi.fn(),refreshContexts:vi.fn(),setShowContextModal:vi.fn() } as AuthContextType;
const teacher = {id:4,school:{id:1,name:'School A'},academic_year:11,academic_year_detail:{id:11,name:'2026'},user_id:8,username:'noura',employee_code:'A-T0001',full_name:'نورة أحمد',phone:'0501',email:'noura@example.com',specialization:'رياضيات',qualification:'بكالوريوس',hire_date:'2025-09-01',address:'',photo:null,is_active:true,assignments_count:1,created_at:''};
const assignment = {id:7,school:{id:1,name:'School A'},academic_year:11,academic_year_detail:{id:11,name:'2026'},teacher:4,teacher_detail:{id:4,full_name:'نورة أحمد',employee_code:'A-T0001',specialization:'رياضيات'},classroom:21,classroom_detail:{id:21,name:'Grade 6',code:'G6'},section:31,section_detail:{id:31,name:'A',code:'A'},subject:41,subject_detail:{id:41,name:'Math',code:'MATH'},is_current:true,start_date:'2026-09-01',end_date:null,created_at:''};
const page = <T,>(results:T[])=>({count:results.length,next:null,previous:null,results});

function renderPage() {
  return render(<MemoryRouter><ToastProvider><TeachersPage/><ToastContainer/></ToastProvider></MemoryRouter>);
}

describe('TeachersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(UseAuthModule,'useAuth').mockReturnValue(auth);
    vi.mocked(teacherService.getTeachers).mockResolvedValue(page([teacher]));
    vi.mocked(teacherService.getTeacher).mockResolvedValue(teacher);
    vi.mocked(teacherService.getAssignments).mockResolvedValue(page([assignment]));
    vi.mocked(teacherService.createTeacher).mockResolvedValue(teacher);
    vi.mocked(teacherService.updateTeacher).mockResolvedValue(teacher);
    vi.mocked(teacherService.createAssignment).mockResolvedValue(assignment);
    vi.mocked(teacherService.updateAssignment).mockResolvedValue(assignment);
    vi.mocked(teacherService.deleteAssignment).mockResolvedValue(undefined);
    vi.mocked(academicService.getAcademicYears).mockResolvedValue(page([{id:11,school:{id:1,name:'School A'},name:'2026',start_date:'2026-09-01',end_date:'2027-06-30',is_active:true,created_at:''}]));
    vi.mocked(academicService.getClassrooms).mockResolvedValue(page([{id:21,school:{id:1,name:'School A'},academic_year:11,academic_year_detail:{id:11,name:'2026'},name:'Grade 6',code:'G6',is_active:true,sections_count:1,students_count:0,created_at:''}]));
    vi.mocked(academicService.getSections).mockResolvedValue(page([{id:31,school:{id:1,name:'School A'},academic_year:11,academic_year_detail:{id:11,name:'2026'},classroom:21,classroom_detail:{id:21,name:'Grade 6',code:'G6'},name:'A',code:'A',is_active:true,students_count:0,created_at:''}]));
    vi.mocked(academicService.getSubjects).mockResolvedValue(page([{id:41,school:{id:1,name:'School A'},name:'Math',code:'MATH',is_active:true}]));
  });

  it('lists, searches and filters teachers while showing profile and assignments', async () => {
    renderPage();
    expect(screen.getByText('إدارة المعلمين')).toBeInTheDocument();
    expect((await screen.findAllByText('نورة أحمد')).length).toBeGreaterThan(0);
    expect(screen.getByText('A-T0001')).toBeInTheDocument();
    expect(await screen.findByText(/Grade 6/)).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('بحث بالاسم أو الرقم...'), {target:{value:'نورة'}});
    await waitFor(()=>expect(teacherService.getTeachers).toHaveBeenLastCalledWith({search:'نورة',is_active:undefined}));
    fireEvent.change(screen.getByLabelText('تصفية حالة الملف'), {target:{value:'inactive'}});
    await waitFor(()=>expect(teacherService.getTeachers).toHaveBeenLastCalledWith({search:'نورة',is_active:false}));
  });

  it('creates a teacher with the optional account fields and edits profile state neutrally', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:'إضافة معلم'}));
    fireEvent.change(screen.getByLabelText('الاسم الكامل'),{target:{value:'نورة أحمد'}});
    fireEvent.change(screen.getByLabelText('اسم المستخدم الاختياري'),{target:{value:'noura'}});
    fireEvent.change(screen.getByLabelText('كلمة المرور الاختيارية'),{target:{value:'Secret123!'}});
    fireEvent.click(screen.getByRole('button',{name:'حفظ المعلم'}));
    await waitFor(()=>expect(teacherService.createTeacher).toHaveBeenCalledWith(expect.objectContaining({full_name:'نورة أحمد',account_username:'noura',account_password:'Secret123!'})));
    expect(screen.queryByText(/تعطيل تسجيل الدخول/)).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole('button',{name:'تعديل ملف المعلم'}));
    expect(screen.getByLabelText('ملف نشط')).toBeChecked();
  });

  it('creates and edits assignments with classroom-scoped sections and current-state controls', async () => {
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:'إضافة تكليف'}));
    await screen.findByRole('option',{name:'2026'});
    fireEvent.change(screen.getByLabelText('السنة الأكاديمية'),{target:{value:'11'}});
    await waitFor(()=>expect(academicService.getClassrooms).toHaveBeenLastCalledWith({academic_year_id:11,all_years:true}));
    await screen.findByRole('option',{name:'Grade 6'});
    fireEvent.change(screen.getByLabelText('الصف'),{target:{value:'21'}});
    await waitFor(()=>expect(academicService.getSections).toHaveBeenLastCalledWith({classroom_id:21,all_years:true}));
    fireEvent.change(screen.getByLabelText('الشعبة'),{target:{value:'31'}});
    fireEvent.change(screen.getByLabelText('المادة'),{target:{value:'41'}});
    fireEvent.click(screen.getByRole('button',{name:'حفظ التكليف'}));
    await waitFor(()=>expect(teacherService.createAssignment).toHaveBeenCalledWith(expect.objectContaining({teacher:4,classroom:21,section:31,subject:41,is_current:true})));
    fireEvent.click(await screen.findByRole('button',{name:'تعديل التكليف'}));
    await waitFor(()=>expect(screen.getByLabelText('الصف')).toHaveValue('21'));
    await waitFor(()=>expect(screen.getByLabelText('الشعبة')).toHaveValue('31'));
    await waitFor(()=>expect(screen.getByLabelText('المادة')).toHaveValue('41'));
    fireEvent.click(screen.getByLabelText('تكليف حالي'));
    fireEvent.click(screen.getByRole('button',{name:'حفظ التكليف'}));
    await waitFor(()=>expect(teacherService.updateAssignment).toHaveBeenCalledWith(7,expect.objectContaining({is_current:false})));
    expect(screen.queryByText(/حذف السجلات التشغيلية/)).not.toBeInTheDocument();
  });

  it('deletes an unused assignment and presents dependency-protection errors', async () => {
    vi.spyOn(window,'confirm').mockReturnValue(true);
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:'حذف التكليف'}));
    await waitFor(()=>expect(teacherService.deleteAssignment).toHaveBeenCalledWith(7));
    expect(screen.queryByText('Math')).not.toBeInTheDocument();
    vi.mocked(teacherService.getAssignments).mockResolvedValueOnce(page([assignment]));
    vi.mocked(teacherService.deleteAssignment).mockRejectedValueOnce(new ApiError(400,'Validation failed.',['Cannot delete assignment in use; mark it non-current instead.'] as unknown as Record<string,unknown>));
    renderPage();
    fireEvent.click(await screen.findByRole('button',{name:'حذف التكليف'}));
    expect(await screen.findByText('Cannot delete assignment in use; mark it non-current instead.')).toBeInTheDocument();
  });

  it('shows loading, empty and API-error states', async () => {
    let resolveTeachers:(value:ReturnType<typeof page<typeof teacher>>) => void = ()=>undefined;
    vi.mocked(teacherService.getTeachers).mockReturnValueOnce(new Promise(resolve=>{resolveTeachers=resolve;}));
    const first=renderPage();
    expect(screen.getByText('جاري التحميل...')).toBeInTheDocument();
    resolveTeachers(page([]));
    expect(await screen.findByText('لا يوجد معلمون')).toBeInTheDocument();
    first.unmount();
    vi.mocked(teacherService.getTeachers).mockRejectedValueOnce(new Error('Teacher load failed'));
    renderPage();
    expect(await screen.findByText('Teacher load failed')).toBeInTheDocument();
  });

  it('keeps historical context read-only and hides every mutation control', async () => {
    vi.spyOn(UseAuthModule,'useAuth').mockReturnValue({...auth,isReadOnly:true,isHistorical:true,activeMembership:{...auth.activeMembership!,status:'historical',access_mode:'read_only',can_write:false}});
    renderPage();
    expect(await screen.findByText('سياق تاريخي — للقراءة فقط')).toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'إضافة معلم'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'تعديل ملف المعلم'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'إضافة تكليف'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'تعديل التكليف'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'حذف التكليف'})).not.toBeInTheDocument();
  });
});

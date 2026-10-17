import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ToastContainer } from '../components/feedback/Toast';
import { ToastProvider } from '../context/ToastContext';
import { AuthContextType } from '../context/authContextDef';
import * as UseAuthModule from '../context/useAuth';
import { ParentsPage } from '../pages/ParentsPage';
import { parentService } from '../services/parentService';
import { studentService } from '../services/studentService';

vi.mock('../services/parentService', () => ({ parentService: {
  getParents: vi.fn(), createParent: vi.fn(), updateParent: vi.fn(),
  getGuardians: vi.fn(), createGuardian: vi.fn(), updateGuardian: vi.fn(), deleteGuardian: vi.fn(),
} }));
vi.mock('../services/studentService', () => ({ studentService: { getStudents: vi.fn() } }));

const auth = { user:{id:1,username:'admin',email:'',full_name:'Admin',role:'school_admin'}, activeMembership:{membership_id:1,school:{id:1,name:'School A'},role:'school_admin',academic_year:{id:11,name:'2026'},access_mode:'read_write',status:'active',is_default:true,is_current_school:true,can_write:true,start_date:'',end_date:'',last_used_at:null,unread_notifications_count:0,unread_conversations_count:0}, allMemberships:[],isLoading:false,isAuthenticated:true,isHistorical:false,isReadOnly:false,isSchoolAdmin:true,showContextModal:false,login:vi.fn(),logout:vi.fn(),switchContext:vi.fn(),refreshContexts:vi.fn(),setShowContextModal:vi.fn() } as AuthContextType;
const child = {id:10,student_code:'A-S00001',full_name:'ليان أحمد'};
const guardian = {id:30,parent_id:5,parent_name:'أحمد علي',relationship:'father' as const,is_primary:true,can_receive_notifications:true,can_receive_financial_alerts:true,created_at:''};
const parent = {id:5,parent_code:'A-P00001',full_name:'أحمد علي',national_id:'',phone:'0500',email:'a@example.com',address:'',occupation:'',workplace:'',is_active:true,created_at:'',username:'parent-a',can_edit_profile:true,children:[{...guardian,student:child}]};
const student = {id:10,student_code:'A-S00001',full_name:'ليان أحمد',gender:'female' as const,birth_date:null,is_active:true,created_at:'',school:{id:1,name:'School A'},current_enrollment:null,guardians:[]};
const page = <T,>(results:T[])=>({count:results.length,next:null,previous:null,results});

function renderPage(){return render(<MemoryRouter><ToastProvider><ParentsPage/><ToastContainer/></ToastProvider></MemoryRouter>);}

describe('ParentsPage',()=>{
  beforeEach(()=>{
    vi.clearAllMocks(); vi.spyOn(UseAuthModule,'useAuth').mockReturnValue(auth);
    vi.mocked(parentService.getParents).mockResolvedValue(page([parent]));
    vi.mocked(parentService.createParent).mockResolvedValue(parent);
    vi.mocked(parentService.updateParent).mockResolvedValue(parent);
    vi.mocked(parentService.getGuardians).mockResolvedValue(page([guardian]));
    vi.mocked(parentService.createGuardian).mockResolvedValue(guardian);
    vi.mocked(parentService.updateGuardian).mockResolvedValue(guardian);
    vi.mocked(parentService.deleteGuardian).mockResolvedValue(undefined);
    vi.mocked(studentService.getStudents).mockResolvedValue(page([student]));
  });

  it('lists searches and filters parents and shows only local children',async()=>{
    renderPage();
    expect((await screen.findAllByText('أحمد علي')).length).toBeGreaterThan(0);
    expect(screen.getByText('ليان أحمد')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('بحث بالاسم أو الرمز...'),{target:{value:'أحمد'}});
    await waitFor(()=>expect(parentService.getParents).toHaveBeenLastCalledWith({search:'أحمد',is_active:undefined}));
    fireEvent.change(screen.getByLabelText('تصفية حالة الملف'),{target:{value:'inactive'}});
    await waitFor(()=>expect(parentService.getParents).toHaveBeenLastCalledWith({search:'أحمد',is_active:false}));
  });

  it('creates a parent with optional account and initial guardian fields',async()=>{
    renderPage(); fireEvent.click(await screen.findByRole('button',{name:'إضافة ولي أمر'}));
    fireEvent.change(screen.getByLabelText('الاسم الكامل'),{target:{value:'أحمد علي'}});
    fireEvent.change(screen.getByLabelText('الطالب الأول'),{target:{value:'10'}});
    fireEvent.change(screen.getByLabelText('صلة القرابة'),{target:{value:'father'}});
    fireEvent.change(screen.getByLabelText('اسم المستخدم الاختياري'),{target:{value:'parent-a'}});
    fireEvent.change(screen.getByLabelText('كلمة المرور الاختيارية'),{target:{value:'SecurePass123!'}});
    fireEvent.click(screen.getByRole('button',{name:'حفظ ولي الأمر'}));
    await waitFor(()=>expect(parentService.createParent).toHaveBeenCalledWith(expect.objectContaining({full_name:'أحمد علي',student_id:10,relationship:'father',account_username:'parent-a',account_password:'SecurePass123!'})));
    expect(screen.queryByText(/البحث في مدارس أخرى/)).not.toBeInTheDocument();
  });

  it('respects profile ownership and manages local guardian relationships',async()=>{
    renderPage();
    expect(await screen.findByRole('button',{name:'تعديل ملف ولي الأمر'})).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'ربط طالب محلي'}));
    fireEvent.change(screen.getByLabelText('الطالب'),{target:{value:'10'}});
    fireEvent.change(screen.getByLabelText('صلة القرابة'),{target:{value:'guardian'}});
    fireEvent.click(screen.getByRole('button',{name:'حفظ العلاقة'}));
    await waitFor(()=>expect(parentService.createGuardian).toHaveBeenCalledWith(10,expect.objectContaining({parent_id:5,relationship:'guardian'})));
    fireEvent.click(await screen.findByRole('button',{name:'تعديل علاقة الوصاية'}));
    fireEvent.click(screen.getByLabelText('ولي الأمر الأساسي'));
    fireEvent.click(screen.getByRole('button',{name:'حفظ العلاقة'}));
    await waitFor(()=>expect(parentService.updateGuardian).toHaveBeenCalled());
  });

  it('confirms primary unlink and presents backend errors',async()=>{
    vi.spyOn(window,'confirm').mockReturnValue(true);
    vi.mocked(parentService.deleteGuardian).mockRejectedValueOnce(new Error('لا يمكن إزالة العلاقة'));
    renderPage(); fireEvent.click(await screen.findByRole('button',{name:'إلغاء ربط ولي الأمر الأساسي'}));
    expect(window.confirm).toHaveBeenCalledWith(expect.stringContaining('الأساسي'));
    expect(await screen.findByText('لا يمكن إزالة العلاقة')).toBeInTheDocument();
  });

  it('shows loading empty error and historical read-only states',async()=>{
    let resolveList:(value:ReturnType<typeof page<typeof parent>>)=>void=()=>undefined;
    vi.mocked(parentService.getParents).mockReturnValueOnce(new Promise(resolve=>{resolveList=resolve;}));
    const first=renderPage(); expect(screen.getByText('جاري التحميل...')).toBeInTheDocument();
    resolveList(page([])); expect(await screen.findByText('لا يوجد أولياء أمور')).toBeInTheDocument(); first.unmount();
    vi.mocked(parentService.getParents).mockRejectedValueOnce(new Error('Parent load failed'));
    const second=renderPage(); expect(await screen.findByText('Parent load failed')).toBeInTheDocument(); second.unmount();
    vi.spyOn(UseAuthModule,'useAuth').mockReturnValue({...auth,isReadOnly:true,isHistorical:true,activeMembership:{...auth.activeMembership!,status:'historical',access_mode:'read_only',can_write:false}});
    renderPage(); expect(await screen.findByText('سياق تاريخي — للقراءة فقط')).toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'إضافة ولي أمر'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'تعديل ملف ولي الأمر'})).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'ربط طالب محلي'})).not.toBeInTheDocument();
  });
});

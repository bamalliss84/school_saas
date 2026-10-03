import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StudentsPage } from '../pages/StudentsPage';
import { ToastProvider } from '../context/ToastContext';
import * as UseAuthModule from '../context/useAuth';
import { studentService } from '../services/studentService';
import { academicService } from '../services/academicService';
import { AuthContextType } from '../context/authContextDef';

vi.mock('../services/studentService', () => ({ studentService: {
  getStudents: vi.fn(), getStudent: vi.fn(), getHistory: vi.fn(),
  createStudent: vi.fn(), updateStudent: vi.fn(), createEnrollment: vi.fn(), updateEnrollment: vi.fn(),
} }));
vi.mock('../services/academicService', () => ({ academicService: {
  getAcademicYears: vi.fn(), getClassrooms: vi.fn(), getSections: vi.fn(),
} }));

const auth = { user:{id:1,username:'admin',email:'',full_name:'Admin',role:'school_admin'}, activeMembership:{membership_id:1,school:{id:1,name:'A'},role:'school_admin',academic_year:{id:1,name:'2026'},access_mode:'read_write',status:'active',is_default:true,is_current_school:true,can_write:true,start_date:'',end_date:'',last_used_at:null,unread_notifications_count:0,unread_conversations_count:0}, allMemberships:[],isLoading:false,isAuthenticated:true,isHistorical:false,isReadOnly:false,isSchoolAdmin:true,showContextModal:false,login:vi.fn(),logout:vi.fn(),switchContext:vi.fn(),refreshContexts:vi.fn(),setShowContextModal:vi.fn() } as AuthContextType;
const enrollment = { id:10, school:{id:1,name:'A'}, academic_year:{id:1,name:'2026'}, classroom:{id:2,name:'Grade 1',code:'G1'}, section:{id:3,name:'A',code:'A'}, status:'active' as const, is_current:true, start_date:'2026-09-01', end_date:null, created_at:'' };
const student = { id:5,student_code:'A-S00001',full_name:'أحمد علي',gender:'male' as const,birth_date:'2015-01-01',is_active:true,created_at:'',school:{id:1,name:'A'},current_enrollment:enrollment,guardians:[] };

describe('StudentsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks(); vi.spyOn(UseAuthModule,'useAuth').mockReturnValue(auth);
    vi.mocked(studentService.getStudents).mockResolvedValue({count:1,next:null,previous:null,results:[student]});
    vi.mocked(studentService.getStudent).mockResolvedValue(student);
    vi.mocked(studentService.getHistory).mockResolvedValue({count:1,next:null,previous:null,results:[enrollment]});
    vi.mocked(academicService.getAcademicYears).mockResolvedValue({count:0,next:null,previous:null,results:[]});
    vi.mocked(academicService.getClassrooms).mockResolvedValue({count:0,next:null,previous:null,results:[]});
    vi.mocked(academicService.getSections).mockResolvedValue({count:0,next:null,previous:null,results:[]});
  });
  it('lists students and displays selected profile with enrollment history', async () => {
    render(<MemoryRouter><ToastProvider><StudentsPage /></ToastProvider></MemoryRouter>);
    expect(screen.getByText('إدارة الطلاب')).toBeInTheDocument();
    await waitFor(()=>expect(screen.getAllByText('أحمد علي').length).toBeGreaterThan(0));
    expect((await screen.findAllByText('A-S00001')).length).toBeGreaterThan(0);
    expect((await screen.findAllByText(/Grade 1/)).length).toBeGreaterThan(0);
  });
  it('offers student and enrollment actions in writable context', async () => {
    render(<MemoryRouter><ToastProvider><StudentsPage /></ToastProvider></MemoryRouter>);
    expect(await screen.findByText('إضافة طالب')).toBeInTheDocument();
    expect(await screen.findByText('إضافة تسجيل')).toBeInTheDocument();
  });
  it('hides write actions in historical context', async () => {
    vi.spyOn(UseAuthModule,'useAuth').mockReturnValue({...auth,isReadOnly:true,isHistorical:true,activeMembership:{...auth.activeMembership!,status:'historical',access_mode:'read_only',can_write:false}});
    render(<MemoryRouter><ToastProvider><StudentsPage /></ToastProvider></MemoryRouter>);
    await waitFor(()=>expect(screen.getAllByText('أحمد علي').length).toBeGreaterThan(0));
    expect(screen.queryByText('إضافة طالب')).not.toBeInTheDocument();
    expect(screen.queryByText('إضافة تسجيل')).not.toBeInTheDocument();
  });
});

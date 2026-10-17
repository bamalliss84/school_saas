import React, { useEffect, useMemo, useState } from 'react';
import { apiClient } from '../services/apiClient';
import { academicService } from '../services/academicService';
import { useAuth } from '../context/useAuth';
import { useToast } from '../context/useToast';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingSpinner } from '../components/feedback/LoadingSpinner';

type Module = 'timetable'|'attendance'|'homework'|'messages'|'announcements'|'onboarding'|'data'|'reports'|'settings';
const labels:Record<Module,string>={timetable:'الجدول المدرسي',attendance:'الحضور والغياب',homework:'الواجبات',messages:'الرسائل والمحادثات',announcements:'الإعلانات والإشعارات',onboarding:'تهيئة المدرسة',data:'الاستيراد والتصدير',reports:'التقارير',settings:'إعدادات المدرسة'};
const box:React.CSSProperties={padding:'1rem',border:'1px solid var(--border-subtle)',borderRadius:'var(--radius-md)',background:'var(--neutral-50)'};

export const OperationsPage:React.FC<{module:Module}>=({module})=>{
 const {isReadOnly}=useAuth(); const toast=useToast();
 const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [data,setData]=useState<any>(null);
 const [classes,setClasses]=useState<any[]>([]); const [sections,setSections]=useState<any[]>([]);
 const [classId,setClassId]=useState<number|undefined>(); const [sectionId,setSectionId]=useState<number|undefined>();
 const [date,setDate]=useState(new Date().toISOString().slice(0,10)); const [draft,setDraft]=useState<any>({});
 const load=async()=>{
  setLoading(true);setError('');
  try{
   if(module==='timetable'){const c=await academicService.getClassrooms();setClasses(c.results);if(c.results[0])setClassId(v=>v||c.results[0].id);setData(await apiClient.get('/timetable/config/'))}
   else if(module==='attendance') setData(await apiClient.get('/attendance/',{params:{attendance_date:date}}));
   else if(module==='homework') setData(await apiClient.get('/homework/'));
   else if(module==='messages') setData(await apiClient.get('/conversations/'));
   else if(module==='announcements') setData(await apiClient.get('/announcements/'));
   else if(module==='onboarding') setData(await apiClient.get('/admin/onboarding/status/'));
   else if(module==='reports') setData(await apiClient.get('/admin/reports/summary/'));
   else if(module==='settings') setData(await apiClient.get('/admin/settings/'));
   else setData(await apiClient.get('/admin/data/export/',{params:{kind:'students'}}));
  }catch(e:any){setError(e?.message||'تعذر تحميل البيانات');}finally{setLoading(false)}
 };
 useEffect(()=>{load()},[module,date]);
 useEffect(()=>{if(classId)academicService.getSections({classroom_id:classId}).then(r=>{setSections(r.results);setSectionId(r.results[0]?.id)})},[classId]);
 useEffect(()=>{if(module==='timetable'&&classId&&sectionId){setLoading(true);apiClient.get('/timetable/grid/',{params:{classroom_id:classId,section_id:sectionId}}).then(setData).catch((e:any)=>setError(e.message)).finally(()=>setLoading(false))}},[module,classId,sectionId]);
 const rows=useMemo(()=>Array.isArray(data)?data:(data?.results||data?.rows||[]),[data]);
 const saveSettings=async()=>{try{setData(await apiClient.patch('/admin/settings/',draft));toast.success('تم حفظ الإعدادات')}catch(e:any){toast.error(e.message)}};
 const importRows=async()=>{try{const rows=JSON.parse(draft.rows||'[]');await apiClient.post('/admin/data/import/',{kind:draft.kind||'students',rows});toast.success('تم الاستيراد بنجاح');load()}catch(e:any){toast.error(e.message||'بيانات الاستيراد غير صالحة')}};
 return <div style={{display:'flex',flexDirection:'column',gap:'1rem'}}>
  <div><h1 style={{margin:0,fontSize:'1.5rem'}}>{labels[module]}</h1><p style={{color:'var(--text-secondary)'}}>إدارة {labels[module]} ضمن المدرسة والسنة الدراسية النشطة{isReadOnly?' — وضع القراءة التاريخية':''}</p></div>
  {(module==='timetable'||module==='attendance')&&<Card><div style={{padding:'1rem',display:'flex',gap:'.75rem',flexWrap:'wrap'}}>
   {module==='timetable'&&<><select value={classId||''} onChange={e=>setClassId(Number(e.target.value))}>{classes.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select><select value={sectionId||''} onChange={e=>setSectionId(Number(e.target.value))}>{sections.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></>}
   {module==='attendance'&&<input type="date" value={date} onChange={e=>setDate(e.target.value)}/>}<Button variant="outline" size="sm" onClick={load}>تحديث</Button>
  </div></Card>}
  {loading?<LoadingSpinner text="جاري التحميل..."/>:error?<Card><div style={{padding:'2rem',color:'var(--danger-600)'}}>{error}<div><Button variant="outline" size="sm" onClick={load}>إعادة المحاولة</Button></div></div></Card>:
   module==='onboarding'?<Card><div style={{padding:'1.25rem'}}><h3>جاهزية المدرسة: {data?.progress||0}%</h3><div style={{display:'grid',gap:'.5rem'}}>{data?.steps?.map((s:any)=><div key={s.key} style={box}>{s.complete?'✓':'○'} {s.label}</div>)}</div></div></Card>:
   module==='reports'?<div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(190px,1fr))',gap:'1rem'}}>{Object.entries(data||{}).map(([k,v]:any)=><Card key={k}><div style={{padding:'1rem'}}><strong>{k}</strong>{Object.entries(v||{}).map(([a,b]:any)=><div key={a}>{a}: {String(b)}</div>)}</div></Card>)}</div>:
   module==='settings'?<Card><div style={{padding:'1.25rem',display:'grid',gap:'.75rem',maxWidth:600}}>{['name','phone','email','address'].map(k=><input key={k} placeholder={k} defaultValue={data?.school?.[k]||''} onChange={e=>setDraft((d:any)=>({...d,[k]:e.target.value}))}/>)}{['school_name_ar','school_name_en','primary_color','timezone'].map(k=><input key={k} placeholder={k} defaultValue={data?.settings?.[k]||''} onChange={e=>setDraft((d:any)=>({...d,[k]:e.target.value}))}/>) }{!isReadOnly&&<Button onClick={saveSettings}>حفظ الإعدادات</Button>}</div></Card>:
   module==='data'?<><Card><div style={{padding:'1rem',display:'grid',gap:'.75rem'}}><select onChange={e=>setDraft((d:any)=>({...d,kind:e.target.value}))}><option value="students">الطلاب</option><option value="teachers">المعلمون</option></select><textarea rows={7} placeholder='ألصق JSON array بعد المعاينة' onChange={e=>setDraft((d:any)=>({...d,rows:e.target.value}))}/>{!isReadOnly&&<Button onClick={importRows}>تحقق واستيراد</Button>}</div></Card><Card><pre style={{padding:'1rem',overflow:'auto',direction:'ltr'}}>{JSON.stringify(data,null,2)}</pre></Card></>:
   module==='timetable'?<Card><div style={{padding:'1rem',overflowX:'auto'}}>{!data?.entries?.length?<EmptyState title="لا توجد حصص" description="أضف الفترات وتكليفات المعلمين ثم كوّن الجدول."/>:<table style={{width:'100%'}}><thead><tr><th>اليوم</th><th>الفترة</th><th>المادة</th><th>المعلم</th></tr></thead><tbody>{data.entries.map((x:any)=><tr key={x.id}><td>{x.weekday}</td><td>{x.period_name||x.period}</td><td>{x.subject_name||x.subject}</td><td>{x.teacher_name||x.teacher}</td></tr>)}</tbody></table>}</div></Card>:
   <Card><div style={{padding:'1rem',overflowX:'auto'}}>{rows.length===0?<EmptyState title="لا توجد بيانات" description={'لا توجد سجلات في '+labels[module]}/>:<pre style={{direction:'ltr',textAlign:'left',whiteSpace:'pre-wrap'}}>{JSON.stringify(rows,null,2)}</pre>}</div></Card>}
 </div>
};

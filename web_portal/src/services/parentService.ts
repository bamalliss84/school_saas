import { apiClient } from './apiClient';
import { PaginatedResponse } from '../types/api';
import { Guardian, GuardianInput, ParentInput, ParentProfile } from '../types/parents';

export const parentService={
  getParents:(params?:{search?:string;is_active?:boolean})=>apiClient.get<PaginatedResponse<ParentProfile>>('/parents/',{params}),
  getParent:(id:number)=>apiClient.get<ParentProfile>(`/parents/${id}/`),
  createParent:(data:ParentInput)=>apiClient.post<ParentProfile>('/parents/',data),
  updateParent:(id:number,data:Partial<ParentInput>)=>apiClient.patch<ParentProfile>(`/parents/${id}/`,data),
  getGuardians:(studentId:number)=>apiClient.get<PaginatedResponse<Guardian>>(`/students/${studentId}/guardians/`),
  createGuardian:(studentId:number,data:GuardianInput)=>apiClient.post<Guardian>(`/students/${studentId}/guardians/`,data),
  updateGuardian:(studentId:number,id:number,data:Partial<GuardianInput>)=>apiClient.patch<Guardian>(`/students/${studentId}/guardians/${id}/`,data),
  deleteGuardian:(studentId:number,id:number)=>apiClient.delete<void>(`/students/${studentId}/guardians/${id}/`),
};

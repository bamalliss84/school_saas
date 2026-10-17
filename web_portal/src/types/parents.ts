import { PaginatedResponse } from './api';

export type GuardianRelationship='father'|'mother'|'brother'|'sister'|'guardian'|'other';
export interface ChildBrief{id:number;student_code:string;full_name:string}
export interface Guardian{id:number;parent_id:number;parent_name:string;relationship:GuardianRelationship;is_primary:boolean;can_receive_notifications:boolean;can_receive_financial_alerts:boolean;created_at:string}
export interface ParentChild extends Omit<Guardian,'parent_name'>{student:ChildBrief}
export interface ParentProfile{id:number;parent_code:string;full_name:string;national_id:string|null;phone:string|null;email:string|null;address:string|null;occupation:string|null;workplace:string|null;is_active:boolean;created_at:string;username:string;children:ParentChild[];can_edit_profile:boolean}
export interface ParentInput{full_name:string;national_id?:string;phone?:string;email?:string;address?:string;occupation?:string;workplace?:string;is_active?:boolean;account_username?:string;account_password?:string;student_id:number;relationship:GuardianRelationship;is_primary?:boolean;can_receive_notifications?:boolean;can_receive_financial_alerts?:boolean}
export interface GuardianInput{parent_id?:number;relationship:GuardianRelationship;is_primary?:boolean;can_receive_notifications?:boolean;can_receive_financial_alerts?:boolean}
export type ParentPage=PaginatedResponse<ParentProfile>;

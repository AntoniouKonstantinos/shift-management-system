import { AccessLevel } from './auth.model';

export interface Employee {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  role: string;
  hire_date: string;
  is_active: boolean;
  has_account: boolean;
  access_level: AccessLevel | null;
}

export interface EmployeeCreate {
  full_name: string;
  email: string;
  phone?: string | null;
  role_id: number;
  password?: string;
  access_level?: AccessLevel;
}

export interface EmployeeUpdate {
  full_name?: string;
  email?: string;
  phone?: string | null;
  role_id?: number;
  is_active?: boolean;
  password?: string;
  access_level?: AccessLevel;
}

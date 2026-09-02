export interface Employee {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  role: string;
  hire_date: string;
  is_active: boolean;
}

export interface EmployeeCreate {
  full_name: string;
  email: string;
  phone?: string | null;
  role_id: number;
}

export interface EmployeeUpdate {
  full_name?: string;
  email?: string;
  phone?: string | null;
  role_id?: number;
  is_active?: boolean;
}

export interface Shift {
  id: number;
  department: string;
  shift_date: string;
  start_time: string;
  end_time: string;
  required_staff: number;
  assigned_count: number;
  notes: string | null;
  assignments?: ShiftAssignmentDetail[];
}

export interface ShiftAssignmentDetail {
  id: number;
  employee: string;
  status: string;
}

export interface ShiftCreate {
  department_id: number;
  shift_date: string;
  start_time: string;
  end_time: string;
  required_staff?: number;
  notes?: string | null;
}

export interface ShiftUpdate {
  department_id?: number;
  shift_date?: string;
  start_time?: string;
  end_time?: string;
  required_staff?: number;
  notes?: string | null;
}

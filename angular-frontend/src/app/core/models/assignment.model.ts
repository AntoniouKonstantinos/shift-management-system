export interface Assignment {
  id: number;
  employee_id: number;
  employee_name: string;
  shift_id: number;
  status: string;
  check_in: string | null;
  check_out: string | null;
}

export interface AssignCandidate {
  id: number;
  full_name: string;
  role: string;
}

export interface AssignPayload {
  employee_id: number;
  force?: boolean;
}

export interface AssignmentStatusUpdate {
  status: 'assigned' | 'confirmed' | 'completed' | 'no_show';
}

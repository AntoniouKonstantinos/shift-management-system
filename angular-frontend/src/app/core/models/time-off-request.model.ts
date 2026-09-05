export interface TimeOffRequest {
  id: number;
  employee_id: number;
  employee_name: string;
  start_date: string;
  end_date: string;
  reason: string | null;
  status: 'pending' | 'approved' | 'rejected';
}

export interface TimeOffRequestCreate {
  employee_id: number;
  start_date: string;
  end_date: string;
  reason?: string | null;
}

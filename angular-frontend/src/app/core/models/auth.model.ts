export type AccessLevel = 'manager' | 'employee';

export interface AuthUser {
  employee_id: number;
  full_name: string;
  email: string;
  role: string;
  access_level: AccessLevel;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: AuthUser;
}

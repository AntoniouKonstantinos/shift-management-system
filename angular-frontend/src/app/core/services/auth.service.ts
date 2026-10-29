import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, tap } from 'rxjs';
import {
  AuthUser,
  ChangePasswordRequest,
  LoginResponse,
  MessageResponse,
} from '../models/auth.model';

const TOKEN_KEY = 'access_token';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly baseUrl = '/api/auth';

  readonly currentUser = signal<AuthUser | null>(null);
  readonly isLoggedIn = computed(() => this.currentUser() !== null);
  readonly isManager = computed(() => this.currentUser()?.access_level === 'manager');

  constructor(
    private http: HttpClient,
    private router: Router,
  ) {}

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  login(email: string, password: string): Observable<AuthUser> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login`, { email, password }).pipe(
      tap((response) => {
        localStorage.setItem(TOKEN_KEY, response.access_token);
        this.currentUser.set(response.user);
      }),
      map((response) => response.user),
    );
  }

  changePassword(currentPassword: string, newPassword: string): Observable<MessageResponse> {
    const payload: ChangePasswordRequest = {
      current_password: currentPassword,
      new_password: newPassword,
    };
    return this.http.post<MessageResponse>(`${this.baseUrl}/change-password`, payload);
  }

  restoreSession(): Observable<AuthUser | null> {
    if (!this.getToken()) {
      return of(null);
    }

    return this.http.get<AuthUser>(`${this.baseUrl}/me`).pipe(
      tap((user) => this.currentUser.set(user)),
      catchError(() => {
        this.clearSession();
        return of(null);
      }),
    );
  }

  logout(): void {
    this.clearSession();
    this.router.navigateByUrl('/login');
  }

  private clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    this.currentUser.set(null);
  }
}

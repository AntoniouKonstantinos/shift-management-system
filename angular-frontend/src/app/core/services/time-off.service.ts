import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TimeOffRequest, TimeOffRequestCreate } from '../models/time-off-request.model';

@Injectable({
  providedIn: 'root',
})
export class TimeOffService {
  private readonly baseUrl = '/api/time-off';

  constructor(private http: HttpClient) {}

  list(employeeId?: number, status?: string): Observable<TimeOffRequest[]> {
    let params = new HttpParams();
    if (employeeId) params = params.set('employee_id', employeeId);
    if (status) params = params.set('status', status);

    return this.http.get<TimeOffRequest[]>(this.baseUrl, { params });
  }

  create(payload: TimeOffRequestCreate): Observable<TimeOffRequest> {
    return this.http.post<TimeOffRequest>(this.baseUrl, payload);
  }

  approve(id: number): Observable<TimeOffRequest> {
    return this.http.patch<TimeOffRequest>(`${this.baseUrl}/${id}/approve`, {});
  }

  reject(id: number): Observable<TimeOffRequest> {
    return this.http.patch<TimeOffRequest>(`${this.baseUrl}/${id}/reject`, {});
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}

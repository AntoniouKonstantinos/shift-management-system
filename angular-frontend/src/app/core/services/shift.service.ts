import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Shift, ShiftCreate, ShiftUpdate } from '../models/shift.model';

@Injectable({
  providedIn: 'root',
})
export class ShiftService {
  private readonly baseUrl = '/api/shifts';

  constructor(private http: HttpClient) {}

  list(dateFrom?: string, dateTo?: string, departmentId?: number): Observable<Shift[]> {
    let params = new HttpParams();
    if (dateFrom) params = params.set('date_from', dateFrom);
    if (dateTo) params = params.set('date_to', dateTo);
    if (departmentId) params = params.set('department_id', departmentId);

    return this.http.get<Shift[]>(this.baseUrl, { params });
  }

  get(id: number): Observable<Shift> {
    return this.http.get<Shift>(`${this.baseUrl}/${id}`);
  }

  create(payload: ShiftCreate): Observable<Shift> {
    return this.http.post<Shift>(this.baseUrl, payload);
  }

  update(id: number, payload: ShiftUpdate): Observable<Shift> {
    return this.http.put<Shift>(`${this.baseUrl}/${id}`, payload);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}

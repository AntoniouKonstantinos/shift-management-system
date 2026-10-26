import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Availability, AvailabilityCreate, AvailabilityUpdate } from '../models/availability.model';

@Injectable({
  providedIn: 'root',
})
export class AvailabilityService {
  constructor(private http: HttpClient) {}

  private url(employeeId: number): string {
    return `/api/employees/${employeeId}/availability`;
  }

  list(employeeId: number): Observable<Availability[]> {
    return this.http.get<Availability[]>(this.url(employeeId));
  }

  create(employeeId: number, payload: AvailabilityCreate): Observable<Availability> {
    return this.http.post<Availability>(this.url(employeeId), payload);
  }

  update(
    employeeId: number,
    slotId: number,
    payload: AvailabilityUpdate,
  ): Observable<Availability> {
    return this.http.put<Availability>(`${this.url(employeeId)}/${slotId}`, payload);
  }

  delete(employeeId: number, slotId: number): Observable<void> {
    return this.http.delete<void>(`${this.url(employeeId)}/${slotId}`);
  }
}

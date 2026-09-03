import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Assignment,
  AssignCandidate,
  AssignPayload,
  AssignmentStatusUpdate,
} from '../models/assignment.model';

@Injectable({
  providedIn: 'root',
})
export class AssignmentService {
  private readonly baseUrl = '/api';

  constructor(private http: HttpClient) {}

  getCandidates(shiftId: number): Observable<AssignCandidate[]> {
    return this.http.get<AssignCandidate[]>(`${this.baseUrl}/shifts/${shiftId}/candidates`);
  }

  assign(shiftId: number, payload: AssignPayload): Observable<Assignment> {
    return this.http.post<Assignment>(`${this.baseUrl}/shifts/${shiftId}/assign`, payload);
  }

  updateStatus(assignmentId: number, payload: AssignmentStatusUpdate): Observable<Assignment> {
    return this.http.patch<Assignment>(`${this.baseUrl}/assignments/${assignmentId}`, payload);
  }

  checkIn(assignmentId: number): Observable<Assignment> {
    return this.http.patch<Assignment>(`${this.baseUrl}/assignments/${assignmentId}/check-in`, {});
  }

  remove(assignmentId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/assignments/${assignmentId}`);
  }
}

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Department } from '../models/department.model';

@Injectable({
  providedIn: 'root',
})
export class DepartmentService {
  private readonly baseUrl = '/api/departments';

  constructor(private http: HttpClient) {}

  list(): Observable<Department[]> {
    return this.http.get<Department[]>(this.baseUrl);
  }
}

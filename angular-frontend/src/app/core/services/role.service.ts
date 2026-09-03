import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Role } from '../models/role.model';

@Injectable({
  providedIn: 'root',
})
export class RoleService {
  private readonly baseUrl = '/api/roles';

  constructor(private http: HttpClient) {}

  list(): Observable<Role[]> {
    return this.http.get<Role[]>(this.baseUrl);
  }
}

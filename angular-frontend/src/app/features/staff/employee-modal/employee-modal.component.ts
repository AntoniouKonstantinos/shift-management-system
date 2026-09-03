import {
  Component,
  EventEmitter,
  Input,
  Output,
  OnInit,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Employee, EmployeeCreate, EmployeeUpdate } from '../../../core/models/employee.model';
import { Role } from '../../../core/models/role.model';
import { RoleService } from '../../../core/services/role.service';
import { EmployeeService } from '../../../core/services/employee.service';

@Component({
  selector: 'app-employee-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './employee-modal.component.html',
  styleUrl: './employee-modal.component.css',
})
export class EmployeeModalComponent implements OnInit, OnChanges {
  @Input() employee: Employee | null = null;
  @Output() close = new EventEmitter<void>();
  @Output() saved = new EventEmitter<void>();

  roles: Role[] = [];

  fullName = '';
  email = '';
  phone = '';
  roleId: number | null = null;

  constructor(
    private roleService: RoleService,
    private employeeService: EmployeeService,
  ) {}

  ngOnInit(): void {
    this.roleService.list().subscribe({
      next: (data: Role[]) => (this.roles = data),
      error: (err: any) => console.error(err),
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['employee']) {
      this.resetForm();
    }
  }

  private resetForm(): void {
    if (this.employee) {
      this.fullName = this.employee.full_name;
      this.email = this.employee.email;
      this.phone = this.employee.phone ?? '';
      const matchedRole = this.roles.find((r) => r.name === this.employee!.role);
      this.roleId = matchedRole ? matchedRole.id : null;
    } else {
      this.fullName = '';
      this.email = '';
      this.phone = '';
      this.roleId = null;
    }
  }

  onSubmit(): void {
    if (!this.roleId) {
      alert('Please select a role.');
      return;
    }

    if (this.employee) {
      const payload: EmployeeUpdate = {
        full_name: this.fullName,
        email: this.email,
        phone: this.phone || null,
        role_id: this.roleId,
      };
      this.employeeService.update(this.employee.id, payload).subscribe({
        next: () => this.saved.emit(),
        error: (err) => alert(err.error?.error ?? 'Failed to update employee.'),
      });
    } else {
      const payload: EmployeeCreate = {
        full_name: this.fullName,
        email: this.email,
        phone: this.phone || null,
        role_id: this.roleId,
      };
      this.employeeService.create(payload).subscribe({
        next: () => this.saved.emit(),
        error: (err) => alert(err.error?.error ?? 'Failed to create employee.'),
      });
    }
  }

  onCancel(): void {
    this.close.emit();
  }
}

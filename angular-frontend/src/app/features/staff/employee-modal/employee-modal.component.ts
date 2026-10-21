import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AccessLevel } from '../../../core/models/auth.model';
import { Employee, EmployeeCreate, EmployeeUpdate } from '../../../core/models/employee.model';
import { Role } from '../../../core/models/role.model';
import { RoleService } from '../../../core/services/role.service';
import { EmployeeService } from '../../../core/services/employee.service';

const MIN_PASSWORD_LENGTH = 8;

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

  roles = signal<Role[]>([]);

  fullName = signal<string>('');
  email = signal<string>('');
  phone = signal<string>('');
  roleId = signal<number | null>(null);
  password = signal<string>('');
  accessLevel = signal<AccessLevel>('employee');

  constructor(
    private roleService: RoleService,
    private employeeService: EmployeeService,
  ) {}

  get hasAccount(): boolean {
    return !!this.employee?.has_account;
  }

  ngOnInit(): void {
    this.roleService.list().subscribe({
      next: (data) => {
        this.roles.set(data);
        this.matchRole();
      },
      error: (err) => console.error(err),
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['employee']) {
      this.resetForm();
    }
  }

  private resetForm(): void {
    this.password.set('');
    this.roleId.set(null);

    if (this.employee) {
      this.fullName.set(this.employee.full_name);
      this.email.set(this.employee.email);
      this.phone.set(this.employee.phone ?? '');
      this.accessLevel.set(this.employee.access_level ?? 'employee');
      this.matchRole();
    } else {
      this.fullName.set('');
      this.email.set('');
      this.phone.set('');
      this.accessLevel.set('employee');
    }
  }

  private matchRole(): void {
    if (!this.employee || this.roleId() !== null) {
      return;
    }
    const match = this.roles().find((r) => r.name === this.employee!.role);
    if (match) {
      this.roleId.set(match.id);
    }
  }

  onSubmit(): void {
    const roleId = this.roleId();
    if (!roleId) {
      alert('Please select a role.');
      return;
    }

    const password = this.password();
    if (password && password.length < MIN_PASSWORD_LENGTH) {
      alert(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }

    const includeAccessLevel = this.hasAccount || !!password;
    const accountFields = {
      ...(password ? { password } : {}),
      ...(includeAccessLevel ? { access_level: this.accessLevel() } : {}),
    };

    if (this.employee) {
      const payload: EmployeeUpdate = {
        full_name: this.fullName(),
        email: this.email(),
        phone: this.phone() || null,
        role_id: roleId,
        ...accountFields,
      };
      this.employeeService.update(this.employee.id, payload).subscribe({
        next: () => this.saved.emit(),
        error: (err) => alert(err.error?.error ?? 'Failed to update employee.'),
      });
    } else {
      const payload: EmployeeCreate = {
        full_name: this.fullName(),
        email: this.email(),
        phone: this.phone() || null,
        role_id: roleId,
        ...accountFields,
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

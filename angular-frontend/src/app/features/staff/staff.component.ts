import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Employee } from '../../core/models/employee.model';
import { EmployeeService } from '../../core/services/employee.service';
import { ConfirmService } from '../../core/services/confirm.service';
import { ToastService } from '../../core/services/toast.service';
import { EmployeeModalComponent } from './employee-modal/employee-modal.component';

@Component({
  selector: 'app-staff',
  standalone: true,
  imports: [CommonModule, EmployeeModalComponent],
  templateUrl: './staff.component.html',
  styleUrl: './staff.component.css',
})
export class StaffComponent implements OnInit {
  employees = signal<Employee[]>([]);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  showModal = signal<boolean>(false);
  editingEmployee = signal<Employee | null>(null);

  constructor(
    private employeeService: EmployeeService,
    private confirmService: ConfirmService,
    private toast: ToastService,
  ) {}

  ngOnInit(): void {
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.loading.set(true);
    this.employeeService.list().subscribe({
      next: (data) => {
        this.employees.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to load employees.');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  async deleteEmployee(employee: Employee): Promise<void> {
    const confirmed = await this.confirmService.confirm({
      title: 'Delete employee',
      message:
        `Delete ${employee.full_name}? Their availability, time-off requests ` +
        'and shift assignments will be deleted too.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!confirmed) {
      return;
    }

    this.employeeService.delete(employee.id).subscribe({
      next: () => {
        this.toast.success(`${employee.full_name} was deleted.`);
        this.loadEmployees();
      },
      error: (err) => this.toast.error(err.error?.error ?? 'Failed to delete the employee.'),
    });
  }

  openCreateModal(): void {
    this.editingEmployee.set(null);
    this.showModal.set(true);
  }

  openEditModal(employee: Employee): void {
    this.editingEmployee.set(employee);
    this.showModal.set(true);
  }

  onModalClose(): void {
    this.showModal.set(false);
  }

  onModalSaved(): void {
    const wasEditing = this.editingEmployee() !== null;
    this.showModal.set(false);
    this.toast.success(wasEditing ? 'Employee updated.' : 'Employee created.');
    this.loadEmployees();
  }
}

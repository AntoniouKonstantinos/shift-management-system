import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Employee } from '../../core/models/employee.model';
import { EmployeeService } from '../../core/services/employee.service';
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

  constructor(private employeeService: EmployeeService) {}

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

  deleteEmployee(id: number): void {
    if (!confirm('Are you sure you want to delete this employee?')) {
      return;
    }

    this.employeeService.delete(id).subscribe({
      next: () => this.loadEmployees(),
      error: (err) => {
        alert('Failed to delete employee.');
        console.error(err);
      },
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
    this.showModal.set(false);
    this.loadEmployees();
  }
}

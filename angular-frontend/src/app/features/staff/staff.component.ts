import { Component, OnInit } from '@angular/core';
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
  employees: Employee[] = [];
  loading = true;
  error: string | null = null;

  constructor(private employeeService: EmployeeService) {}

  ngOnInit(): void {
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.loading = true;
    this.employeeService.list().subscribe({
      next: (data) => {
        this.employees = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load employees.';
        this.loading = false;
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

  showModal = false;
  editingEmployee: Employee | null = null;

  openCreateModal(): void {
    this.editingEmployee = null;
    this.showModal = true;
  }

  openEditModal(employee: Employee): void {
    this.editingEmployee = employee;
    this.showModal = true;
  }

  onModalClose(): void {
    this.showModal = false;
  }

  onModalSaved(): void {
    this.showModal = false;
    this.loadEmployees();
  }
}

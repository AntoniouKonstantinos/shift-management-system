import { Component, EventEmitter, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Employee } from '../../../core/models/employee.model';
import { EmployeeService } from '../../../core/services/employee.service';
import { TimeOffService } from '../../../core/services/time-off.service';

@Component({
  selector: 'app-request-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './request-modal.component.html',
  styleUrl: './request-modal.component.css',
})
export class RequestModalComponent implements OnInit {
  @Output() close = new EventEmitter<void>();
  @Output() saved = new EventEmitter<void>();

  employees = signal<Employee[]>([]);

  employeeId = signal<number | null>(null);
  startDate = signal<string>('');
  endDate = signal<string>('');
  reason = signal<string>('');

  constructor(
    private employeeService: EmployeeService,
    private timeOffService: TimeOffService,
  ) {}

  ngOnInit(): void {
    this.employeeService.list().subscribe({
      next: (data) => this.employees.set(data.filter((e) => e.is_active)),
      error: (err) => console.error(err),
    });
  }

  onSubmit(): void {
    const employeeId = this.employeeId();
    const startDate = this.startDate();
    const endDate = this.endDate();

    if (!employeeId || !startDate || !endDate) {
      alert('Please select an employee and both dates.');
      return;
    }

    if (startDate > endDate) {
      alert('Start date must be before or equal to end date.');
      return;
    }

    this.timeOffService
      .create({
        employee_id: employeeId,
        start_date: startDate,
        end_date: endDate,
        reason: this.reason() || null,
      })
      .subscribe({
        next: () => this.saved.emit(),
        error: (err) => alert(err.error?.error ?? 'Failed to create request.'),
      });
  }

  onCancel(): void {
    this.close.emit();
  }
}

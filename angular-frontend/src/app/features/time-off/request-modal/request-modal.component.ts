import { Component, EventEmitter, OnInit, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Employee } from '../../../core/models/employee.model';
import { TimeOffRequestCreate } from '../../../core/models/time-off-request.model';
import { EmployeeService } from '../../../core/services/employee.service';
import { TimeOffService } from '../../../core/services/time-off.service';
import { AuthService } from '../../../core/services/auth.service';

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
    public auth: AuthService,
  ) {}

  ngOnInit(): void {
    if (!this.auth.isManager()) {
      return;
    }

    this.employeeId.set(this.auth.currentUser()?.employee_id ?? null);

    this.employeeService.list().subscribe({
      next: (data) => this.employees.set(data.filter((e) => e.is_active)),
      error: (err) => console.error(err),
    });
  }

  onSubmit(): void {
    const isManager = this.auth.isManager();
    const employeeId = this.employeeId();
    const startDate = this.startDate();
    const endDate = this.endDate();

    if (!startDate || !endDate || (isManager && !employeeId)) {
      alert('Please fill in all required fields.');
      return;
    }

    if (startDate > endDate) {
      alert('Start date must be before or equal to end date.');
      return;
    }

    const payload: TimeOffRequestCreate = {
      start_date: startDate,
      end_date: endDate,
      reason: this.reason() || null,
    };
    if (isManager && employeeId) {
      payload.employee_id = employeeId;
    }

    this.timeOffService.create(payload).subscribe({
      next: () => this.saved.emit(),
      error: (err) => alert(err.error?.error ?? 'Failed to create request.'),
    });
  }

  onCancel(): void {
    this.close.emit();
  }
}

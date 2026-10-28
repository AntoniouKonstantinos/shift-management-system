import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Availability, DAY_NAMES } from '../../core/models/availability.model';
import { Employee } from '../../core/models/employee.model';
import { AvailabilityService } from '../../core/services/availability.service';
import { EmployeeService } from '../../core/services/employee.service';
import { AuthService } from '../../core/services/auth.service';

interface DayRow {
  index: number;
  name: string;
  slots: Availability[];
}

@Component({
  selector: 'app-availability',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './availability.component.html',
  styleUrl: './availability.component.css',
})
export class AvailabilityComponent implements OnInit {
  readonly dayNames = DAY_NAMES;

  employees = signal<Employee[]>([]);
  selectedEmployeeId = signal<number | null>(null);
  slots = signal<Availability[]>([]);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  day = signal<number>(0);
  startTime = signal<string>('17:00');
  endTime = signal<string>('23:00');

  days = computed<DayRow[]>(() =>
    this.dayNames.map((name, index) => ({
      index,
      name,
      slots: this.slots().filter((slot) => slot.day_of_week === index),
    })),
  );

  constructor(
    private availabilityService: AvailabilityService,
    private employeeService: EmployeeService,
    public auth: AuthService,
  ) {}

  ngOnInit(): void {
    const myId = this.auth.currentUser()?.employee_id ?? null;

    if (!this.auth.isManager()) {
      this.selectedEmployeeId.set(myId);
      this.loadSlots();
      return;
    }

    this.employeeService.list().subscribe({
      next: (data) => {
        const active = data.filter((e) => e.is_active);
        this.employees.set(active);

        const first = active.find((e) => e.id !== myId) ?? active[0];
        this.selectedEmployeeId.set(first ? first.id : myId);
        this.loadSlots();
      },
      error: (err) => {
        this.error.set('Failed to load employees.');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onEmployeeChange(employeeId: number): void {
    this.selectedEmployeeId.set(employeeId);
    this.loadSlots();
  }

  private loadSlots(): void {
    const employeeId = this.selectedEmployeeId();
    if (employeeId === null) {
      this.loading.set(false);
      return;
    }

    this.loading.set(true);
    this.error.set(null);

    this.availabilityService.list(employeeId).subscribe({
      next: (data) => {
        this.slots.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to load availability.');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

    addSlot(): void {
    const employeeId = this.selectedEmployeeId();
    const start = this.startTime();
    const end = this.endTime();

    if (employeeId === null) {
      return;
    }
    if (!start || !end) {
      alert('Please choose a start and an end time.');
      return;
    }
    if (start === end) {
      alert('Start and end time cannot be the same.');
      return;
    }

    this.availabilityService
      .create(employeeId, { day_of_week: this.day(), start_time: start, end_time: end })
      .subscribe({
        next: () => this.loadSlots(),
        error: (err) => alert(err.error?.error ?? 'Failed to add availability.'),
      });
  }

  deleteSlot(slot: Availability): void {
    this.availabilityService.delete(slot.employee_id, slot.id).subscribe({
      next: () => this.loadSlots(),
      error: (err) => alert(err.error?.error ?? 'Failed to remove availability.'),
    });
  }
}

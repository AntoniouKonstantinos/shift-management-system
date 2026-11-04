import { Component, EventEmitter, Input, OnInit, Output, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Department } from '../../../core/models/department.model';
import { Shift, ShiftCreate } from '../../../core/models/shift.model';
import { DepartmentService } from '../../../core/services/department.service';
import { ShiftService } from '../../../core/services/shift.service';

@Component({
  selector: 'app-shift-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './shift-modal.component.html',
  styleUrl: './shift-modal.component.css',
})
export class ShiftModalComponent implements OnInit {
  @Input() shift: Shift | null = null;
  @Input() initialDate: string | null = null;
  @Output() close = new EventEmitter<void>();
  @Output() saved = new EventEmitter<void>();

  departments = signal<Department[]>([]);
  departmentId = signal<number | null>(null);
  shiftDate = signal<string>('');
  startTime = signal<string>('17:00');
  endTime = signal<string>('23:00');
  requiredStaff = signal<number | null>(1);
  notes = signal<string>('');
  saving = signal<boolean>(false);

  endsNextDay = computed(
    () => !!this.startTime() && !!this.endTime() && this.endTime() < this.startTime(),
  );

  constructor(
    private departmentService: DepartmentService,
    private shiftService: ShiftService,
  ) {}

  ngOnInit(): void {
    if (this.shift) {
      this.departmentId.set(this.shift.department_id);
      this.shiftDate.set(this.shift.shift_date);
      this.startTime.set(this.shift.start_time);
      this.endTime.set(this.shift.end_time);
      this.requiredStaff.set(this.shift.required_staff);
      this.notes.set(this.shift.notes ?? '');
    } else if (this.initialDate) {
      this.shiftDate.set(this.initialDate);
    }

    this.departmentService.list().subscribe({
      next: (data) => {
        this.departments.set(data);
        if (this.departmentId() === null && data.length > 0) {
          this.departmentId.set(data[0].id);
        }
      },
      error: (err) => console.error(err),
    });
  }

  onSubmit(): void {
    const departmentId = this.departmentId();
    const requiredStaff = this.requiredStaff();

    if (departmentId === null || !this.shiftDate() || !this.startTime() || !this.endTime()) {
      alert('Please fill in the department, the date and both times.');
      return;
    }
    if (this.startTime() === this.endTime()) {
      alert('Start and end time cannot be the same.');
      return;
    }
    if (requiredStaff === null || !Number.isInteger(requiredStaff) || requiredStaff < 1) {
      alert('Staff needed must be a whole number of at least 1.');
      return;
    }

    const payload: ShiftCreate = {
      department_id: departmentId,
      shift_date: this.shiftDate(),
      start_time: this.startTime(),
      end_time: this.endTime(),
      required_staff: requiredStaff,
      notes: this.notes().trim() || null,
    };

    this.saving.set(true);

    const request$ = this.shift
      ? this.shiftService.update(this.shift.id, payload)
      : this.shiftService.create(payload);

    request$.subscribe({
      next: () => {
        this.saving.set(false);
        this.saved.emit();
      },
      error: (err) => {
        this.saving.set(false);
        alert(err.error?.error ?? 'Failed to save the shift.');
      },
    });
  }

  onCancel(): void {
    this.close.emit();
  }
}

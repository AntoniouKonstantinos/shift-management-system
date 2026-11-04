import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Shift } from '../../core/models/shift.model';
import { ShiftService } from '../../core/services/shift.service';
import { AssignmentService } from '../../core/services/assignment.service';
import { AuthService } from '../../core/services/auth.service';
import { AssignModalComponent } from './assign-modal/assign-modal.component';
import { ShiftModalComponent } from './shift-modal/shift-modal.component';

interface DayColumn {
  date: string;
  shifts: Shift[];
}

@Component({
  selector: 'app-schedule',
  standalone: true,
  imports: [CommonModule, AssignModalComponent, ShiftModalComponent],
  templateUrl: './schedule.component.html',
  styleUrl: './schedule.component.css',
})
export class ScheduleComponent implements OnInit {
  currentWeekStart = signal<Date>(this.getMonday(new Date()));
  days = signal<DayColumn[]>([]);
  loading = signal<boolean>(true);

  activeShiftId = signal<number | null>(null);

  shiftModalOpen = signal<boolean>(false);
  editingShift = signal<Shift | null>(null);
  newShiftDate = signal<string | null>(null);

  weekLabel = computed(() => {
    const start = this.currentWeekStart();
    const end = new Date(start);
    end.setDate(end.getDate() + 6);
    return `${this.formatDate(start)} — ${this.formatDate(end)}`;
  });

  constructor(
    private shiftService: ShiftService,
    private assignmentService: AssignmentService,
    public auth: AuthService,
  ) {}

  ngOnInit(): void {
    this.loadWeek();
  }

  previousWeek(): void {
    this.shiftWeek(-7);
  }

  nextWeek(): void {
    this.shiftWeek(7);
  }

  private shiftWeek(deltaDays: number): void {
    const next = new Date(this.currentWeekStart());
    next.setDate(next.getDate() + deltaDays);
    this.currentWeekStart.set(next);
    this.loadWeek();
  }

  private loadWeek(showLoading = true): void {
    if (showLoading) {
      this.loading.set(true);
    }

    const start = this.currentWeekStart();
    const weekEnd = new Date(start);
    weekEnd.setDate(weekEnd.getDate() + 6);

    this.shiftService.list(this.formatDate(start), this.formatDate(weekEnd)).subscribe({
      next: (shifts) => {
        this.days.set(this.groupByDay(shifts));
        this.loading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.loading.set(false);
      },
    });
  }

  private groupByDay(shifts: Shift[]): DayColumn[] {
    const byDate: Record<string, Shift[]> = {};
    for (const shift of shifts) {
      if (!byDate[shift.shift_date]) byDate[shift.shift_date] = [];
      byDate[shift.shift_date].push(shift);
    }

    const start = this.currentWeekStart();
    const columns: DayColumn[] = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(start);
      day.setDate(day.getDate() + i);
      const dateStr = this.formatDate(day);
      columns.push({ date: dateStr, shifts: byDate[dateStr] ?? [] });
    }
    return columns;
  }

  private getMonday(date: Date): Date {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0, 0, 0, 0);
    return d;
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  coverageClass(shift: Shift): string {
    if (shift.assigned_count >= shift.required_staff) return 'covered';
    if (shift.assigned_count === 0) return 'empty';
    return 'partial';
  }

  shortName(fullName: string): string {
    const parts = fullName.trim().split(/\s+/);
    if (parts.length < 2) return parts[0];
    return `${parts[0]} ${parts[parts.length - 1][0]}.`;
  }

  openAssignModal(shiftId: number): void {
    this.activeShiftId.set(shiftId);
  }

  onAssignModalClose(): void {
    this.activeShiftId.set(null);
  }

  onAssignModalSaved(): void {
    this.activeShiftId.set(null);
    this.loadWeek(false);
  }

  openCreateShift(date: string): void {
    this.editingShift.set(null);
    this.newShiftDate.set(date);
    this.shiftModalOpen.set(true);
  }

  openEditShift(shift: Shift): void {
    this.editingShift.set(shift);
    this.newShiftDate.set(null);
    this.shiftModalOpen.set(true);
  }

  onShiftModalClose(): void {
    this.shiftModalOpen.set(false);
  }

  onShiftModalSaved(): void {
    this.shiftModalOpen.set(false);
    this.loadWeek(false);
  }

  deleteShift(shift: Shift): void {
    const warning =
      shift.assigned_count > 0
        ? ` The ${shift.assigned_count} assigned staff will be removed from it.`
        : '';
    const message =
      `Delete the ${shift.department} shift on ${shift.shift_date} ` +
      `(${shift.start_time}–${shift.end_time})?${warning}`;

    if (!confirm(message)) {
      return;
    }

    this.shiftService.delete(shift.id).subscribe({
      next: () => this.loadWeek(false),
      error: (err) => alert(err.error?.error ?? 'Failed to delete the shift.'),
    });
  }

  removeAssignment(assignmentId: number): void {
    this.assignmentService.remove(assignmentId).subscribe({
      next: () => this.loadWeek(false),
      error: (err) => alert(err.error?.error ?? 'Failed to remove the assignment.'),
    });
  }
}

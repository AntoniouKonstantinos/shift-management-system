import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Shift } from '../../core/models/shift.model';
import { ShiftService } from '../../core/services/shift.service';

interface DayColumn {
  date: string;
  shifts: Shift[];
}

@Component({
  selector: 'app-schedule',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './schedule.component.html',
  styleUrl: './schedule.component.css',
})
export class ScheduleComponent implements OnInit {
  currentWeekStart: Date = this.getMonday(new Date());
  days: DayColumn[] = [];
  loading = true;

  activeShiftId: number | null = null;

  constructor(private shiftService: ShiftService) {}

  ngOnInit(): void {
    this.loadWeek();
  }

  get weekLabel(): string {
    const end = new Date(this.currentWeekStart);
    end.setDate(end.getDate() + 6);
    return `${this.formatDate(this.currentWeekStart)} — ${this.formatDate(end)}`;
  }

  previousWeek(): void {
    this.shiftWeek(-7);
  }

  nextWeek(): void {
    this.shiftWeek(7);
  }

  private shiftWeek(deltaDays: number): void {
    const next = new Date(this.currentWeekStart);
    next.setDate(next.getDate() + deltaDays);
    this.currentWeekStart = next;
    this.loadWeek();
  }

  private loadWeek(): void {
    this.loading = true;
    const weekEnd = new Date(this.currentWeekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);

    this.shiftService
      .list(this.formatDate(this.currentWeekStart), this.formatDate(weekEnd))
      .subscribe({
        next: (shifts) => {
          this.days = this.groupByDay(shifts);
          this.loading = false;
        },
        error: (err) => {
          console.error(err);
          this.loading = false;
        },
      });
  }

  private groupByDay(shifts: Shift[]): DayColumn[] {
    const byDate: Record<string, Shift[]> = {};
    for (const shift of shifts) {
      if (!byDate[shift.shift_date]) byDate[shift.shift_date] = [];
      byDate[shift.shift_date].push(shift);
    }

    const columns: DayColumn[] = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(this.currentWeekStart);
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

  openAssignModal(shiftId: number): void {
    this.activeShiftId = shiftId;
  }

  onAssignModalClose(): void {
    this.activeShiftId = null;
  }

  onAssignModalSaved(): void {
    this.activeShiftId = null;
    this.loadWeek();
  }
}

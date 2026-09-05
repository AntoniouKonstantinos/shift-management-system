import {
  Component,
  EventEmitter,
  Input,
  Output,
  OnInit,
  OnChanges,
  SimpleChanges,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AssignCandidate } from '../../../core/models/assignment.model';
import { AssignmentService } from '../../../core/services/assignment.service';

@Component({
  selector: 'app-assign-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assign-modal.component.html',
  styleUrl: './assign-modal.component.css',
})
export class AssignModalComponent implements OnInit, OnChanges {
  @Input({ required: true }) shiftId!: number;
  @Output() close = new EventEmitter<void>();
  @Output() saved = new EventEmitter<void>();

  candidates = signal<AssignCandidate[]>([]);
  selectedEmployeeId = signal<number | null>(null);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);

  constructor(private assignmentService: AssignmentService) {}

  ngOnInit(): void {
    this.loadCandidates();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['shiftId'] && !changes['shiftId'].firstChange) {
      this.loadCandidates();
    }
  }

  private loadCandidates(): void {
    this.loading.set(true);
    this.error.set(null);
    this.selectedEmployeeId.set(null);

    this.assignmentService.getCandidates(this.shiftId).subscribe({
      next: (data) => {
        this.candidates.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to load candidates.');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onAssign(): void {
    const employeeId = this.selectedEmployeeId();
    if (!employeeId) {
      alert('Please select an employee.');
      return;
    }

    this.assignmentService.assign(this.shiftId, { employee_id: employeeId }).subscribe({
      next: () => this.saved.emit(),
      error: (err) => alert(err.error?.error ?? 'Failed to assign employee.'),
    });
  }

  onCancel(): void {
    this.close.emit();
  }
}

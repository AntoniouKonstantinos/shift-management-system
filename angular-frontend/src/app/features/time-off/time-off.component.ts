import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TimeOffRequest } from '../../core/models/time-off-request.model';
import { TimeOffService } from '../../core/services/time-off.service';

@Component({
  selector: 'app-time-off',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './time-off.component.html',
  styleUrl: './time-off.component.css',
})
export class TimeOffComponent implements OnInit {
  requests = signal<TimeOffRequest[]>([]);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);
  statusFilter = signal<string>('');

  showModal = signal<boolean>(false);

  constructor(private timeOffService: TimeOffService) {}

  ngOnInit(): void {
    this.loadRequests();
  }

  loadRequests(): void {
    this.loading.set(true);
    this.error.set(null);

    const status = this.statusFilter() || undefined;

    this.timeOffService.list(undefined, status).subscribe({
      next: (data) => {
        this.requests.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to load time-off requests.');
        this.loading.set(false);
        console.error(err);
      },
    });
  }

  onStatusFilterChange(value: string): void {
    this.statusFilter.set(value);
    this.loadRequests();
  }

  approve(id: number): void {
    this.timeOffService.approve(id).subscribe({
      next: () => this.loadRequests(),
      error: (err) => alert(err.error?.error ?? 'Failed to approve request.'),
    });
  }

  reject(id: number): void {
    this.timeOffService.reject(id).subscribe({
      next: () => this.loadRequests(),
      error: (err) => alert(err.error?.error ?? 'Failed to reject request.'),
    });
  }

  deleteRequest(id: number): void {
    if (!confirm('Delete this request?')) {
      return;
    }

    this.timeOffService.delete(id).subscribe({
      next: () => this.loadRequests(),
      error: (err) => alert(err.error?.error ?? 'Failed to delete request.'),
    });
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      pending: 'Pending',
      approved: 'Approved',
      rejected: 'Rejected',
    };
    return labels[status] ?? status;
  }

  openCreateModal(): void {
    this.showModal.set(true);
  }

  onModalClose(): void {
    this.showModal.set(false);
  }

  onModalSaved(): void {
    this.showModal.set(false);
    this.loadRequests();
  }
}

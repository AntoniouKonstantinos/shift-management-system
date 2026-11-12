import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TimeOffRequest } from '../../core/models/time-off-request.model';
import { TimeOffService } from '../../core/services/time-off.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmService } from '../../core/services/confirm.service';
import { ToastService } from '../../core/services/toast.service';
import { RequestModalComponent } from './request-modal/request-modal.component';

@Component({
  selector: 'app-time-off',
  standalone: true,
  imports: [CommonModule, FormsModule, RequestModalComponent],
  templateUrl: './time-off.component.html',
  styleUrl: './time-off.component.css',
})
export class TimeOffComponent implements OnInit {
  requests = signal<TimeOffRequest[]>([]);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);
  statusFilter = signal<string>('');

  showModal = signal<boolean>(false);

  constructor(
    private timeOffService: TimeOffService,
    private confirmService: ConfirmService,
    private toast: ToastService,
    public auth: AuthService,
  ) {}

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
      next: () => {
        this.toast.success('Request approved.');
        this.loadRequests();
      },
      error: (err) => this.toast.error(err.error?.error ?? 'Failed to approve the request.'),
    });
  }

  reject(id: number): void {
    this.timeOffService.reject(id).subscribe({
      next: () => {
        this.toast.success('Request rejected.');
        this.loadRequests();
      },
      error: (err) => this.toast.error(err.error?.error ?? 'Failed to reject the request.'),
    });
  }

  async deleteRequest(request: TimeOffRequest): Promise<void> {
    const isManager = this.auth.isManager();

    const confirmed = await this.confirmService.confirm({
      title: isManager ? 'Delete request' : 'Withdraw request',
      message: isManager
        ? `Delete the time-off request of ${request.employee_name} ` +
          `(${request.start_date} – ${request.end_date})?`
        : `Withdraw your time-off request for ${request.start_date} – ${request.end_date}?`,
      confirmLabel: isManager ? 'Delete' : 'Withdraw',
      danger: true,
    });
    if (!confirmed) {
      return;
    }

    this.timeOffService.delete(request.id).subscribe({
      next: () => {
        this.toast.success(isManager ? 'Request deleted.' : 'Request withdrawn.');
        this.loadRequests();
      },
      error: (err) => this.toast.error(err.error?.error ?? 'Failed to delete the request.'),
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
    this.toast.success('Time-off request submitted.');
    this.loadRequests();
  }
}

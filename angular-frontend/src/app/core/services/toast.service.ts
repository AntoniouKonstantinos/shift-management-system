import { Injectable, signal } from '@angular/core';

export type ToastKind = 'success' | 'error' | 'info';

export interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

const MAX_VISIBLE_TOASTS = 4;

@Injectable({
  providedIn: 'root',
})
export class ToastService {
  private nextId = 1;

  readonly toasts = signal<Toast[]>([]);

  success(message: string): void {
    this.show('success', message, 4000);
  }

  info(message: string): void {
    this.show('info', message, 4000);
  }

  error(message: string): void {
    this.show('error', message, 7000);
  }

  dismiss(id: number): void {
    this.toasts.update((list) => list.filter((toast) => toast.id !== id));
  }

  private show(kind: ToastKind, message: string, durationMs: number): void {
    const id = this.nextId++;
    this.toasts.update((list) => [...list, { id, kind, message }].slice(-MAX_VISIBLE_TOASTS));
    setTimeout(() => this.dismiss(id), durationMs);
  }
}

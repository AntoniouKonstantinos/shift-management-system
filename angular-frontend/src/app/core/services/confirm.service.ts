import { Injectable, signal } from '@angular/core';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

export interface ConfirmRequest {
  options: ConfirmOptions;
  resolve: (result: boolean) => void;
}

@Injectable({
  providedIn: 'root',
})
export class ConfirmService {
  readonly request = signal<ConfirmRequest | null>(null);

  confirm(options: ConfirmOptions): Promise<boolean> {
    return new Promise<boolean>((resolve) => {
      this.request()?.resolve(false);
      this.request.set({ options, resolve });
    });
  }

  answer(result: boolean): void {
    const current = this.request();
    if (!current) {
      return;
    }
    this.request.set(null);
    current.resolve(result);
  }
}

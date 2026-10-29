import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { MIN_PASSWORD_LENGTH } from '../../core/constants';

@Component({
  selector: 'app-account',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './account.component.html',
  styleUrl: './account.component.css',
})
export class AccountComponent {
  readonly minLength = MIN_PASSWORD_LENGTH;

  currentPassword = signal<string>('');
  newPassword = signal<string>('');
  confirmPassword = signal<string>('');

  submitting = signal<boolean>(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  constructor(public auth: AuthService) {}

  onSubmit(): void {
    this.error.set(null);
    this.success.set(null);

    const current = this.currentPassword();
    const next = this.newPassword();

    if (!current || !next || !this.confirmPassword()) {
      this.error.set('Please fill in all fields.');
      return;
    }
    if (next.length < this.minLength) {
      this.error.set(`The new password must be at least ${this.minLength} characters.`);
      return;
    }
    if (next !== this.confirmPassword()) {
      this.error.set('The new password and its confirmation do not match.');
      return;
    }
    if (next === current) {
      this.error.set('The new password must be different from the current one.');
      return;
    }

    this.submitting.set(true);

    this.auth.changePassword(current, next).subscribe({
      next: () => {
        this.submitting.set(false);
        this.currentPassword.set('');
        this.newPassword.set('');
        this.confirmPassword.set('');
        this.success.set('Your password has been updated.');
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(err.error?.error ?? 'Failed to change the password. Please try again.');
      },
    });
  }
}

import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  email = signal<string>('');
  password = signal<string>('');
  error = signal<string | null>(null);
  submitting = signal<boolean>(false);

  constructor(
    private auth: AuthService,
    private router: Router,
  ) {}

  onSubmit(): void {
    if (!this.email() || !this.password()) {
      this.error.set('Please enter your email and password.');
      return;
    }

    this.submitting.set(true);
    this.error.set(null);

    this.auth.login(this.email(), this.password()).subscribe({
      next: () => {
        this.submitting.set(false);
        this.router.navigateByUrl('/');
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(err.error?.error ?? 'Login failed. Please try again.');
      },
    });
  }
}

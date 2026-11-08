import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected username = '';
  protected password = '';
  protected readonly error = signal<string | null>(null);
  protected readonly pending = signal(false);

  protected async submit(): Promise<void> {
    this.error.set(null);
    this.pending.set(true);
    try {
      await this.auth.login(this.username, this.password);
      await this.router.navigate(['/']);
    } catch (error) {
      this.error.set(
        error instanceof HttpErrorResponse && error.status === 401
          ? 'Invalid username or password'
          : 'Login failed, try again later',
      );
    } finally {
      this.pending.set(false);
    }
  }
}

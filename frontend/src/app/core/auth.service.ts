import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { User } from './models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  // The session token lives in an HttpOnly cookie set by the backend and is never
  // readable by JavaScript: the authentication state derives from the loaded user.
  private readonly user = signal<User | null>(null);

  readonly currentUser = this.user.asReadonly();
  readonly isAuthenticated = computed(() => this.user() !== null);

  /** Restore the session from the cookie on startup, if there is one. */
  async bootstrap(): Promise<void> {
    try {
      this.user.set(await firstValueFrom(this.http.get<User>('/api/auth/me')));
    } catch {
      this.user.set(null);
    }
  }

  async login(username: string, password: string): Promise<void> {
    this.user.set(
      await firstValueFrom(this.http.post<User>('/api/auth/login', { username, password })),
    );
  }

  /** Forget the session after the backend rejected it (expired or revoked). */
  clear(): void {
    this.user.set(null);
  }

  async logout(): Promise<void> {
    try {
      await firstValueFrom(this.http.post<void>('/api/auth/logout', {}));
    } catch {
      // Clearing the local state is enough to log out when the backend is unreachable
    }
    this.user.set(null);
    await this.router.navigate(['/login']);
  }
}

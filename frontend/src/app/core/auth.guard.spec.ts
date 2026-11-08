import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  UrlTree,
  provideRouter,
} from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('authGuard', () => {
  const run = () =>
    TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
  });

  it('redirects to /login without a session', () => {
    const result = run();
    expect(result instanceof UrlTree && result.toString()).toBe('/login');
  });

  it('lets an authenticated user through', async () => {
    const auth = TestBed.inject(AuthService);
    const login = auth.login('admin', 'secret');
    TestBed.inject(HttpTestingController)
      .expectOne('/api/auth/login')
      .flush({ id: 1, username: 'admin', is_admin: true });
    await login;
    expect(run()).toBe(true);
  });
});

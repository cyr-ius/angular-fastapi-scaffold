import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith('/api/')) {
    return next(req);
  }
  const auth = inject(AuthService);
  const router = inject(Router);

  // The session travels in an HttpOnly cookie: send it with every API call
  return next(req.clone({ withCredentials: true })).pipe(
    catchError((error: unknown) => {
      // A 401 on /api/auth/* is expected when not logged in (startup probe, bad password)
      if (
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !req.url.startsWith('/api/auth/')
      ) {
        auth.clear();
        void router.navigate(['/login']);
      }
      return throwError(() => error);
    }),
  );
};

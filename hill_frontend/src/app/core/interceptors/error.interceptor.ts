import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { HttpErrorHandler } from '../services/http/http-error.handler';
import { AuthService } from '../services/auth/auth.service';

/**
 * Error Interceptor (Functional - Angular 20)
 * 
 * Handles HTTP errors globally:
 * - 401: Unauthorized → logout and redirect to login
 * - 403: Forbidden → show error
 * - Other errors: format and pass to HttpErrorHandler
 * 
 * Usage: Configured in app.config.ts with provideHttpClient(withInterceptors([errorInterceptor]))
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const httpErrorHandler = inject(HttpErrorHandler);
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle specific error codes
      switch (error.status) {
        case 401:
          // Unauthorized - logout and redirect to login
          console.warn('Unauthorized request detected. Logging out...');
          authService.logout();
          break;

        case 403:
          // Forbidden - user doesn't have permission
          console.warn('Forbidden: You do not have permission to access this resource.');
          break;

        case 0:
          // Network error or CORS issue
          console.error('Network error: Unable to connect to server.');
          break;

        default:
          // Log other errors
          console.error(`HTTP Error ${error.status}:`, error.message);
      }

      // Use HttpErrorHandler to format error and throw
      return httpErrorHandler.handleError(error);
    })
  );
};


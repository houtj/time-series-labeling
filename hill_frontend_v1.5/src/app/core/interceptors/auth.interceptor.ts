import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { TokenService } from '../services/auth/token.service';

/**
 * Authentication Interceptor (Functional - Angular 20)
 * 
 * Automatically attaches JWT token to all outgoing HTTP requests
 * 
 * Usage: Configured in app.config.ts with provideHttpClient(withInterceptors([authInterceptor]))
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const tokenService = inject(TokenService);
  const token = tokenService.getToken();

  // If no token, proceed with original request
  if (!token) {
    return next(req);
  }

  // Clone request and add Authorization header
  const authReq = req.clone({
    setHeaders: {
      Authorization: `Bearer ${token}`
    }
  });

  return next(authReq);
};


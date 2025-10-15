import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth/auth.service';
import { map, take } from 'rxjs/operators';

/**
 * Authentication Guard (Functional - Angular 20)
 * 
 * Protects routes that require authentication
 * Redirects to login page if user is not authenticated
 * 
 * Usage in routes:
 * {
 *   path: 'folders',
 *   component: FoldersPageComponent,
 *   canActivate: [authGuard]
 * }
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Check if user is authenticated using signal
  if (authService.isAuthenticated()) {
    return true;
  }

  // For dev mode: Check if we should allow access without auth
  // This can be toggled via environment variable
  const allowUnauthenticated = true; // Set to false when auth is required

  if (allowUnauthenticated) {
    console.warn('Auth guard bypassed for development mode');
    return true;
  }

  // Not authenticated - redirect to login
  console.warn('User not authenticated. Redirecting to login...');
  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url }
  });
};

/**
 * Alternative: Observable-based auth guard for async checks
 * Use this if you need to verify auth with the backend
 */
export const authGuardAsync: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.checkAuth().pipe(
    take(1),
    map(user => {
      if (user) {
        return true;
      }

      // Not authenticated - redirect to login
      console.warn('User not authenticated. Redirecting to login...');
      return router.createUrlTree(['/login'], {
        queryParams: { returnUrl: state.url }
      });
    })
  );
};


import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of, BehaviorSubject } from 'rxjs';
import { ApiService } from '../http/api.service';
import { TokenService } from './token.service';
import { UserProfile } from '../../models';

/**
 * Authentication service
 * Handles user authentication, login, logout
 * Uses Angular 20 signals for reactive state management
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiService = inject(ApiService);
  private readonly tokenService = inject(TokenService);
  private readonly router = inject(Router);

  // Using signals for modern Angular 20 reactive state
  readonly isAuthenticated = signal<boolean>(this.tokenService.hasToken());
  readonly currentUser = signal<UserProfile | null>(null);

  // Fallback BehaviorSubject for components not yet using signals
  readonly isAuthenticated$ = new BehaviorSubject<boolean>(this.tokenService.hasToken());
  readonly currentUser$ = new BehaviorSubject<UserProfile | null>(null);

  /**
   * Login with credentials
   */
  login(credentials: { email: string; password: string }): Observable<any> {
    return this.apiService.post('/auth/login', credentials).pipe(
      tap((response: any) => {
        if (response.token) {
          this.tokenService.saveToken(response.token);
          if (response.refreshToken) {
            this.tokenService.saveRefreshToken(response.refreshToken);
          }
          this.setAuthenticated(true);
          if (response.user) {
            this.setCurrentUser(response.user);
          }
        }
      })
    );
  }

  /**
   * Logout
   */
  logout(): void {
    this.tokenService.clearTokens();
    this.setAuthenticated(false);
    this.setCurrentUser(null);
    this.router.navigate(['/login']);
  }

  /**
   * Check if user is authenticated
   */
  checkAuth(): Observable<UserProfile> {
    if (!this.tokenService.hasToken()) {
      this.setAuthenticated(false);
      return of(null as any);
    }

    return this.apiService.get<UserProfile>('/auth/me').pipe(
      tap((user) => {
        this.setAuthenticated(true);
        this.setCurrentUser(user);
      }),
      catchError(() => {
        this.logout();
        return of(null as any);
      })
    );
  }

  /**
   * Refresh authentication token
   */
  refreshToken(): Observable<any> {
    const refreshToken = this.tokenService.getRefreshToken();
    if (!refreshToken) {
      return of(null);
    }

    return this.apiService.post('/auth/refresh', { refreshToken }).pipe(
      tap((response: any) => {
        if (response.token) {
          this.tokenService.saveToken(response.token);
        }
      }),
      catchError(() => {
        this.logout();
        return of(null);
      })
    );
  }

  /**
   * Set authentication state
   */
  private setAuthenticated(value: boolean): void {
    this.isAuthenticated.set(value);
    this.isAuthenticated$.next(value);
  }

  /**
   * Set current user
   */
  private setCurrentUser(user: UserProfile | null): void {
    this.currentUser.set(user);
    this.currentUser$.next(user);
  }

  /**
   * Get current user value (synchronous)
   */
  getCurrentUser(): UserProfile | null {
    return this.currentUser();
  }

  /**
   * Check if user is authenticated (synchronous)
   */
  isUserAuthenticated(): boolean {
    return this.isAuthenticated();
  }
}


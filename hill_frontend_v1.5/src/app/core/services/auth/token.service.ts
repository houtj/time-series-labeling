import { Injectable } from '@angular/core';

/**
 * Token management service
 * Handles storage and retrieval of authentication tokens
 */
@Injectable({
  providedIn: 'root'
})
export class TokenService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';

  /**
   * Save access token
   */
  saveToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Get access token
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Remove access token
   */
  removeToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  /**
   * Save refresh token
   */
  saveRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Remove refresh token
   */
  removeRefreshToken(): void {
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Clear all tokens
   */
  clearTokens(): void {
    this.removeToken();
    this.removeRefreshToken();
  }

  /**
   * Check if user has valid token
   */
  hasToken(): boolean {
    return !!this.getToken();
  }
}


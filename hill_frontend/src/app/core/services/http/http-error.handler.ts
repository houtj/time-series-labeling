import { Injectable, inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';

/**
 * HTTP error types
 */
export interface AppError {
  message: string;
  statusCode?: number;
  error?: any;
}

/**
 * Centralized HTTP error handler
 * Provides consistent error handling and user-friendly messages
 */
@Injectable({
  providedIn: 'root'
})
export class HttpErrorHandler {
  
  /**
   * Handle HTTP errors and return user-friendly messages
   */
  handleError(error: HttpErrorResponse): Observable<never> {
    const appError: AppError = {
      message: this.getErrorMessage(error),
      statusCode: error.status,
      error: error.error
    };

    console.error('HTTP Error:', appError);
    
    return throwError(() => appError);
  }

  /**
   * Get user-friendly error message based on error type
   */
  private getErrorMessage(error: HttpErrorResponse): string {
    if (error.error instanceof ErrorEvent) {
      // Client-side or network error
      return `Network error: ${error.error.message}`;
    }

    // Server-side error
    switch (error.status) {
      case 0:
        return 'Unable to connect to server. Please check your internet connection.';
      case 400:
        return error.error?.message || 'Invalid request. Please check your input.';
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return error.error?.message || 'A conflict occurred. The resource may already exist.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service unavailable. Please try again later.';
      default:
        return error.error?.message || `An unexpected error occurred (${error.status}).`;
    }
  }

  /**
   * Check if error is a specific status code
   */
  isStatus(error: any, statusCode: number): boolean {
    return error?.statusCode === statusCode;
  }

  /**
   * Check if error is authentication related
   */
  isAuthError(error: any): boolean {
    return error?.statusCode === 401 || error?.statusCode === 403;
  }

  /**
   * Check if error is network related
   */
  isNetworkError(error: any): boolean {
    return error?.statusCode === 0;
  }
}


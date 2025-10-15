import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

/**
 * Central API service for all HTTP requests
 * Provides a consistent interface for making HTTP calls
 * 
 * Modern Angular 20 with inject() function
 */
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  /**
   * GET request
   */
  get<T>(path: string, params?: HttpParams | { [key: string]: string | string[] }): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${path}`, { params });
  }

  /**
   * POST request
   */
  post<T>(path: string, body: any = {}): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${path}`, body);
  }

  /**
   * PUT request
   */
  put<T>(path: string, body: any = {}): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${path}`, body);
  }

  /**
   * PATCH request
   */
  patch<T>(path: string, body: any = {}): Observable<T> {
    return this.http.patch<T>(`${this.baseUrl}${path}`, body);
  }

  /**
   * DELETE request
   */
  delete<T>(path: string, params?: HttpParams | { [key: string]: string | string[] }): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${path}`, { params });
  }

  /**
   * Upload file with progress tracking
   */
  upload<T>(path: string, formData: FormData): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${path}`, formData, {
      reportProgress: true,
    });
  }

  /**
   * Get full URL for a path
   */
  getFullUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }
}


import { Injectable, inject } from '@angular/core';
import { Observable, map, catchError } from 'rxjs';
import { HttpParams } from '@angular/common/http';
import { ApiService } from '../services/http/api.service';
import { HttpErrorHandler } from '../services/http/http-error.handler';

/**
 * Base Repository
 * 
 * Provides common CRUD operations for all repositories
 * Handles JSON parsing from backend (backend returns stringified JSON)
 * 
 * Generic T: The model type (e.g., UserModel, FolderModel)
 */
@Injectable({
  providedIn: 'root'
})
export abstract class BaseRepository<T> {
  protected readonly apiService = inject(ApiService);
  protected readonly errorHandler = inject(HttpErrorHandler);

  /**
   * Abstract property - each repository defines its base path
   * Example: '/users', '/folders', '/files'
   */
  protected abstract readonly basePath: string;

  /**
   * Get all items
   */
  protected getAll(params?: HttpParams | { [key: string]: string | string[] }): Observable<T[]> {
    return this.apiService.get<string>(this.basePath, params).pipe(
      map(response => this.parseResponse<T[]>(response) as T[]),
      catchError(error => this.errorHandler.handleError(error))
    ) as Observable<T[]>;
  }

  /**
   * Get single item by ID
   */
  protected getById(id: string): Observable<T> {
    return this.apiService.get<string>(`${this.basePath}/${id}`).pipe(
      map(response => this.parseResponse<T>(response) as T),
      catchError(error => this.errorHandler.handleError(error))
    ) as Observable<T>;
  }

  /**
   * Create new item
   */
  protected create(item: Partial<T>): Observable<any> {
    return this.apiService.post(this.basePath, item).pipe(
      catchError(error => this.errorHandler.handleError(error))
    );
  }

  /**
   * Update existing item
   */
  protected update(id: string, item: Partial<T>): Observable<any> {
    return this.apiService.put(`${this.basePath}/${id}`, item).pipe(
      catchError(error => this.errorHandler.handleError(error))
    );
  }

  /**
   * Delete item
   */
  protected delete(id: string): Observable<any> {
    return this.apiService.delete(`${this.basePath}/${id}`).pipe(
      catchError(error => this.errorHandler.handleError(error))
    );
  }

  /**
   * Parse JSON response from backend
   * Backend returns stringified JSON (due to MongoDB ObjectId serialization)
   */
  protected parseResponse<R = T>(response: string | R): R {
    if (typeof response === 'string') {
      try {
        return JSON.parse(response) as R;
      } catch (error) {
        console.error('Failed to parse response:', error);
        throw error;
      }
    }
    return response as R;
  }

  /**
   * Build HttpParams from object
   */
  protected buildParams(params: { [key: string]: any }): HttpParams {
    let httpParams = new HttpParams();
    Object.keys(params).forEach(key => {
      const value = params[key];
      if (value !== null && value !== undefined) {
        httpParams = httpParams.set(key, typeof value === 'object' ? JSON.stringify(value) : value);
      }
    });
    return httpParams;
  }
}


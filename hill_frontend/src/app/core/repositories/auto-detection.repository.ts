import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { AutoDetectionConversation } from '../models';

/**
 * Auto-Detection Repository
 * Handles all auto-detection conversation data access
 */
@Injectable({
  providedIn: 'root'
})
export class AutoDetectionRepository extends BaseRepository<AutoDetectionConversation> {
  protected readonly basePath = '/conversations/detection';

  /**
   * Get auto-detection conversation for file
   */
  getDetectionConversation(fileId: string): Observable<AutoDetectionConversation> {
    return this.apiService.get<string>(`${this.basePath}/${fileId}`).pipe(
      map(response => this.parseResponse<AutoDetectionConversation>(response))
    );
  }

  /**
   * Clear auto-detection conversation for file
   */
  clearDetectionConversation(fileId: string): Observable<string> {
    return this.apiService.delete(`${this.basePath}/${fileId}`);
  }

  /**
   * Get latest detection run for file
   */
  getLatestRun(fileId: string): Observable<any> {
    return this.apiService.get<string>(`${this.basePath}/${fileId}/latest`).pipe(
      map(response => this.parseResponse(response))
    );
  }

  /**
   * Get detection history for file
   */
  getDetectionHistory(fileId: string): Observable<any[]> {
    return this.apiService.get<string>(`${this.basePath}/${fileId}/history`).pipe(
      map(response => this.parseResponse<any[]>(response))
    );
  }
}


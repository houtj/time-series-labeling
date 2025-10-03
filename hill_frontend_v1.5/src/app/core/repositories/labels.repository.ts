import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { LabelModel, LabeledEvent } from '../models';
import { UserStateService } from '../services';

/**
 * Labels Repository
 * Handles all label-related data access
 */
@Injectable({
  providedIn: 'root'
})
export class LabelsRepository extends BaseRepository<LabelModel> {
  protected readonly basePath = '/labels';
  private readonly userState = inject(UserStateService);

  /**
   * Get label by ID
   */
  getLabel(labelId: string): Observable<LabelModel> {
    return this.getById(labelId);
  }

  /**
   * Save/update entire label
   * Note: Backend expects PUT /labels with body: { label: LabelModel, user: string }
   */
  saveLabel(label: LabelModel): Observable<string> {
    const userInfo = this.userState.userInfo();
    const userName = userInfo?.name || 'Unknown';
    
    // Backend expects label and user in request body, not ID in URL
    return this.apiService.put(this.basePath, {
      label: label,
      user: userName
    });
  }

  /**
   * Add single event to label
   */
  addEvent(labelId: string, event: LabeledEvent): Observable<string> {
    return this.apiService.post(`${this.basePath}/event`, {
      labelId,
      ...event
    });
  }

  /**
   * Add multiple events to label
   */
  addEvents(labelId: string, events: LabeledEvent[]): Observable<string> {
    return this.apiService.post(`${this.basePath}/events`, {
      labelId,
      events
    });
  }

  /**
   * Update event in label
   */
  updateEvent(labelId: string, eventIndex: number, event: Partial<LabeledEvent>): Observable<string> {
    return this.apiService.put(`${this.basePath}/event`, {
      labelId,
      eventIndex,
      ...event
    });
  }

  /**
   * Delete event from label
   */
  deleteEvent(labelId: string, eventIndex: number): Observable<string> {
    const params = this.buildParams({ labelId, eventIndex: eventIndex.toString() });
    return this.apiService.delete(`${this.basePath}/event`, params);
  }

  /**
   * Add class to label
   */
  addClass(labelId: string, classData: {
    name: string;
    color: string;
    description: string;
  }): Observable<string> {
    return this.apiService.post(`${this.basePath}/classes`, {
      labelId,
      ...classData
    });
  }

  /**
   * Update class in label
   */
  updateClass(labelId: string, className: string, updates: {
    newName?: string;
    color?: string;
    description?: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/classes`, {
      labelId,
      className,
      ...updates
    });
  }

  /**
   * Add guideline to label
   */
  addGuideline(labelId: string, guideline: any): Observable<string> {
    return this.apiService.post(`${this.basePath}/guideline`, {
      labelId,
      ...guideline
    });
  }

  /**
   * Update guideline in label
   */
  updateGuideline(labelId: string, guidelineIndex: number, guideline: any): Observable<string> {
    return this.apiService.put(`${this.basePath}/guideline`, {
      labelId,
      guidelineIndex,
      ...guideline
    });
  }

  /**
   * Delete guideline from label
   */
  deleteGuideline(labelId: string, guidelineIndex: number): Observable<string> {
    const params = this.buildParams({ labelId, guidelineIndex: guidelineIndex.toString() });
    return this.apiService.delete(`${this.basePath}/guideline`, params);
  }
}


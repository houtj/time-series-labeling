import { Injectable, inject } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { tap, switchMap, debounceTime, catchError } from 'rxjs/operators';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

// Core imports
import { LabelsRepository, FilesRepository, UsersRepository } from '../../../core/repositories';
import { UserStateService } from '../../../core/services';
import { FileModel, FolderModel, LabelModel, UserModel, DataModel } from '../../../core/models';
import { environment } from '../../../../environments/environment';

// Feature services
import { LabelStateService } from './label-state.service';

// PrimeNG
import { MessageService } from 'primeng/api';

/**
 * Labeling Actions Service
 * Handles all business logic for labeling operations:
 * - Save labels (manual and auto-save)
 * - Import/Export labels
 * - Download data
 * - Share folders
 * - Refresh data
 */
@Injectable()
export class LabelingActionsService {
  private readonly labelsRepo = inject(LabelsRepository);
  private readonly filesRepo = inject(FilesRepository);
  private readonly usersRepo = inject(UsersRepository);
  private readonly http = inject(HttpClient);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly userState = inject(UserStateService);
  private readonly labelState = inject(LabelStateService);
  private readonly messageService = inject(MessageService);
  
  // Auto-save queue with debouncing
  private autoSaveQueue$ = new Subject<{ label: LabelModel; labelId: string }>();
  
  constructor() {
    // Set up auto-save with 500ms debounce
    this.autoSaveQueue$.pipe(
      debounceTime(500),
      switchMap(({ label, labelId }) => 
        this.labelsRepo.saveLabel(label).pipe(
          // Silently save (no toast for auto-save)
          tap(() => {
            console.log('Auto-saved guideline');
          }),
          // Refetch to sync with backend
          switchMap(() => this.labelsRepo.getLabel(labelId)),
          tap((freshLabel: LabelModel) => {
            // Update state with fresh data from backend
            this.labelState.updateLabel(freshLabel);
          }),
          catchError((error) => {
            console.error('Auto-save failed:', error);
            this.messageService.add({
              severity: 'warn',
              summary: 'Auto-save Failed',
              detail: 'Failed to auto-save changes'
            });
            throw error;
          })
        )
      )
    ).subscribe();
  }

  /**
   * Save current label to database (manual save with toast)
   */
  saveLabel(labelInfo: LabelModel): Observable<string> {
    return this.labelsRepo.saveLabel(labelInfo).pipe(
      tap(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Labels saved successfully'
        });
      })
    );
  }
  
  /**
   * Queue label for auto-save (debounced, silent)
   */
  queueAutoSave(label: LabelModel): void {
    const labelId = label._id?.$oid;
    if (!labelId) {
      console.warn('Cannot auto-save: label ID is missing');
      return;
    }
    this.autoSaveQueue$.next({ label, labelId });
  }

  /**
   * Import labels from a JSON file
   */
  importLabels(fileInputId: string, labelInfo: LabelModel, userInfo: UserModel, fileInfo: FileModel): Observable<LabelModel> {
    const input = document.getElementById(fileInputId) as HTMLInputElement;
    const file = input?.files?.[0];
    
    if (!file) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'No file selected'
      });
      throw new Error('No file selected');
    }
    
    const labelId = labelInfo._id?.$oid || '';
    const formData = new FormData();
    formData.append('data', labelId);
    formData.append('user', userInfo.name);
    formData.append('file', file, file.name);
    
    return this.http.post(`${environment.apiUrl}/labels/event`, formData).pipe(
      tap(() => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Labels imported successfully'
        });
        // Clear the file input
        input.value = '';
      }),
      // Automatically refetch fresh label data after import
      switchMap(() => this.labelsRepo.getLabel(labelId)),
      tap((freshLabel: LabelModel) => {
        // Update state with imported labels
        this.labelState.updateLabel(freshLabel);
      }),
      catchError((error) => {
        console.error('Failed to import labels:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to import labels'
        });
        // Clear the file input
        input.value = '';
        throw error;
      })
    );
  }

  /**
   * Export labels as JSON download
   */
  exportLabels(labelInfo: LabelModel): SafeResourceUrl {
    if (!labelInfo) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'No label data available'
      });
      throw new Error('No label data available');
    }
    
    // Export both events and guidelines
    const exportData = {
      events: labelInfo.events || [],
      guidelines: labelInfo.guidelines || []
    };
    const json = JSON.stringify(exportData);
    return this.sanitizer.bypassSecurityTrustUrl(
      'data:text/json;charset=UTF-8,' + encodeURIComponent(json)
    );
  }

  /**
   * Download file data as JSON
   */
  downloadData(fileId: string): Observable<SafeResourceUrl> {
    if (!fileId) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'No file selected'
      });
      throw new Error('No file selected');
    }
    
    return this.filesRepo.getFile(fileId).pipe(
      tap({
        next: (result: { fileInfo: FileModel; data: DataModel[] }) => {
          const json = JSON.stringify(result.data);
          return this.sanitizer.bypassSecurityTrustUrl(
            'data:text/json;charset=UTF-8,' + encodeURIComponent(json)
          );
        },
        error: (error: any) => {
          console.error('Failed to download data:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to download data'
          });
        }
      }),
      switchMap((result: { fileInfo: FileModel; data: DataModel[] }) => {
        const json = JSON.stringify(result.data);
        const uri = this.sanitizer.bypassSecurityTrustUrl(
          'data:text/json;charset=UTF-8,' + encodeURIComponent(json)
        );
        return new Observable<SafeResourceUrl>(observer => {
          observer.next(uri);
          observer.complete();
        });
      })
    );
  }

  /**
   * Share folder with another user
   */
  shareFolder(folderInfo: FolderModel, targetUser: UserModel, message: string): Observable<any> {
    const currentUser = this.userState.userInfo();
    
    if (!currentUser) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'User not authenticated'
      });
      throw new Error('User not authenticated');
    }
    
    const data = {
      folder: folderInfo,
      user: targetUser,
      userName: currentUser.name,
      message: message
    };
    
    return this.usersRepo.shareFolderWithUser(data).pipe(
      tap({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Folder shared successfully'
          });
        },
        error: (error: any) => {
          console.error('Failed to share folder:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to share folder'
          });
        }
      })
    );
  }

  /**
   * Refresh label data from database
   */
  refreshLabelData(labelId: string): Observable<LabelModel> {
    return this.labelsRepo.getLabel(labelId).pipe(
      tap({
        next: (label: LabelModel) => {
          this.labelState.updateLabel(label);
          this.messageService.add({
            severity: 'success',
            summary: 'Refreshed',
            detail: 'Label data reloaded from database'
          });
        },
        error: (error: any) => {
          console.error('Failed to refresh label data:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to refresh label data'
          });
        }
      })
    );
  }
}


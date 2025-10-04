import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { FileModel, DataModel } from '../models';

/**
 * Files Repository
 * Handles all file-related data access
 */
@Injectable({
  providedIn: 'root'
})
export class FilesRepository extends BaseRepository<FileModel> {
  protected readonly basePath = '/files';

  /**
   * Get multiple files by IDs
   */
  getFiles(fileIds: string[]): Observable<FileModel[]> {
    const params = this.buildParams({ filesId: JSON.stringify(fileIds) });
    return this.getAll(params);
  }

  /**
   * Get single file with data
   */
  getFile(fileId: string): Observable<{ fileInfo: FileModel; data: DataModel[] }> {
    return this.apiService.get<string>(`${this.basePath}/${fileId}`).pipe(
      map(response => {
        const parsed = this.parseResponse<any>(response);
        return {
          fileInfo: this.parseResponse(parsed.fileInfo),
          data: this.parseResponse(parsed.data)
        };
      })
    );
  }

  /**
   * Upload files
   */
  uploadFiles(folderId: string, userName: string, files: File[]): Observable<string> {
    const formData = new FormData();
    formData.append('data', folderId);
    formData.append('user', userName);
    files.forEach(file => formData.append('files', file));
    
    return this.apiService.upload(this.basePath, formData);
  }

  /**
   * Update file description
   */
  updateDescription(fileId: string, description: string, userName: string): Observable<string> {
    return this.apiService.put(`${this.basePath}/description`, {
      fileId,
      description,
      userName
    });
  }

  /**
   * Delete file
   */
  deleteFile(fileId: string, folderId: string): Observable<string> {
    const params = this.buildParams({ fileId, folderId });
    return this.apiService.delete(this.basePath, params);
  }

  /**
   * Reparse files in a folder
   */
  reparseFiles(folderId: string): Observable<string> {
    return this.apiService.put(`${this.basePath}/reparse`, {
      folderId
    });
  }

  /**
   * Download JSON files (all files data in folder)
   */
  downloadJsonFiles(folderId: string): Observable<string> {
    return this.apiService.get<string>(`${this.basePath}/data/${folderId}`);
  }

  /**
   * Get files with events (for folder overview)
   */
  getFilesEvents(folderId: string): Observable<any> {
    return this.apiService.get<string>(`${this.basePath}/events/${folderId}`).pipe(
      map(response => this.parseResponse(response))
    );
  }
}


import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { FolderModel } from '../models';

/**
 * Folders Repository
 * Handles all folder-related data access
 */
@Injectable({
  providedIn: 'root'
})
export class FoldersRepository extends BaseRepository<FolderModel> {
  protected readonly basePath = '/folders';

  /**
   * Get multiple folders by IDs
   */
  getFolders(folderIds: string[]): Observable<FolderModel[]> {
    const params = this.buildParams({ folders: JSON.stringify(folderIds) });
    return this.getAll(params);
  }

  /**
   * Get single folder by ID
   */
  getFolder(folderId: string): Observable<FolderModel> {
    return this.getById(folderId);
  }

  /**
   * Create new folder
   */
  createFolder(data: {
    newFolderName: string;
    project: { id: string; name: string };
    template: { id: string; name: string };
    userId: string;
  }): Observable<string> {
    return this.create(data);
  }

  /**
   * Delete folder
   */
  deleteFolder(folder: FolderModel): Observable<string> {
    const params = this.buildParams({ folder: JSON.stringify(folder) });
    return this.apiService.delete(`${this.basePath}`, params);
  }
}


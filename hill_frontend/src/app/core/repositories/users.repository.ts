import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { UserModel } from '../models';

/**
 * Users Repository
 * Handles all user-related data access
 */
@Injectable({
  providedIn: 'root'
})
export class UsersRepository extends BaseRepository<UserModel> {
  protected readonly basePath = '/users';

  /**
   * Get current user info (default user in dev mode)
   */
  getUserInfo(): Observable<UserModel> {
    return this.apiService.get<string>(`${this.basePath}/info`).pipe(
      map(response => this.parseResponse<UserModel>(response))
    );
  }

  /**
   * Get all users
   */
  getAllUsers(): Observable<UserModel[]> {
    return this.getAll();
  }

  /**
   * Share folder with user
   */
  shareFolderWithUser(data: {
    folder: any;
    user: UserModel;
    userName: string;
    message: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/shared-folders`, data);
  }

  /**
   * Share files with user
   */
  shareFilesWithUser(data: {
    folder: any;
    user: UserModel;
    userName: string;
    message: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/shared-files`, data);
  }

  /**
   * Share project with user
   */
  shareProjectWithUser(data: {
    project: any;
    user: UserModel;
    userName: string;
    message: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/shared-projects`, data);
  }

  /**
   * Update user's recent files
   */
  updateRecentFiles(data: {
    userInfo: UserModel;
    folderId: string;
    fileId: string;
    folderName: string;
    fileName: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/recent-files`, data);
  }
}


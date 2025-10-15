import { Injectable, signal, computed } from '@angular/core';
import { UserModel, FolderModel, FileModel, ProjectModel, LabelModel, DataModel } from '../../models';

/**
 * User state management service
 * Centralized state management using Angular 20 signals
 * Replaces scattered BehaviorSubjects with modern reactive primitives
 */
@Injectable({
  providedIn: 'root'
})
export class UserStateService {
  
  // UI State
  readonly pageTitle = signal<string | undefined>(undefined);
  readonly pageLabel = signal<string | undefined>(undefined);

  // User State
  readonly userInfo = signal<UserModel | undefined>(undefined);
  
  // Collections
  readonly projectList = signal<ProjectModel[]>([]);
  readonly folderList = signal<FolderModel[]>([]);
  readonly filesList = signal<FileModel[]>([]);

  // Selected Items
  readonly selectedFolder = signal<FolderModel | undefined>(undefined);
  readonly selectedFile = signal<FileModel | undefined>(undefined);
  readonly selectedLabel = signal<LabelModel | undefined>(undefined);
  readonly selectedData = signal<DataModel[] | undefined>(undefined);

  // Computed values
  readonly hasUser = computed(() => !!this.userInfo());
  readonly hasProjects = computed(() => this.projectList().length > 0);
  readonly hasFolders = computed(() => this.folderList().length > 0);
  readonly hasFiles = computed(() => this.filesList().length > 0);

  /**
   * Update page title
   */
  updatePageTitle(title: string): void {
    this.pageTitle.set(title);
  }

  /**
   * Update page label
   */
  updatePageLabel(label: string): void {
    this.pageLabel.set(label);
  }

  /**
   * Set user info
   */
  setUserInfo(user: UserModel): void {
    this.userInfo.set(user);
  }

  /**
   * Set project list
   */
  setProjectList(projects: ProjectModel[]): void {
    this.projectList.set(projects);
  }

  /**
   * Set folder list
   */
  setFolderList(folders: FolderModel[]): void {
    this.folderList.set(folders);
  }

  /**
   * Set files list
   */
  setFilesList(files: FileModel[]): void {
    this.filesList.set(files);
  }

  /**
   * Select folder
   */
  selectFolder(folder: FolderModel): void {
    this.selectedFolder.set(folder);
  }

  /**
   * Select file
   */
  selectFile(file: FileModel): void {
    this.selectedFile.set(file);
  }

  /**
   * Set selected label
   */
  setSelectedLabel(label: LabelModel): void {
    this.selectedLabel.set(label);
  }

  /**
   * Set selected data
   */
  setSelectedData(data: DataModel[]): void {
    this.selectedData.set(data);
  }

  /**
   * Clear all selections
   */
  clearSelections(): void {
    this.selectedFolder.set(undefined);
    this.selectedFile.set(undefined);
    this.selectedLabel.set(undefined);
    this.selectedData.set(undefined);
  }

  /**
   * Clear all state
   */
  clearState(): void {
    this.pageTitle.set(undefined);
    this.pageLabel.set(undefined);
    this.userInfo.set(undefined);
    this.projectList.set([]);
    this.folderList.set([]);
    this.filesList.set([]);
    this.clearSelections();
  }

  /**
   * Get user info (synchronous access)
   */
  getUserInfo(): UserModel | undefined {
    return this.userInfo();
  }

  /**
   * Get selected folder (synchronous access)
   */
  getSelectedFolder(): FolderModel | undefined {
    return this.selectedFolder();
  }

  /**
   * Get selected file (synchronous access)
   */
  getSelectedFile(): FileModel | undefined {
    return this.selectedFile();
  }
}


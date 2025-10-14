import { Component, OnInit, OnDestroy, ViewChild, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

// PrimeNG imports
import { TableModule, Table } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Dialog } from 'primeng/dialog';
import { Select } from 'primeng/select';
import { SpeedDial } from 'primeng/speeddial';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { Toast } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';

// Core services and models
import { UserStateService } from '../../../core/services';
import { FoldersRepository, UsersRepository, ProjectsRepository } from '../../../core/repositories';
import { FolderModel, ProjectModel, UserModel } from '../../../core/models';

// Shared components
import { ShareDialogComponent, TemplateEditorDialogComponent } from '../../../shared/components';

@Component({
  selector: 'app-folders-page',
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputText,
    Dialog,
    Select,
    SpeedDial,
    ConfirmPopupModule,
    Toast,
    ShareDialogComponent,
    TemplateEditorDialogComponent
  ],
  standalone: true,
  providers: [ConfirmationService, MessageService],
  templateUrl: './folders-page.html',
  styleUrl: './folders-page.scss'
})
export class FoldersPageComponent implements OnInit, OnDestroy {
  @ViewChild('dt1') table?: Table;

  // Inject services
  private readonly router = inject(Router);
  private readonly userState = inject(UserStateService);
  private readonly foldersRepo = inject(FoldersRepository);
  private readonly usersRepo = inject(UsersRepository);
  private readonly projectsRepo = inject(ProjectsRepository);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly subscriptions = new Subscription();

  // Signals for reactive state
  readonly folders = signal<FolderModel[]>([]);
  readonly loading = signal(true);

  // Component state
  newFolderDialogVisible = false;
  newFolderName = '';
  userInfo?: UserModel;
  projectList?: ProjectModel[];
  templateList?: ProjectModel['templates'];
  newFolderProject?: ProjectModel;
  newFolderTemplate?: ProjectModel['templates'][0];
  
  shareDialogVisible = false;
  usersList?: UserModel[];
  selectedUser?: UserModel;
  selectedFolder?: FolderModel;
  
  templateEditorDialogVisible = false;
  editingTemplateId?: string;
  editingProjectId?: string;
  
  filterText = '';

  ngOnInit(): void {
    this.userState.updatePageTitle('Folders');
    this.loadUserAndFolders();
  }

  /**
   * Load user info and folders
   */
  private loadUserAndFolders(): void {
    this.loading.set(true);
    
    this.usersRepo.getUserInfo().subscribe({
      next: (user) => {
        this.userInfo = user;
        this.userState.setUserInfo(user);
        
        // Load folders if user has any
        if (user.folderList && user.folderList.length > 0) {
          this.loadFolders(user.folderList);
        } else {
          this.loading.set(false);
        }
        
        // Load projects for user
        if (user.projectList && user.projectList.length > 0) {
          this.loadProjects(user.projectList);
        }
      },
      error: (error) => {
        console.error('Failed to load user info:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load user information'
        });
        this.loading.set(false);
      }
    });
  }

  /**
   * Load folders from backend
   */
  private loadFolders(folderIds: string[]): void {
    this.foldersRepo.getFolders(folderIds).subscribe({
      next: (folders) => {
        this.folders.set(folders);
        this.userState.setFolderList(folders);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load folders:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load folders'
        });
        this.loading.set(false);
      }
    });
  }

  /**
   * Load projects for dropdown
   */
  private loadProjects(projectIds: string[]): void {
    this.projectsRepo.getProjects(projectIds).subscribe({
      next: (projects) => {
        this.projectList = projects;
        this.userState.setProjectList(projects);
      },
      error: (error) => {
        console.error('Failed to load projects:', error);
      }
    });
  }

  /**
   * Open new folder dialog
   */
  onClickNewFolder(event: MouseEvent, isSubmit: boolean): void {
    if (!isSubmit) {
      // Open dialog
      this.newFolderName = '';
      if (this.projectList && this.projectList.length > 0) {
        this.newFolderProject = this.projectList[0];
        this.templateList = this.projectList[0].templates;
        if (this.templateList && this.templateList.length > 0) {
          this.newFolderTemplate = this.templateList[0];
        }
      }
      this.newFolderDialogVisible = true;
    } else {
      // Submit new folder
      if (!this.newFolderName || !this.newFolderProject || !this.newFolderTemplate || !this.userInfo) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Validation Error',
          detail: 'Please fill all fields'
        });
        return;
      }

      const data = {
        newFolderName: this.newFolderName,
        project: {
          id: this.newFolderProject._id?.$oid || '',
          name: this.newFolderProject.projectName
        },
        template: {
          id: this.newFolderTemplate.id,
          name: this.newFolderTemplate.name
        },
        userId: this.userInfo._id?.$oid || ''
      };

      this.foldersRepo.createFolder(data).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Folder created successfully'
          });
          this.newFolderDialogVisible = false;
          this.loadUserAndFolders(); // Refresh list
        },
        error: (error) => {
          console.error('Failed to create folder:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create folder'
          });
        }
      });
    }
  }

  /**
   * Handle project selection change
   */
  onChangeSelectedProject(event: any): void {
    this.templateList = this.newFolderProject?.templates;
    if (this.templateList && this.templateList.length > 0) {
      this.newFolderTemplate = this.templateList[0];
    }
  }

  /**
   * Navigate to folder (files page)
   */
  onClickFolder(event: MouseEvent, folder: FolderModel): void {
    const folderId = folder._id?.$oid;
    if (folderId) {
      this.router.navigate(['/files', folderId]);
    }
  }

  /**
   * Delete folder
   */
  onClickRemove(event: MouseEvent, folder: FolderModel): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure you want to remove the folder? All files will be lost.',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () => {
        this.foldersRepo.deleteFolder(folder).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Success',
              detail: 'Folder deleted successfully'
            });
            this.loadUserAndFolders(); // Refresh list
          },
          error: (error) => {
            console.error('Failed to delete folder:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to delete folder'
            });
          }
        });
      }
    });
  }

  /**
   * Open share dialog
   */
  onClickShare(event: MouseEvent, folder: FolderModel): void {
    this.selectedFolder = folder;
    this.shareDialogVisible = true;
  }

  /**
   * Handle share action from dialog
   */
  onShareFolder(event: { user: UserModel; message: string }): void {
    if (!this.selectedFolder || !this.userInfo) {
      return;
    }

    const data = {
      folder: this.selectedFolder,
      user: event.user,
      userName: this.userInfo.name,
      message: event.message
    };

    this.usersRepo.shareFolderWithUser(data).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Folder shared successfully'
        });
        this.shareDialogVisible = false;
      },
      error: (error) => {
        console.error('Failed to share folder:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to share folder'
        });
        this.shareDialogVisible = false;
      }
    });
  }

  /**
   * Refresh folders list
   */
  onClickRefresh(event: MouseEvent): void {
    this.loadUserAndFolders();
    this.messageService.add({
      severity: 'success',
      summary: 'Refreshed',
      detail: 'Folders synchronized with database'
    });
  }

  /**
   * Open template editor for selected template
   */
  onClickManagement(event: MouseEvent): void {
    if (!this.newFolderTemplate || !this.newFolderProject) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Template Selected',
        detail: 'Please select a project and template first'
      });
      return;
    }
    
    this.editingTemplateId = this.newFolderTemplate.id;
    this.editingProjectId = this.newFolderProject._id?.$oid;
    this.templateEditorDialogVisible = true;
  }

  /**
   * Handle template editor save - refresh projects to get updated templates
   */
  onTemplateEditorSave(): void {
    if (this.userInfo?.projectList) {
      this.loadProjects(this.userInfo.projectList);
    }
    this.messageService.add({
      severity: 'success',
      summary: 'Template Updated',
      detail: 'The template has been updated successfully'
    });
  }

  /**
   * Cancel dialog
   */
  onClickDialogCancel(event: MouseEvent, dialog: string): void {
    if (dialog === 'newFolder') {
      this.newFolderDialogVisible = false;
    } else if (dialog === 'shareFolder') {
      this.shareDialogVisible = false;
    }
  }

  /**
   * Clear table filter
   */
  clear(table: Table): void {
    this.filterText = '';
    table.clear();
  }

  /**
   * Handle filter input
   */
  onInputFilter(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.table?.filterGlobal(value, 'contains');
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}

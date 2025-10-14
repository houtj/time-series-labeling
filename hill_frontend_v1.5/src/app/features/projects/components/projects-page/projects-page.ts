import { Component, OnInit, OnDestroy, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

// PrimeNG imports
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Dialog } from 'primeng/dialog';
import { Select } from 'primeng/select';
import { SpeedDial } from 'primeng/speeddial';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { Toast } from 'primeng/toast';
import { ColorPicker } from 'primeng/colorpicker';
import { TextareaModule } from 'primeng/textarea';
import { ConfirmationService, MessageService } from 'primeng/api';

// Core services and models
import { UserStateService } from '../../../../core/services';
import { ProjectsRepository, UsersRepository, TemplatesRepository } from '../../../../core/repositories';
import { ProjectModel, UserModel, TemplateModel } from '../../../../core/models';

// Feature components
import { TemplateEditorDialogComponent } from '../template-editor-dialog/template-editor-dialog';

@Component({
  selector: 'app-projects-page',
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
    ColorPicker,
    TextareaModule,
    TemplateEditorDialogComponent
  ],
  standalone: true,
  providers: [ConfirmationService, MessageService],
  templateUrl: './projects-page.html',
  styleUrl: './projects-page.scss'
})
export class ProjectsPageComponent implements OnInit, OnDestroy {
  // Inject services
  private readonly router = inject(Router);
  private readonly userState = inject(UserStateService);
  private readonly projectsRepo = inject(ProjectsRepository);
  private readonly usersRepo = inject(UsersRepository);
  private readonly templatesRepo = inject(TemplatesRepository);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly subscriptions = new Subscription();

  // Signals
  readonly projects = signal<ProjectModel[]>([]);
  readonly loading = signal(true);

  // Component state
  selectedProject?: ProjectModel;
  userInfo?: UserModel;
  
  // Classes
  classesList?: ProjectModel['classes'];
  addNewClassDialogVisible = false;
  updateClassDialogVisible = false;
  newClassName = '';
  newClassColor = '#000000';
  newClassDescription = '';
  updatingClassName = '';
  classDescriptionPlaceholder = 'Please describe the visual pattern of this event class. Include details about:\n• How measurements change at the start and end of the event\n• How measurements change during the event\n• Typical duration range of the event\n• Expected noise characteristics in the measurements\n• Sequential dependencies with other event classes';
  
  // Templates
  templateList?: ProjectModel['templates'];
  addNewTemplateDialogVisible = false;
  newTemplateName = '';
  fileTypesList = [{ name: '.xlsx' }, { name: '.xls' }, { name: '.csv' }];
  selectedFileType = { name: '.xlsx' };
  templateEditorDialogVisible = false;
  editingTemplateId?: string;
  
  // Project
  addNewProjectDialogVisible = false;
  newProjectName = '';
  
  // Share
  shareDialogVisible = false;
  usersList?: UserModel[];
  selectedUser?: UserModel;

  ngOnInit(): void {
    this.userState.updatePageTitle('Project Settings');
    this.loadUserAndProjects();
  }

  /**
   * Load user info and projects
   */
  private loadUserAndProjects(): void {
    this.loading.set(true);
    
    this.usersRepo.getUserInfo().subscribe({
      next: (user) => {
        this.userInfo = user;
        this.userState.setUserInfo(user);
        
        // Load projects if user has any
        if (user.projectList && user.projectList.length > 0) {
          this.loadProjects(user.projectList);
        } else {
          this.loading.set(false);
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
   * Load projects from backend
   */
  private loadProjects(projectIds: string[]): void {
    this.projectsRepo.getProjects(projectIds).subscribe({
      next: (projects) => {
        this.projects.set(projects);
        this.userState.setProjectList(projects);
        
        // Update selectedProject to the refreshed object
        if (this.selectedProject) {
          // Find the updated version of the currently selected project
          const updatedProject = projects.find(
            p => p._id?.$oid === this.selectedProject?._id?.$oid
          );
          if (updatedProject) {
            this.selectedProject = updatedProject;
            this.classesList = this.selectedProject.classes;
            this.templateList = this.selectedProject.templates;
          }
        } else if (projects.length > 0) {
          // Select first project by default if no project is selected
          this.selectedProject = projects[0];
          this.classesList = this.selectedProject.classes;
          this.templateList = this.selectedProject.templates;
        }
        
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load projects:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load projects'
        });
        this.loading.set(false);
      }
    });
  }

  /**
   * Handle project selection change
   */
  onChangeSelectedProject(event: any): void {
    this.classesList = this.selectedProject?.classes;
    this.templateList = this.selectedProject?.templates;
  }

  // ==================== PROJECT OPERATIONS ====================
  
  /**
   * Open/submit new project dialog
   */
  onClickAddNewProject(event: MouseEvent, isSubmit: boolean): void {
    if (!isSubmit) {
      this.newProjectName = '';
      this.addNewProjectDialogVisible = true;
    } else {
      if (!this.newProjectName || !this.userInfo) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Validation Error',
          detail: 'Please enter a project name'
        });
        return;
      }

      const data = {
        projectName: this.newProjectName,
        userId: this.userInfo._id?.$oid || ''
      };

      this.projectsRepo.createProject(data).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Project created successfully'
          });
          this.addNewProjectDialogVisible = false;
          this.loadUserAndProjects();
        },
        error: (error) => {
          console.error('Failed to create project:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create project'
          });
        }
      });
    }
  }

  /**
   * Share project with user
   */
  onClickShare(event: MouseEvent): void {
    this.usersRepo.getAllUsers().subscribe({
      next: (users) => {
        this.usersList = users;
        this.selectedUser = users[0];
        this.shareDialogVisible = true;
      },
      error: (error) => {
        console.error('Failed to load users:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load users'
        });
      }
    });
  }

  /**
   * Confirm share project
   */
  onClickShareOK(event: MouseEvent): void {
    if (!this.selectedProject || !this.selectedUser || !this.userInfo) {
      return;
    }

    const data = {
      project: this.selectedProject,
      user: this.selectedUser,
      userName: this.userInfo.name,
      message: ''
    };

    this.usersRepo.shareProjectWithUser(data).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Project shared successfully'
        });
        this.shareDialogVisible = false;
      },
      error: (error) => {
        console.error('Failed to share project:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to share project'
        });
        this.shareDialogVisible = false;
      }
    });
  }

  // ==================== CLASS OPERATIONS ====================
  
  /**
   * Open/submit new class dialog
   */
  onClickAddNewClass(event: MouseEvent, isSubmit: boolean): void {
    if (!isSubmit) {
      this.newClassName = '';
      this.newClassColor = '#000000';
      this.newClassDescription = '';
      this.addNewClassDialogVisible = true;
    } else {
      if (!this.newClassName || !this.selectedProject) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Validation Error',
          detail: 'Please enter a class name'
        });
        return;
      }

      const projectId = this.selectedProject._id?.$oid || '';
      const classData = {
        name: this.newClassName,
        color: this.newClassColor,
        description: this.newClassDescription
      };

      this.projectsRepo.addClass(projectId, classData).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Class created successfully'
          });
          this.addNewClassDialogVisible = false;
          this.loadUserAndProjects();
        },
        error: (error) => {
          console.error('Failed to create class:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create class'
          });
        }
      });
    }
  }

  /**
   * Open update class dialog
   */
  onClickUpdateClass(event: MouseEvent, class_: ProjectModel['classes'][0]): void {
    this.newClassName = class_.name;
    this.newClassColor = class_.color;
    this.newClassDescription = class_.description || '';
    this.updatingClassName = class_.name;
    this.updateClassDialogVisible = true;
  }

  /**
   * Submit class update
   */
  onClickUpdateClassOk(event: MouseEvent): void {
    if (!this.selectedProject) {
      return;
    }

    const projectId = this.selectedProject._id?.$oid || '';
    const className = this.updatingClassName;
    const updates = {
      newName: this.newClassName,
      color: this.newClassColor,
      description: this.newClassDescription
    };

    this.projectsRepo.updateClass(projectId, className, updates).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Class updated successfully'
        });
        this.updateClassDialogVisible = false;
        this.loadUserAndProjects();
      },
      error: (error) => {
        console.error('Failed to update class:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update class'
        });
      }
    });
  }

  /**
   * Refresh classes list
   */
  onClickRefreshClass(event: MouseEvent): void {
    this.loadUserAndProjects();
  }

  // ==================== TEMPLATE OPERATIONS ====================
  
  /**
   * Open/submit new template dialog
   */
  onClickAddNewTemplate(event: MouseEvent, isSubmit: boolean): void {
    if (!isSubmit) {
      this.newTemplateName = '';
      this.selectedFileType = { name: '.xlsx' };
      this.addNewTemplateDialogVisible = true;
    } else {
      if (!this.newTemplateName || !this.selectedProject) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Validation Error',
          detail: 'Please enter a template name'
        });
        return;
      }

      const data = {
        projectId: this.selectedProject._id?.$oid || '',
        templateName: this.newTemplateName,
        fileType: this.selectedFileType.name
      };

      this.templatesRepo.createTemplate(data).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Template created successfully'
          });
          this.addNewTemplateDialogVisible = false;
          this.loadUserAndProjects();
        },
        error: (error) => {
          console.error('Failed to create template:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to create template'
          });
        }
      });
    }
  }

  /**
   * Open template editor
   */
  onClickUpdateTemplate(event: MouseEvent, template: ProjectModel['templates'][0]): void {
    this.editingTemplateId = template.id;
    this.templateEditorDialogVisible = true;
  }

  /**
   * Handle template editor save
   */
  onTemplateEditorSave(): void {
    this.loadUserAndProjects();
  }

  /**
   * Refresh templates list
   */
  onClickRefreshTemplate(event: MouseEvent): void {
    this.loadUserAndProjects();
  }

  // ==================== DIALOG OPERATIONS ====================
  
  /**
   * Cancel dialog
   */
  onClickDialogCancel(event: MouseEvent, dialog: string): void {
    switch (dialog) {
      case 'newProject':
        this.addNewProjectDialogVisible = false;
        break;
      case 'newClass':
        this.addNewClassDialogVisible = false;
        break;
      case 'updateClass':
        this.updateClassDialogVisible = false;
        break;
      case 'newTemplate':
        this.addNewTemplateDialogVisible = false;
        break;
      case 'shareProject':
        this.shareDialogVisible = false;
        break;
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}

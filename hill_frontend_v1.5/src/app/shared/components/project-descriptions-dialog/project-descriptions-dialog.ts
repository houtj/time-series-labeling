import { Component, model, input, output, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports
import { Dialog } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { Textarea } from 'primeng/textarea';
import { Divider } from 'primeng/divider';
import { ScrollPanel } from 'primeng/scrollpanel';

// Services and Models
import { ProjectsRepository } from '../../../core/repositories/projects.repository';
import { ProjectModel } from '../../../core/models';
import { MessageService } from 'primeng/api';

/**
 * Project Descriptions Dialog Component
 * Allows editing of project general description and all class descriptions
 * Used on both project page and labeling page
 */
@Component({
  selector: 'app-project-descriptions-dialog',
  imports: [
    CommonModule,
    FormsModule,
    Dialog,
    ButtonModule,
    Textarea,
    Divider,
    ScrollPanel
  ],
  standalone: true,
  templateUrl: './project-descriptions-dialog.html',
  styleUrl: './project-descriptions-dialog.scss'
})
export class ProjectDescriptionsDialogComponent {
  private readonly projectsRepo = inject(ProjectsRepository);
  private readonly messageService = inject(MessageService);

  // Signals
  visible = model<boolean>(false);
  projectId = input<string | undefined>(undefined);
  projectName = input<string>('');
  classes = input<ProjectModel['classes']>([]);
  generalDescription = input<string>('');
  
  // Outputs
  onSave = output<void>();

  // Component state
  editingGeneralDescription = '';
  editingClassDescriptions: { name: string; color: string; description: string }[] = [];
  saving = false;

  constructor() {
    // Watch for dialog opening to load data
    effect(() => {
      const isVisible = this.visible();
      if (isVisible) {
        this.loadDescriptions();
      }
    });
  }

  /**
   * Load current descriptions into editing state
   */
  private loadDescriptions(): void {
    this.editingGeneralDescription = this.generalDescription() || '';
    this.editingClassDescriptions = (this.classes() || []).map(c => ({
      name: c.name,
      color: c.color,
      description: c.description || ''
    }));
  }

  /**
   * Handle save action
   */
  onClickSave(): void {
    const projectId = this.projectId();
    if (!projectId) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Project ID is required'
      });
      return;
    }

    this.saving = true;

    this.projectsRepo.updateProjectDescriptions(
      projectId,
      this.editingGeneralDescription,
      this.editingClassDescriptions
    ).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Project descriptions updated successfully'
        });
        this.onSave.emit();
        this.closeDialog();
      },
      error: (error) => {
        console.error('Failed to update descriptions:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update descriptions'
        });
      },
      complete: () => {
        this.saving = false;
      }
    });
  }

  /**
   * Handle cancel action
   */
  onClickCancel(): void {
    this.closeDialog();
  }

  /**
   * Close dialog
   */
  private closeDialog(): void {
    this.visible.set(false);
  }

  /**
   * Get placeholder text for general description
   */
  getGeneralDescriptionPlaceholder(): string {
    return 'Describe the overall context and purpose of this project.\n\n' +
           'Include:\n' +
           '• What types of data are being labeled\n' +
           '• The general patterns or phenomena of interest\n' +
           '• Any domain-specific context\n' +
           '• Overall goals of the labeling project';
  }

  /**
   * Get placeholder text for class description
   */
  getClassDescriptionPlaceholder(): string {
    return 'Describe the visual pattern of this event class.\n\n' +
           'Include:\n' +
           '• How measurements change at the start and end\n' +
           '• How measurements change during the event\n' +
           '• Typical duration range\n' +
           '• Expected noise characteristics\n' +
           '• Dependencies with other classes';
  }
}


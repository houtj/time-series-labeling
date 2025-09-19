import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ProjectModel } from '../model';
import { environment } from '../../environments/environment';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-description-dialog',
  templateUrl: './description-dialog.component.html',
  styleUrl: './description-dialog.component.scss'
})
export class DescriptionDialogComponent {
  private http = inject(HttpClient);
  private messageService = inject(MessageService);

  @Input() visible: boolean = false;
  @Input() project?: ProjectModel;
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() onSave = new EventEmitter<void>();

  public generalDescription: string = '';
  public classDescriptions: {name: string, description: string, color: string}[] = [];
  public loading: boolean = false;

  ngOnChanges() {
    if (this.visible && this.project) {
      this.loadDescriptions();
    }
  }

  loadDescriptions() {
    this.loading = true;
    this.generalDescription = this.project?.general_pattern_description || '';
    this.classDescriptions = this.project?.classes?.map(cls => ({
      name: cls.name,
      description: cls.description || '',
      color: cls.color
    })) || [];
    this.loading = false;
  }

  onConfirm() {
    if (!this.project) return;

    this.loading = true;
    
    const updateData = {
      projectId: this.project._id!.$oid,
      generalDescription: this.generalDescription,
      classDescriptions: this.classDescriptions
    };

    this.http.put<string>(`${environment.databaseUrl}/project-descriptions`, updateData).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success', 
          summary: 'Descriptions Updated', 
          detail: 'Project and class descriptions have been saved successfully.'
        });
        this.onSave.emit();
        this.onCancel();
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error', 
          summary: 'Update Failed', 
          detail: 'Failed to save descriptions. Please try again.'
        });
        this.loading = false;
      }
    });
  }

  onCancel() {
    this.visible = false;
    this.visibleChange.emit(false);
    this.loading = false;
  }

  getClassDescriptionPlaceholder(): string {
    return 'Describe the visual pattern of this event class:\n• How measurements change at start/end\n• How measurements change during the event\n• Typical duration range\n• Expected noise characteristics\n• Sequential dependencies with other events';
  }

  getGeneralDescriptionPlaceholder(): string {
    return 'Provide a general description of the project and its overall pattern recognition goals. Describe the context, objectives, and general characteristics of the events you are studying.';
  }
}

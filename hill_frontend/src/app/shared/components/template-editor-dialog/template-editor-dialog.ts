import { Component, effect, input, model, output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

// PrimeNG imports
import { Dialog } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Select } from 'primeng/select';
import { ColorPicker } from 'primeng/colorpicker';
import { Checkbox } from 'primeng/checkbox';
import { MessageService } from 'primeng/api';

// Core imports
import { TemplatesRepository } from '../../../core/repositories';
import { TemplateModel } from '../../../core/models';
import { environment } from '../../../../environments/environment';

/**
 * Template Editor Dialog Component
 * Advanced dialog for editing template channel configurations
 */
@Component({
  selector: 'app-template-editor-dialog',
  imports: [
    CommonModule,
    FormsModule,
    Dialog,
    ButtonModule,
    InputText,
    Select,
    ColorPicker,
    Checkbox
  ],
  standalone: true,
  templateUrl: './template-editor-dialog.html',
  styleUrl: './template-editor-dialog.scss'
})
export class TemplateEditorDialogComponent {
  // Two-way bindable signal for dialog visibility
  visible = model<boolean>(false);
  
  // Inputs using modern signal-based API
  templateId = input<string | undefined>(undefined);
  projectId = input<string | undefined>(undefined);
  
  // Outputs
  onSave = output<void>();

  // Inject services
  private readonly templatesRepo = inject(TemplatesRepository);
  private readonly messageService = inject(MessageService);
  private readonly http = inject(HttpClient);

  // Template data
  template?: TemplateModel;
  templateName = '';
  
  // File type options
  fileTypesList = [{ name: '.xlsx' }, { name: '.xls' }, { name: '.csv' }];
  selectedFileType = { name: '.xlsx' };

  constructor() {
    // Use effect to react to input changes - more declarative and cleaner than ngOnChanges
    effect(() => {
      const isVisible = this.visible();
      const id = this.templateId();
      
      // Load template when dialog becomes visible and has a templateId
      if (isVisible && id) {
        this.loadTemplate();
      }
    });
  }

  /**
   * Load template data
   */
  private loadTemplate(): void {
    const id = this.templateId();
    if (!id) return;

    this.templatesRepo.getTemplate(id).subscribe({
      next: (template) => {
        this.template = template;
        this.templateName = template.templateName || '';
        this.selectedFileType = { name: template.fileType || '.xlsx' };
      },
      error: (error) => {
        console.error('Failed to load template:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load template'
        });
      }
    });
  }

  /**
   * Add a new channel to the template
   */
  onClickAddChannel(event: MouseEvent): void {
    if (!this.template) return;

    if (this.template.channels.length >= 8) {
      this.messageService.add({
        severity: 'error',
        summary: 'Maximum Reached',
        detail: 'Support 8 channels maximum'
      });
      return;
    }

    const newChannel: TemplateModel['channels'][0] = {
      mandatory: true,
      channelName: '',
      regex: '',
      unit: '',
      color: this.getRandomColor()
    };

    this.template.channels.push(newChannel);
  }

  /**
   * Remove a channel from the template
   */
  onClickRemoveChannel(event: MouseEvent, index: number): void {
    if (!this.template) return;
    this.template.channels.splice(index, 1);
  }

  /**
   * Upload file to extract columns
   */
  onClickFromFile(event: MouseEvent): void {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    
    if (this.template?.fileType) {
      const fileType = this.template.fileType.startsWith('.') 
        ? this.template.fileType 
        : '.' + this.template.fileType;
      fileInput.accept = fileType;
    }
    
    fileInput.onchange = (event: any) => {
      const file = event.target.files[0];
      if (file) {
        this.uploadFileAndExtractColumns(file);
      }
    };
    
    fileInput.click();
  }

  /**
   * Upload file and extract columns
   */
  private uploadFileAndExtractColumns(file: File): void {
    if (!this.template) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('templateId', this.template._id?.$oid || '');

    this.http.post<any>(`${environment.apiUrl}/templates/extract-columns`, formData).subscribe({
      next: (response) => {
        // Check if backend returned an error object
        if (response.error) {
          console.error('Failed to extract columns:', response.error);
          this.messageService.add({
            severity: 'error',
            summary: 'File Processing Failed',
            detail: response.error
          });
          return;
        }
        
        this.autoMapColumnsToTemplate(response.columns);
        this.messageService.add({
          severity: 'success',
          summary: 'Columns Mapped',
          detail: `Automatically mapped ${response.columns.length} columns to template channels.`
        });
      },
      error: (error) => {
        console.error('Failed to extract columns:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'File Processing Failed',
          detail: 'Could not extract columns from the file. Please check the file format.'
        });
      }
    });
  }

  /**
   * Auto-map columns to template channels
   */
  private autoMapColumnsToTemplate(columns: any[]): void {
    if (!this.template) return;

    // Clear existing channels before auto-mapping
    this.template.channels = [];
    
    // Auto-map the first column to X-axis if no X-axis is configured
    const hasXAxisMapping = this.template.x.regex && this.template.x.regex.trim() !== '';
    if (columns.length > 0 && !hasXAxisMapping) {
      this.template.x.regex = columns[0].name;
      if (!this.template.x.name || this.template.x.name.trim() === '') {
        this.template.x.name = columns[0].name;
      }
    }
    
    // Auto-map all columns as channels (skip first if it was used for X-axis)
    const startIndex = hasXAxisMapping ? 0 : 1;
    
    for (let i = startIndex; i < columns.length && this.template.channels.length < 8; i++) {
      const column = columns[i];
      const newChannel: TemplateModel['channels'][0] = {
        mandatory: true,
        channelName: column.name,
        regex: column.name,
        unit: '',
        color: this.getRandomColor()
      };
      
      this.template.channels.push(newChannel);
    }
  }

  /**
   * Get random color for channels
   */
  private getRandomColor(): string {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  /**
   * Save template changes
   */
  onClickSave(event: MouseEvent): void {
    const projectId = this.projectId();
    if (!this.template || !projectId) return;

    // Update file type
    this.template.fileType = this.selectedFileType.name;

    this.templatesRepo.updateTemplate(projectId, this.template).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Template updated successfully'
        });
        this.closeDialog();
        this.onSave.emit();
      },
      error: (error) => {
        console.error('Failed to update template:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update template'
        });
      }
    });
  }

  /**
   * Close dialog
   */
  onClickCancel(event: MouseEvent): void {
    this.closeDialog();
  }

  private closeDialog(): void {
    this.visible.set(false);
  }
}

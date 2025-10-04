import { Component, EventEmitter, Input, Output, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpEventType } from '@angular/common/http';

// PrimeNG imports
import { FileUploadModule, FileUpload } from 'primeng/fileupload';
import { MessageService } from 'primeng/api';

// Core imports
import { environment } from '../../../../../environments/environment';

/**
 * File Upload Component
 * Reusable component for uploading files to a folder
 */
@Component({
  selector: 'app-file-upload',
  imports: [
    CommonModule,
    FileUploadModule
  ],
  standalone: true,
  templateUrl: './file-upload.html',
  styleUrl: './file-upload.scss'
})
export class FileUploadComponent {
  @ViewChild('fileUpload') fileUpload?: FileUpload;
  
  @Input() folderId?: string;
  @Input() userName?: string;
  @Output() uploadComplete = new EventEmitter<void>();
  @Output() uploadError = new EventEmitter<string>();

  // Inject services
  private readonly http = inject(HttpClient);
  private readonly messageService = inject(MessageService);

  uploadedFileNames: string[] = [];
  uploadProgress = 0;
  isUploading = false;

  /**
   * Handle file upload
   */
  onUploadHandler(event: any): void {
    if (!this.folderId || !this.userName) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Missing folder ID or user name'
      });
      return;
    }

    this.uploadedFileNames = event.files.map((f: File) => f.name);
    const formData = new FormData();
    formData.append('data', this.folderId);
    formData.append('user', this.userName);
    
    for (let file of event.files) {
      formData.append('files', file, file.name);
    }
    
    this.isUploading = true;
    this.uploadProgress = 0;
    
    this.http.post(`${environment.apiUrl}/files`, formData, {
      reportProgress: true,
      observe: 'events'
    }).subscribe({
      next: (res) => {
        if (res.type === HttpEventType.UploadProgress) {
          this.uploadProgress = Math.round(100 * res.loaded / (res.total || 1));
        }
        if (res.type === HttpEventType.Response) {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: `${this.uploadedFileNames.length} file(s) uploaded successfully`
          });
          this.isUploading = false;
          this.uploadComplete.emit();
          this.clear();
        }
      },
      error: (error) => {
        console.error('Failed to upload files:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to upload files'
        });
        this.isUploading = false;
        this.uploadError.emit(error.message || 'Upload failed');
      }
    });
  }

  /**
   * Clear the upload component
   */
  clear(): void {
    this.uploadedFileNames = [];
    this.uploadProgress = 0;
    this.fileUpload?.clear();
  }

  /**
   * Get upload status message
   */
  getStatusMessage(): string {
    if (this.isUploading) {
      return `Uploading... ${this.uploadProgress}%`;
    }
    if (this.uploadedFileNames.length > 0) {
      return `${this.uploadedFileNames.length} file(s) uploaded successfully`;
    }
    return 'Drag and drop files here or click to browse';
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
}

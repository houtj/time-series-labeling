import { Component, OnInit, OnDestroy, ViewChild, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { Subscription } from 'rxjs';

// PrimeNG imports
import { TableModule, Table } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputText } from 'primeng/inputtext';
import { Dialog } from 'primeng/dialog';
import { SpeedDial } from 'primeng/speeddial';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { Toast } from 'primeng/toast';
import { ConfirmationService, MessageService } from 'primeng/api';
import { FileUploadModule } from 'primeng/fileupload';

// Core imports
import { UserStateService } from '../../../../core/services';
import { FoldersRepository, FilesRepository, UsersRepository } from '../../../../core/repositories';
import { FileModel, FolderModel, UserModel } from '../../../../core/models';
import { environment } from '../../../../../environments/environment';

// Feature components
import { FileUploadComponent } from '../file-upload/file-upload';

// Shared components
import { ShareDialogComponent, DescriptionDialogComponent, TemplateEditorDialogComponent } from '../../../../shared/components';

@Component({
  selector: 'app-files-page',
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputText,
    Dialog,
    SpeedDial,
    ConfirmPopupModule,
    Toast,
    FileUploadComponent,
    ShareDialogComponent,
    DescriptionDialogComponent,
    TemplateEditorDialogComponent
  ],
  standalone: true,
  providers: [ConfirmationService, MessageService],
  templateUrl: './files-page.html',
  styleUrl: './files-page.scss'
})
export class FilesPageComponent implements OnInit, OnDestroy {
  @ViewChild('dt1') table?: Table;
  @ViewChild(FileUploadComponent) fileUploadComponent?: FileUploadComponent;

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly userState = inject(UserStateService);
  private readonly foldersRepo = inject(FoldersRepository);
  private readonly filesRepo = inject(FilesRepository);
  private readonly usersRepo = inject(UsersRepository);
  private readonly http = inject(HttpClient);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly subscriptions = new Subscription();

  readonly files = signal<FileModel[]>([]);
  readonly loading = signal(true);

  folderInfo?: FolderModel;
  userInfo?: UserModel;
  folderId?: string;
  uploadFileDialogVisible = false;
  uploadedFileNames: string[] = [];
  shareDialogVisible = false;
  usersList?: UserModel[];
  selectedUser?: UserModel;
  messageShared = '';
  descriptionDialogVisible = false;
  selectedFile?: FileModel;
  selectedFileDescription = '';
  downloadUri?: SafeUrl;
  downloadDialogVisible = false;
  templateEditorDialogVisible = false;
  editingTemplateId?: string;
  editingProjectId?: string;
  filterText = '';

  ngOnInit(): void {
    this.folderId = this.route.snapshot.paramMap.get('folderId') || undefined;
    if (this.folderId) {
      this.loadFolderAndFiles();
    } else {
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No folder ID provided' });
      this.router.navigate(['/folders']);
    }
    this.usersRepo.getUserInfo().subscribe({
      next: (user) => { this.userInfo = user; this.userState.setUserInfo(user); },
      error: (error) => console.error('Failed to load user info:', error)
    });
  }

  private loadFolderAndFiles(): void {
    if (!this.folderId) return;
    this.loading.set(true);
    this.foldersRepo.getFolder(this.folderId).subscribe({
      next: (folder) => {
        this.folderInfo = folder;
        this.userState.updatePageTitle(folder.name);
        if (folder.fileList && folder.fileList.length > 0) {
          this.loadFiles(folder.fileList);
        } else { this.files.set([]); this.loading.set(false); }
      },
      error: (error) => {
        console.error('Failed to load folder:', error);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load folder' });
        this.loading.set(false);
      }
    });
  }

  private loadFiles(fileIds: string[]): void {
    this.filesRepo.getFiles(fileIds).subscribe({
      next: (files) => { this.files.set(files); this.loading.set(false); },
      error: (error) => {
        console.error('Failed to load files:', error);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load files' });
        this.loading.set(false);
      }
    });
  }

  onClickFile(event: MouseEvent, file: FileModel): void {
    if (file.parsing === 'parsed') {
      this.router.navigate(['/labeling', file._id?.$oid], { queryParams: { folderId: this.folderId } });
    } else {
      this.messageService.add({ severity: 'warn', summary: 'File Not Parsed', detail: `${file.name} has not been parsed yet. Please refresh.` });
    }
  }

  onClickRemove(event: MouseEvent, file: FileModel): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure you want to remove this file?',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () => {
        this.filesRepo.deleteFile(file).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'File deleted' });
            this.loadFolderAndFiles();
          },
          error: (error) => {
            console.error('Failed to delete file:', error);
            this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete file' });
          }
        });
      }
    });
  }

  onClickEditDescription(event: MouseEvent, file: FileModel): void {
    this.selectedFile = file;
    this.selectedFileDescription = file.description || '';
    this.descriptionDialogVisible = true;
  }

  onSaveDescription(newDescription: string): void {
    if (!this.selectedFile || !this.userInfo) return;
    this.filesRepo.updateDescription(this.selectedFile._id?.$oid || '', newDescription, this.userInfo.name).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Description updated' });
        this.descriptionDialogVisible = false;
        this.loadFolderAndFiles();
      },
      error: (error) => {
        console.error('Failed to update description:', error);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to update description' });
      }
    });
  }

  onClickUploadFiles(event: MouseEvent): void {
    this.fileUploadComponent?.clear();
    this.uploadFileDialogVisible = true;
  }

  onUploadComplete(): void {
    this.loadFolderAndFiles();
    this.uploadFileDialogVisible = false;
  }

  onUploadError(error: string): void {
    console.error('Upload error:', error);
  }

  onClickShareFolder(event: MouseEvent): void {
    this.shareDialogVisible = true;
  }

  onClickEditTemplate(event: MouseEvent): void {
    if (!this.folderInfo?.template?.id) {
      this.messageService.add({
        severity: 'warn',
        summary: 'No Template',
        detail: 'This folder has no associated template'
      });
      return;
    }

    if (!this.folderInfo?.project?.id) {
      this.messageService.add({
        severity: 'error',
        summary: 'Project Not Found',
        detail: 'Unable to find the associated project'
      });
      return;
    }

    this.editingTemplateId = this.folderInfo.template.id;
    this.editingProjectId = this.folderInfo.project.id;
    this.templateEditorDialogVisible = true;
  }

  onTemplateEditorSave(): void {
    this.messageService.add({
      severity: 'success',
      summary: 'Template Updated',
      detail: 'The template has been updated successfully'
    });
    // Optionally reload folder info to get updated template data
    this.loadFolderAndFiles();
  }

  onShareFolder(event: { user: UserModel; message: string }): void {
    if (!this.folderInfo || !this.userInfo) return;
    const data = { folder: this.folderInfo, user: event.user, userName: this.userInfo.name, message: event.message };
    this.usersRepo.shareFolderWithUser(data).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Folder shared' });
        this.shareDialogVisible = false;
      },
      error: (error) => {
        console.error('Failed to share folder:', error);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to share folder' });
        this.shareDialogVisible = false;
      }
    });
  }

  onClickExportLabels(event: MouseEvent): void {
    if (!this.folderInfo) return;
    this.filesRepo.getFilesEvents(this.folderInfo._id?.$oid || '').subscribe({
      next: (response: any) => {
        const uri = this.sanitizer.bypassSecurityTrustUrl('data:text/json;charset=UTF-8,' + encodeURIComponent(JSON.stringify(response)));
        this.downloadUri = uri;
        this.downloadDialogVisible = true;
      },
      error: (error: any) => {
        console.error('Failed to export labels:', error);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to export labels' });
      }
    });
  }

  onClickImportLabels(event: MouseEvent): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'All existing labels will be replaced!',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () => { document.getElementById('fileImportInput')?.click(); }
    });
  }

  onChangeImportInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file && this.folderInfo && this.userInfo) {
      const formData = new FormData();
      formData.append('data', this.folderInfo._id?.$oid || '');
      formData.append('user', this.userInfo.name);
      formData.append('file', file, file.name);
      this.http.post(`${environment.apiUrl}/labels/events`, formData).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Labels imported' });
          this.loadFolderAndFiles();
        },
        error: (error) => {
          console.error('Failed to import labels:', error);
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to import labels' });
        }
      });
    }
  }

  onClickDownload(event: MouseEvent): void {
    if (!this.folderInfo) return;
    this.filesRepo.downloadJsonFiles(this.folderInfo._id?.$oid || '').subscribe({
      next: (response: string) => {
        const uri = this.sanitizer.bypassSecurityTrustUrl('data:text/json;charset=UTF-8,' + encodeURIComponent(response));
        this.downloadUri = uri;
        this.downloadDialogVisible = true;
      },
      error: (error: any) => {
        console.error('Failed to download files:', error);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to download files' });
      }
    });
  }

  onClickReparsing(event: Event): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure you want to reparse all files?',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () => {
        if (!this.folderInfo) return;
        this.filesRepo.reparseFiles(this.folderInfo._id?.$oid || '').subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Parsing restarted' });
            this.loadFolderAndFiles();
          },
          error: (error) => {
            console.error('Failed to reparse files:', error);
            this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to restart parsing' });
          }
        });
      }
    });
  }

  onClickRefresh(event: MouseEvent): void {
    this.loadFolderAndFiles();
    this.messageService.add({ severity: 'success', summary: 'Refreshed', detail: 'Folder synchronized' });
  }

  onClickParent(event: MouseEvent): void {
    this.router.navigate(['/folders']);
  }

  clear(table: Table): void {
    this.filterText = '';
    table.clear();
  }

  onInputFilter(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.table?.filterGlobal(value, 'contains');
  }

  onClickDialogCancel(event: MouseEvent, dialog: string): void {
    switch (dialog) {
      case 'shareFolder': this.shareDialogVisible = false; break;
      case 'uploadFileDialog': this.uploadFileDialogVisible = false; break;
      case 'description': this.descriptionDialogVisible = false; break;
      case 'download': this.downloadDialogVisible = false; break;
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}

import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';
import { environment } from '../../environments/environment';
import { DataModel, LabelModel, UserModel, FileModel, FolderModel, ProjectModel } from '../model';
import { DatabaseService } from '../database/database.service';

@Injectable({
  providedIn: 'root'
})
export class DialogService {

  constructor(
    private router: Router,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private http: HttpClient,
    private sanitizer: DomSanitizer,
    private databaseService: DatabaseService
  ) { }

  showRemoveEventsConfirmation(event: MouseEvent, callback: () => void): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure you want to remove all the events?',
      icon: 'pi pi-info-circle',
      accept: callback
    });
  }

  showRemoveGuidelinesConfirmation(event: MouseEvent, callback: () => void): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure you want to remove all the guidelines?',
      icon: 'pi pi-info-circle',
      accept: callback
    });
  }

  showNextFileConfirmation(event: MouseEvent, folderInfo: FolderModel, fileList: string[], index: number): void {
    if (index !== fileList.length - 1) {
      this.confirmationService.confirm({
        target: event.target as EventTarget,
        message: 'Are you sure you want to proceed? All the unsaved changes are disgarded!',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.router.navigate(['/labeling', { folderId: folderInfo._id!.$oid, fileId: fileList[index + 1] }]);
        }
      });
    } else {
      this.messageService.add({
        severity: 'warn',
        summary: 'The end',
        detail: 'No next file'
      });
    }
  }

  showPreviousFileConfirmation(event: MouseEvent, folderInfo: FolderModel, fileList: string[], index: number): void {
    if (index !== 0) {
      this.confirmationService.confirm({
        target: event.target as EventTarget,
        message: 'Are you sure you want to proceed? All the unsaved changes are disgarded!',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.router.navigate(['/labeling', { folderId: folderInfo._id!.$oid, fileId: fileList[index - 1] }]);
        }
      });
    } else {
      this.messageService.add({
        severity: 'warn',
        summary: 'The end',
        detail: 'No previous file'
      });
    }
  }

  showImportLabelConfirmation(event: MouseEvent): void {
    this.confirmationService.confirm({
      target: event.target!,
      message: 'All the current events will be replaced by the uploaded events',
      icon: 'pi pi-info-circle',
      accept: () => {
        document.getElementById('fileImportInput')?.click();
      }
    });
  }

  createDownloadUri(data: any): any {
    const json = JSON.stringify(data);
    return this.sanitizer.bypassSecurityTrustUrl("data:text/json;charset=UTF-8," + encodeURIComponent(json));
  }

  handleFileImport(event: Event, labelInfo: LabelModel, userInfo: UserModel, fileInfo: FileModel): void {
    const target = event.target as HTMLInputElement;
    const file: File = (target!.files as FileList)[0];
    if (file) {
      const formData: FormData = new FormData();
      formData.append('data', labelInfo?._id?.$oid!);
      formData.append('user', userInfo.name);
      formData.append('file', file, file.name);
      this.http.post(`${environment.databaseUrl}/event`, formData).subscribe(res => {
        this.databaseService.updateSelectedFile(fileInfo?._id?.$oid!);
      });
    }
  }

  saveLabel(labelInfo: LabelModel, userInfo: UserModel): void {
    this.http.put(`${environment.databaseUrl}/labels`, { label: labelInfo, user: userInfo.name }).subscribe(response => {
      this.messageService.add({
        severity: 'success',
        summary: 'Saved',
        detail: 'Your label has been saved'
      });
    });
  }

  loadUsers(callback: (users: UserModel[]) => void): void {
    this.http.get<string>(`${environment.databaseUrl}/users`).subscribe(users => {
      callback(JSON.parse(users));
    });
  }

  shareFolder(folderInfo: FolderModel, selectedUser: UserModel, userInfo: UserModel, message: string, onSuccess: () => void, onError: () => void): void {
    this.http.put<string>(`${environment.databaseUrl}/usersSharedFiles`, {
      folder: folderInfo,
      user: selectedUser,
      userName: userInfo.name,
      message: message
    }).subscribe(response => {
      this.messageService.add({ severity: 'success', summary: 'Folder Shared', detail: 'Folder Shared successfully' });
      onSuccess();
    }, error => {
      this.messageService.add({ severity: 'error', summary: 'Folder sharing failed.', detail: 'Folder sharing failed.' });
      onError();
    });
  }

  navigateToParent(folderId: string): void {
    this.router.navigate(['/files', { folderId: folderId }]);
  }

  createEvent(selectedClass: ProjectModel['classes'][0], description: string, startX: string|number, endX: string|number, userInfo: UserModel): LabelModel['events'][0] {
    return {
      className: selectedClass.name,
      color: selectedClass.color,
      description: description,
      start: startX,
      end: endX,
      hide: false,
      labeler: userInfo.name,
    };
  }
}

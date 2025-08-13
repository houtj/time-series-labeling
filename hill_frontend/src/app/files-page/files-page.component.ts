import { Component, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { FileModel, FolderModel, UserModel } from '../model';
import { ActivatedRoute, Router } from '@angular/router';
import { DatabaseService } from '../database/database.service';
import { HttpClient, HttpEventType, HttpParams } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { ConfirmationService, MessageService } from 'primeng/api';
import { FileBeforeUploadEvent, FileProgressEvent, FileSendEvent, FileUpload, FileUploadEvent, FileUploadHandlerEvent } from 'primeng/fileupload';
import { DomSanitizer } from '@angular/platform-browser';
import { Subscription } from 'rxjs';
import { Table } from 'primeng/table';

@Component({
  selector: 'app-files-page',
  templateUrl: './files-page.component.html',
  styleUrl: './files-page.component.scss'
})
export class FilesPageComponent implements OnInit, OnDestroy{

  @ViewChild('fileUpload') public fileUpload?: FileUpload
  @ViewChild('dt1') public table?: Table


  private route = inject(ActivatedRoute)
  private router = inject(Router)
  private databaseService = inject(DatabaseService)
  private http = inject(HttpClient)
  private messageService = inject(MessageService)
  private confirmationService = inject(ConfirmationService)
  private sanitizer = inject(DomSanitizer)
  private subscriptions = new Subscription()

  public filesList?: FileModel[]
  public folderInfo?: FolderModel
  public userInfo?: UserModel
  public shareDialogVisible: boolean=false;
  public usersList?: UserModel[]
  public selectedUser?: UserModel
  public messageShared?: string
  public uploadFileDialogVisible: boolean = false;
  public url = `${environment.databaseUrl}/files`
  public uploadedFileNames: string[] = []
  public selectedFile?: FileModel
  public selectedFileDescription: string = ''
  public descriptionDialogVisible: boolean = false;
  public downloadUri: any;
  public downloadDialogVisible: boolean=false;
  public filterText = ''


  ngOnInit(): void {
    this.databaseService.updatePageLabel('Files')
    const folderId = this.route.snapshot.paramMap.get('folderId')
    if (folderId!==undefined && folderId!==null){
      this.databaseService.updateSelectedFolder(folderId!)
    } else {
      this.databaseService.updateSelectedFolder('659c2360df5acff35f6da285')
    }
    this.subscriptions.add(
      this.databaseService.filesList$.subscribe(filesList=>{
        this.filesList = filesList
      })
    )
    
    this.subscriptions.add(
      this.databaseService.selectedFolder$.subscribe(folder=>{
        this.folderInfo = folder
        this.databaseService.updatePageTitle(this.folderInfo?.name!)
      })
    )
    
    this.subscriptions.add(
      this.databaseService.userInfo$.subscribe(user=>{
        this.userInfo = user
      })
    )
    
  }

  onClickExportLabels($event: MouseEvent) {
    this.http.get<string>(`${environment.databaseUrl}/files_event/${this.folderInfo?._id?.$oid!}`).subscribe(response=>{
      const json = response
      const uri = this.sanitizer.bypassSecurityTrustUrl("data:text/json;charset=UTF-8,"+encodeURIComponent(json))
      this.downloadUri = uri
      this.downloadDialogVisible = true
    })
  }

  onClickImportLabels($event: MouseEvent) {
    this.confirmationService.confirm({
      target: $event.target!,
      message: 'All the labels will be replaced by the uploaded labels!!!',
      icon: 'pi pi-info-circle',
      accept: ()=>{
        document.getElementById('fileImportInput')?.click() 
      }
    })
  }

  onClickUploadFiles($event: MouseEvent) {
    this.uploadedFileNames = []
    this.fileUpload!.clear()
    this.fileUpload!.progress = 0
    this.fileUpload!.uploading = false
    this.uploadFileDialogVisible = true
  }
  onClickRefresh($event: MouseEvent) {
    this.databaseService.updateSelectedFolder(this.folderInfo?._id!.$oid!)
    this.messageService.add({
      severity: 'success',
      summary: 'Refresh',
      detail: 'Folder information has been successfully synchronized with database.'
    })
  }
  onClickRemove($event: MouseEvent, file: FileModel) {
    
    this.confirmationService.confirm({
      target: event?.target as EventTarget,
      message:'Are you sure you want to remove the file?',
      icon: 'pi pi-info-circle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () =>{
        const params = new HttpParams({fromObject: {file: JSON.stringify(file)}})
        this.http.delete(`${environment.databaseUrl}/files`, {params: params}).subscribe(response=>{
          this.databaseService.updateSelectedFolder(this.folderInfo!._id!.$oid)
          this.messageService.add({severity: 'success', summary: 'File Deleted', detail: 'File deleted successfully'})
        })
      },
      reject: () =>{
      }
    })
    
  }

  onClickDialogCancel($event: MouseEvent, dialog: string) {
    switch (dialog) {
      case 'shareFolder':
        this.shareDialogVisible = false
        break
      case 'uploadFileDialog':
        this.uploadFileDialogVisible = false
        break
      case 'description':
        this.descriptionDialogVisible = false
        break
    }
  }

  onClickShareFolder($event: MouseEvent) {
    this.http.get<string>(`${environment.databaseUrl}/users`).subscribe(users=>{
      this.shareDialogVisible = true
      this.usersList = JSON.parse(users)
      this.selectedUser = this.usersList![0]
    })
  }

  onClickShareOK($event: MouseEvent) {
    if (this.messageShared===undefined){
      this.messageShared = ''
    }
    this.http.put<string>(`${environment.databaseUrl}/usersSharedFolders`, {folder: this.folderInfo, user: this.selectedUser, userName: this.userInfo!.name, message: this.messageShared}).subscribe(response=>{
      this.shareDialogVisible = false
      this.messageService.add({severity: 'success', summary: 'Folder Shared', detail: 'Folder Shared successfully'})
    }, error=>{
      this.shareDialogVisible = false
      this.messageService.add({severity:'error', summary:'Folder sharing failed.', detail:'Folder sharing failed.'})
    })
  }

  onFileUploadClick($event: FileUploadHandlerEvent) {
    this.uploadedFileNames = $event.files.map(f=>f.name)
    const formData: FormData = new FormData()
    formData.append('data', this.folderInfo?._id?.$oid!)
    formData.append('user', this.userInfo!.name)
    for (let file of $event.files){
      formData.append('files', file, file.name)
    }
    this.fileUpload!.uploading=true
    this.http.post(`${environment.databaseUrl}/files`, formData, {reportProgress: true, observe: 'events'}).subscribe(res=>{
      if (res.type === HttpEventType.UploadProgress) {
        const percentDone = Math.round(100*res.loaded/res.total!)
        this.fileUpload!.progress=percentDone
      }
      if (res.type === HttpEventType.Response){
        this.databaseService.updateSelectedFolder(this.folderInfo?._id!.$oid!)
        this.fileUpload?.clear()
      }
    })
  }

  onClickEditDescription($event: MouseEvent, file: FileModel) {
    this.selectedFile = file
    this.selectedFileDescription = this.selectedFile!.description
    this.descriptionDialogVisible = true
  }

  onClickFile($event: MouseEvent,file: FileModel) {
    if (file.parsing === 'parsed'){
      this.router.navigate(['/labeling', {folderId: this.folderInfo?._id?.$oid!, fileId: file._id?.$oid!}])
    } else {
      this.messageService.add({
        severity: 'error',
        summary: 'File not parsed',
        detail: `${file.name} has not been parsed yet. Please click on the refresh button to get the lastest update of the parsing status. If error happens, please contact the administrator.`
      })
    }
  }
  onClickDownload($event: MouseEvent) {
    this.http.get<string>(`${environment.databaseUrl}/files_data/${this.folderInfo?._id?.$oid!}`).subscribe(response=>{
      const json = response
      const uri = this.sanitizer.bypassSecurityTrustUrl("data:text/json;charset=UTF-8,"+encodeURIComponent(json))
      this.downloadUri = uri
      this.downloadDialogVisible = true
    })
  }

  onClickParent($event: MouseEvent) {
    this.router.navigate(['/folders'])
  }

  onClickEditDescriptionOK($event: MouseEvent) {
    this.descriptionDialogVisible = false
    this.http.put(`${environment.databaseUrl}/descriptions`, {file_id: this.selectedFile?._id?.$oid!, description: this.selectedFileDescription!}).subscribe(response=>{
      this.databaseService.updateSelectedFolder(this.folderInfo?._id?.$oid!)
    })
  }

  onChangeImportInput($event: Event) {
    const target = $event.target as HTMLInputElement
    const file:File = (target!.files as FileList)[0]
    if (file){
      const formData: FormData = new FormData()
      formData.append('data', this.folderInfo?._id?.$oid!)
      formData.append('user', this.userInfo!.name)
      formData.append('file', file, file.name)
      this.http.post(`${environment.databaseUrl}/events`, formData).subscribe(res=>{
        this.databaseService.updateSelectedFolder(this.folderInfo?._id?.$oid!)
      })
    }  
  }

  clear(table: Table) {
    this.filterText = ''
    table.clear();
  }

  onInputFilter($event: Event){
    this.table!.filterGlobal(($event.target as HTMLInputElement).value, 'contains')
  }

  onClickReparsing($event: Event){
    this.confirmationService.confirm({
      target: event?.target as EventTarget,
      message:'Are you sure you want to reparse all the files?',
      icon: 'pi pi-info-circle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () =>{
        this.http.put(`${environment.databaseUrl}/reparsingFiles`, {folderId: this.folderInfo!._id!.$oid}).subscribe(response=>{
          this.databaseService.updateSelectedFolder(this.folderInfo!._id!.$oid)
          this.messageService.add({severity: 'success', summary: 'Restart parsing', detail: 'Parsing restarted. Please wait for the parsing to be done'})
        }, err=>{
          this.messageService.add({severity: 'error', summary: 'Restart parsing failed', detail: 'Parsing cannot be restarted. Please contact the admin.'})
        })
      },
      reject: () =>{
      }
    })
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe()
  }
}

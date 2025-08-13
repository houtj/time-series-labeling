import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { environment } from '../../environments/environment';
import { DatabaseService } from '../database/database.service';
import { FolderModel, ProjectModel, UserModel } from '../model';
import { DropdownChangeEvent } from 'primeng/dropdown';
import { Router } from '@angular/router';
import { Table } from 'primeng/table';
import { ConfirmationService, MessageService } from 'primeng/api';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-folders-page',
  templateUrl: './folders-page.component.html',
  styleUrl: './folders-page.component.scss'
})
export class FoldersPageComponent implements OnInit,OnDestroy {
  @ViewChild('dt1') public table?: Table

  private http = inject(HttpClient)
  private databaseService = inject(DatabaseService)
  private router = inject(Router)
  private messageService = inject(MessageService)
  private confirmationService = inject(ConfirmationService)
  private subscriptions = new Subscription()

  public newFolderDialogVisible: boolean = false
  public newFolderName?: string
  public userInfo?: UserModel
  public folderList?: FolderModel[]
  public projectList?: ProjectModel[]
  public templateList?: ProjectModel['templates']
  public newFolderProject?: ProjectModel
  public newFolderTemplate?: ProjectModel['templates'][0]
  public shareDialogVisible: boolean = false
  public usersList?: UserModel[]
  public selectedUser?: UserModel
  public selectedFolder?: FolderModel
  public filterText = ''

  ngOnInit(): void {
    this.databaseService.updatePageLabel('Folders')
    this.databaseService.updatePageTitle('Folder Overview')
    this.subscriptions.add(
      this.databaseService.userInfo$.subscribe(userInfo=>{
        this.userInfo = userInfo
      })
    )
    this.subscriptions.add(
      this.databaseService.folderList$.subscribe(folders=>{
        this.folderList = folders
      })
    )
    
  }

  onClickNewFolder($event: MouseEvent, dialog:boolean){
    if (dialog===false) {
      this.newFolderName = ''
      this.projectList = this.databaseService.projectList
      if (this.projectList!==undefined && this.projectList.length>0){
        this.newFolderProject = this.projectList[0]
        this.templateList = this.projectList![0].templates
        if (this.templateList!==undefined && this.templateList.length>0){
          this.newFolderTemplate = this.templateList[0]
        }
      }
      this.newFolderDialogVisible = true
    } else {
      const options = {
        newFolderName: this.newFolderName,
        project: {id: this.newFolderProject?._id?.$oid, name:this.newFolderProject?.projectName},
        template: {id: this.newFolderTemplate?.id, name: this.newFolderTemplate?.name},
        userId: this.userInfo!._id!.$oid
      }
      this.http.post<string>(`${environment.databaseUrl}/folders`, options).subscribe(response=>{
        this.databaseService.updateSelectedUser()
        this.newFolderDialogVisible = false
      })
    }
  }

  onChangeSelectedProject($event: DropdownChangeEvent) {
    this.templateList = this.newFolderProject?.templates
    if (this.templateList!==undefined && this.templateList.length>0){
      this.newFolderTemplate = this.templateList[0]
    }
  }

  onClickDialogCancel($event: MouseEvent, dialog: string) {
    switch (dialog) {
      case 'newFolder':
        this.newFolderDialogVisible = false
        break
      case 'shareFolder':
        this.shareDialogVisible = false
        break
    }
  }

  onClickManagement($event: MouseEvent) {
    this.router.navigate(['/projects'])
  }

  onClickRemove($event: MouseEvent, folder: FolderModel) {
    this.confirmationService.confirm({
      target: event?.target as EventTarget,
      message:'Are you sure you want to remove the folder? All the files in the folder will be lost,',
      icon: 'pi pi-info-circle',
      acceptButtonStyleClass: 'p-button-danger p-button-sm',
      accept: () =>{
        const params = new HttpParams({fromObject:{folder: JSON.stringify(folder)}})
        this.http.delete<string>(`${environment.databaseUrl}/folders`,{params:params}).subscribe(response=>{
          this.messageService.add({severity: 'success', summary: 'Folder Deleted', detail: 'Folder deleted successfully'})
        })
      },
      reject: () =>{
      }
    })
  }

  onClickShare($event: MouseEvent, folder: FolderModel) {
    this.http.get<string>(`${environment.databaseUrl}/users`).subscribe(users=>{
      this.shareDialogVisible = true
      this.usersList = JSON.parse(users)
      this.selectedUser = this.usersList![0]
      this.selectedFolder = folder
    })
  }

  onClickShareOK($event: MouseEvent) {
    this.http.put<string>(`${environment.databaseUrl}/usersSharedFolders`, {folder: this.selectedFolder, user: this.selectedUser, userName: this.userInfo?.name, message:''}).subscribe(response=>{
      this.shareDialogVisible = false
      this.messageService.add({severity: 'success', summary: 'Folder Shared', detail: 'Folder Shared successfully'})
    }, error=>{
      this.shareDialogVisible = false
      this.messageService.add({severity: 'error', summary: 'Folder sharing failed', detail: 'Folder sharing failed'})
    })
  }

  onClickFolder($event: MouseEvent, folder: FolderModel) {
    this.router.navigate(['/files', {folderId: folder._id?.$oid}])  
  }

  onClickRefresh($event: MouseEvent) {
    this.databaseService.updateSelectedUser()
    this.messageService.add({
      severity: 'success',
      summary: 'Refresh',
      detail: 'Folders information has been successfully synchronized with database.'
    })
  }

  clear(table: Table) {
    this.filterText = ''
    table.clear();
  }

  onInputFilter($event: Event){
    this.table!.filterGlobal(($event.target as HTMLInputElement).value, 'contains')
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe()
  }
}

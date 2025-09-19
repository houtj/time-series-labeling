import { HttpClient, HttpParams } from '@angular/common/http';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { DatabaseService } from '../database/database.service';
import { Subscription, filter } from 'rxjs';
import { ProjectModel, TemplateModel, UserModel } from '../model';
import { ActivatedRoute, Router } from '@angular/router';
import { environment } from '../../environments/environment';
import { DropdownChangeEvent } from 'primeng/dropdown';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-project-page',
  templateUrl: './project-page.component.html',
  styleUrl: './project-page.component.scss'
})
export class ProjectPageComponent implements OnInit, OnDestroy {


  private http = inject(HttpClient)
  private databaseService = inject(DatabaseService)
  private route = inject(ActivatedRoute)
  private router = inject(Router)
  private messageService = inject(MessageService)
  private subscriptions = new Subscription()

  public projectList!: ProjectModel[]
  public selectedProject?: ProjectModel
  public classesList?: ProjectModel['classes']
  public templateList?: ProjectModel['templates']
  public addNewClassDialogVisible: boolean = false;
  public newClassName: string = '';
  public newClassColor: string = '#000000';
  public addNewTemplateDialogVisible: boolean = false;
  public newTemplateName?: string;
  public addNewProjectDialogVisible: boolean = false;
  public newProjectName?: string;
  public updateClassDialogVisible: boolean = false;
  public updatingClassName?: string
  public fileTypesList = [{'name': '.xlsx'},{'name': '.xls'}, {'name': '.csv'}];
  public selectedFileType?:{'name': string};
  public template?: TemplateModel
  public updatingTemplateName?: string;
  public updatingTemplateDialogVisible: boolean = false;
  public cloneDialogVisible: boolean = false;
  public cloningTemplateId: string = ''
  public shareDialogVisible:boolean = false
  public usersList?: UserModel[]
  public selectedUser?: UserModel
  public userInfo?: UserModel


  ngOnInit(): void {
    this.databaseService.updatePageLabel('Project')
    this.databaseService.updatePageTitle('Project Setting')
    const routeProjectId = this.route.snapshot.paramMap.get('projectId')
    this.subscriptions.add(
      this.databaseService.userInfo$.subscribe(userInfo=>{
        this.userInfo = userInfo
      })
    )
    this.subscriptions.add(
      this.databaseService.projectList$.pipe(
        filter(x=>x!==undefined)
      ).subscribe(projectsInfo=>{
        this.projectList = projectsInfo!
        // page init
        if (this.projectList!==undefined && this.projectList.length>0 && this.selectedProject===undefined){
          if (routeProjectId!==undefined){
            this.selectedProject = this.projectList[0]
          } else {
            this.selectedProject = this.projectList.find(project=>project._id!.$oid===routeProjectId)
          }
          this.classesList = this.selectedProject!.classes
          this.templateList = this.selectedProject!.templates
        }
        else if (this.selectedProject!==undefined){
          this.selectedProject = this.projectList.find(project=>project._id!.$oid===this.selectedProject?._id?.$oid)
          this.classesList = this.selectedProject?.classes
          this.templateList = this.selectedProject?.templates
        }
      })
    )
    
  }

  onClickRefreshClass($event: MouseEvent) {
    this.databaseService.updateSelectedUser()
  }

  onClickRefreshTemplate($event: MouseEvent) {
    this.databaseService.updateSelectedUser()
  }

  onClickAddNewProejct($event: MouseEvent, dialog: boolean) {
    if (dialog===false){
      this.addNewProjectDialogVisible = true
    } else {
      console.log(this.userInfo!._id!.$oid!)
      this.http.post<string>(`${environment.databaseUrl}/projects`, {projectName: this.newProjectName, userId: this.userInfo!._id!.$oid!}).subscribe(response=>{
        this.databaseService.updateSelectedUser()
        this.addNewProjectDialogVisible = false
      })
    }
  }

  onChangeSelectedProject($event: DropdownChangeEvent) {
    this.templateList = this.selectedProject!.templates
    this.classesList = this.selectedProject!.classes
  }

  onClickAddNewClass($event: MouseEvent, dialog: boolean) {
    if (dialog===false){
      this.addNewClassDialogVisible = true
      this.newClassName = ''
      this.newClassColor = '#000000'
    } else {
      const newClass = {
        newClassName: this.newClassName, 
        newClassColor: this.newClassColor,
        projectId: this.selectedProject!._id!.$oid
      }
      this.http.post<string>(`${environment.databaseUrl}/classes`, newClass).subscribe(response=>{
        this.addNewClassDialogVisible = false
        this.databaseService.updateSelectedUser()
      })
    }
  }
  
  onClickAddNewTemplate($event: MouseEvent, dialog: boolean) {
    if (dialog===false){ 
      this.addNewTemplateDialogVisible = true
      this.newTemplateName = ''
      this.selectedFileType={'name': 'xlsx'}
    } else {
      const newTemplate = {
        projectId: this.selectedProject?._id?.$oid,
        templateName: this.newTemplateName!,
        fileType: this.selectedFileType!.name
      }
      this.http.post<string>(`${environment.databaseUrl}/templates`, newTemplate).subscribe(response=>{
        this.addNewTemplateDialogVisible = false
        this.databaseService.updateSelectedUser()
      })
    }
  }

  onClickUpdateClass($event: MouseEvent, class_: ProjectModel['classes'][0]) {
    this.newClassName = class_.name
    this.newClassColor = class_.color
    this.updatingClassName = class_.name
    this.updateClassDialogVisible = true
  }

  onClickUpdateClassOk($event: MouseEvent) {
    const options = {
      updatingClassName: this.updatingClassName,
      newClassName: this.newClassName,
      newClassColor: this.newClassColor,
      projectId: this.selectedProject!._id!.$oid
    }
    this.http.put<string>(`${environment.databaseUrl}/classes`, options).subscribe(response=>{
      this.updateClassDialogVisible = false
      this.databaseService.updateSelectedUser()
    }, error=>{
      this.messageService.add({severity: 'error', summary: 'Failed modifying class', detail: 'Failed modifying class. Please contact us.'})
    })
  }

  onClickUpdateTemplate($event: MouseEvent, template: ProjectModel['templates'][0]) {
    this.updatingTemplateName = template.name
    this.newTemplateName = template.name
    this.http.get<string>(`${environment.databaseUrl}/templates/${template.id}`).subscribe(response=>{
      this.template = JSON.parse(response)
      this.selectedFileType = {'name': this.template!.fileType!}
      this.updatingTemplateDialogVisible = true
    })
  }

  onClickUpdateTemplateOk($event: MouseEvent) {
    this.template!.fileType = this.selectedFileType!.name
    this.http.put<string>(`${environment.databaseUrl}/templates`, {request: this.template, projectId: this.selectedProject!._id!.$oid}).subscribe(response=>{
      this.updatingTemplateDialogVisible=false
      this.databaseService.updateSelectedUser()
    })
  }

  onClickDialogCancel($event: MouseEvent, dialog: string) {
    switch (dialog){
      case 'updateTemplate':
        this.updatingTemplateDialogVisible = false
        break
      case 'updateClass':
        this.updateClassDialogVisible = false
        break
      case 'newTemplate':
        this.addNewTemplateDialogVisible = false
        break
      case 'newClass':
        this.addNewClassDialogVisible = false
        break
      case 'newProject':
        this.addNewProjectDialogVisible = false
        break
      case 'shareProject':
        this.shareDialogVisible = false
        this.selectedUser = undefined
        break
      case 'cloneTemplate':
        this.newTemplateName = ''
        this.cloningTemplateId =''
        this.updatingTemplateName = ''
        this.cloneDialogVisible = false
        break
    }
    }

  onClickAddChannel($event: MouseEvent) {
    if (this.template!.channels.length>=8) {
      this.messageService.add({severity:'error', summary:'Failed adding channel', detail: 'Support 8 channels maximum'})
    } else {
      const newRule:TemplateModel['channels'][0] = {
        mandatory: true,
        channelName: '',
        regex: '',
        unit: '',
        color: '#000000',
      }
      this.template!.channels.push(newRule)
    }
  }

  onClickRemoveChannel($event: MouseEvent, index: number){
    this.template!.channels.splice(index, 1)
  }

  onClickFromFile($event: MouseEvent) {
    // Create file input element programmatically
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    
    // Set accepted file types based on template file type
    if (this.template?.fileType) {
      const fileType = this.template.fileType.startsWith('.') ? this.template.fileType : '.' + this.template.fileType;
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

  uploadFileAndExtractColumns(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('templateId', this.template!._id!.$oid);

    this.http.post<any>(`${environment.databaseUrl}/extract-columns`, formData).subscribe(
      response => {
        this.autoMapColumnsToTemplate(response.columns);
        this.messageService.add({
          severity: 'success', 
          summary: 'Columns Mapped', 
          detail: `Automatically mapped ${response.columns.length} columns to template channels.`
        });
      },
      error => {
        this.messageService.add({
          severity: 'error', 
          summary: 'File Processing Failed', 
          detail: 'Could not extract columns from the file. Please check the file format.'
        });
      }
    );
  }

  autoMapColumnsToTemplate(columns: any[]) {
    // Clear existing channels before auto-mapping
    this.template!.channels = [];
    
    // Auto-map the first column to X-axis if no X-axis is configured
    const hasXAxisMapping = this.template!.x.regex && this.template!.x.regex.trim() !== '';
    if (columns.length > 0 && !hasXAxisMapping) {
      this.template!.x.regex = columns[0].name;
      if (!this.template!.x.name || this.template!.x.name.trim() === '') {
        this.template!.x.name = columns[0].name;
      }
    }
    
    // Auto-map all columns as channels (skip first if it was used for X-axis)
    const startIndex = hasXAxisMapping ? 0 : 1;
    
    for (let i = startIndex; i < columns.length && this.template!.channels.length < 8; i++) {
      const column = columns[i];
      const newChannel: TemplateModel['channels'][0] = {
        mandatory: true,
        channelName: column.name,
        regex: column.name,
        unit: '',
        color: this.getRandomColor(),
      };
      
      this.template!.channels.push(newChannel);
    }
  }

  getRandomColor(): string {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  onClickClone($event: MouseEvent, template: ProjectModel['templates'][0]) {
    this.updatingTemplateName = template.name
    this.newTemplateName = template.name
    this.cloningTemplateId = template.id
    this.cloneDialogVisible=true
  }

  onClickCloneDialogOk($event: MouseEvent) {
    this.http.put<string>(`${environment.databaseUrl}/templates_clone`, {newTemplateName: this.newTemplateName, projectId: this.selectedProject!._id!.$oid, templateId: this.cloningTemplateId}).subscribe(res=>{
      this.databaseService.updateSelectedUser()
    }, error=>{
      
    }).add(()=>{
      this.cloningTemplateId = ''
      this.cloneDialogVisible = false
      this.newTemplateName = ''
      this.updatingTemplateName = ''
    })
  }
  
  ngOnDestroy(): void {
    this.subscriptions.unsubscribe()
  }

  onClickShare($event: MouseEvent){
    this.http.get<string>(`${environment.databaseUrl}/users`).subscribe(users=>{
      this.shareDialogVisible = true
      this.usersList = JSON.parse(users)
      this.selectedUser = this.usersList![0]
    })
  }

  onClickShareOK($event: MouseEvent){
    this.http.put<string>(`${environment.databaseUrl}/usersSharedProjects`, {project: this.selectedProject, user: this.selectedUser, userName: this.userInfo?.name, message:''}).subscribe(response=>{
      this.shareDialogVisible = false
      this.messageService.add({severity: 'success', summary: 'Project Shared', detail: 'Folder Shared successfully'})
    }, error=>{
      this.shareDialogVisible = false
      this.messageService.add({severity: 'error', summary: 'Project sharing failed', detail: 'Folder sharing failed'})
    })
  }
}

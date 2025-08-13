import { Injectable, inject } from '@angular/core';
import { DataModel, FileModel, FolderModel, LabelModel, ProjectModel, UserModel, UserProfile } from '../model';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { BehaviorSubject, Observable, combineLatest, filter, switchMap, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DatabaseService {
  private http = inject(HttpClient)

  public pageTitle$ = new BehaviorSubject<string|undefined>(undefined)
  public pageLabel$ = new BehaviorSubject<string|undefined>(undefined)
  public userProfile?: UserProfile
  public userInfo?: UserModel
  public userInfo$ = new BehaviorSubject<UserModel|undefined>(undefined)
  public projectList$ = new BehaviorSubject<ProjectModel[]|undefined>(undefined)
  public projectList?: ProjectModel[]
  public folderList?: FolderModel[]
  public folderList$ = new BehaviorSubject<FolderModel[]|undefined>(undefined)
  public filesList?: FileModel[]
  public filesList$ = new BehaviorSubject<FileModel[]|undefined>(undefined)
  public selectedFolder?: FolderModel
  public selectedFolder$ = new BehaviorSubject<FolderModel|undefined>(undefined)
  public selectedFile?: FileModel
  public selectedFile$ = new BehaviorSubject<FileModel|undefined>(undefined)
  public selectedLabel?: LabelModel
  public selectedLabel$ = new BehaviorSubject<LabelModel|undefined>(undefined)
  public data$ = new BehaviorSubject<DataModel[]|undefined>(undefined)

  constructor() { }
  public updatePageTitle(pageTitle:string){
    this.pageTitle$.next(pageTitle)
  }
  public updatePageLabel(pageLabel:string){
    this.pageLabel$.next(pageLabel)
  }
  public updateSelectedUser(){
    // const params = new HttpParams({fromObject:{mail: this.userProfile!.mail!, name: this.userProfile!.displayName!}})
    this.http.get<string>(`${environment.databaseUrl}/userInfo`).pipe(
      tap(data=>{
        console.log('login as default')
        this.userInfo = JSON.parse(data)
        this.userInfo$.next(this.userInfo)
      }),
      switchMap(data=>{
        const folderList = this.userInfo!.folderList
        const projectList = this.userInfo!.projectList
        console.log(this.userInfo)
        const folderParams = new HttpParams({fromObject: {folders: JSON.stringify(folderList)}})
        const projectParams = new HttpParams({fromObject: {projects: JSON.stringify(projectList)}})
        return combineLatest([
          this.http.get<string>(`${environment.databaseUrl}/folders`, {params: folderParams}),
          this.http.get<string>(`${environment.databaseUrl}/projects`, {params: projectParams})
        ])
      })
    ).subscribe(data=>{
      console.log(data)
      const folders = data[0]
      const projects = data[1]
      this.folderList = JSON.parse(folders)
      this.folderList$.next(this.folderList)
      this.projectList = JSON.parse(projects)
      this.projectList$.next(this.projectList) 
    })
    // this.http.get<string>(`${environment.databaseUrl}/userInfo`, {params: params}).pipe(
    //   tap(data=>{
    //     this.userInfo = JSON.parse(data)
    //     this.userInfo$.next(this.userInfo)
    //   }),
    //   switchMap(data=>{
    //     const folderList = this.userInfo!.folderList
    //     const projectList = this.userInfo!.projectList
    //     console.log(this.userInfo)
    //     const folderParams = new HttpParams({fromObject: {folders: JSON.stringify(folderList)}})
    //     const projectParams = new HttpParams({fromObject: {projects: JSON.stringify(projectList)}})
    //     return combineLatest([
    //       this.http.get<string>(`${environment.databaseUrl}/folders`, {params: folderParams}),
    //       this.http.get<string>(`${environment.databaseUrl}/projects`, {params: projectParams})
    //     ])
    //   })
    // ).subscribe(data=>{
    //   console.log(data)
    //   const folders = data[0]
    //   const projects = data[1]
    //   this.folderList = JSON.parse(folders)
    //   this.folderList$.next(this.folderList)
    //   this.projectList = JSON.parse(projects)
    //   this.projectList$.next(this.projectList) 
    // })
  }


  public updateSelectedFolder(selectedFolderId: string){
    this.http.get<string>(`${environment.databaseUrl}/folders/${selectedFolderId}`).pipe(
      tap(response=>{
        this.selectedFolder = JSON.parse(response)
        this.selectedFolder$.next(this.selectedFolder)
      }),
      switchMap(response=>{
        const filesId = this.selectedFolder!.fileList
        const params = new HttpParams({fromObject: {filesId: JSON.stringify(filesId)}})
        return this.http.get<string>(`${environment.databaseUrl}/files`, {params: params})
      }),
      tap(response=>{
        this.filesList = JSON.parse(response)
        this.filesList$.next(this.filesList)
      })
    ).subscribe()
  }

  public updateSelectedFile(selectedFileId: string){
    this.http.get<string>(`${environment.databaseUrl}/files/${selectedFileId}`).pipe(
      tap(response=>{
        const resp = JSON.parse(response)
        const fileInfoResp = resp.fileInfo
        const dataResp = resp.data
        this.selectedFile = JSON.parse(fileInfoResp)
        this.selectedFile$.next(this.selectedFile)
        this.data$.next(JSON.parse(dataResp))
      }),
      switchMap(response=>{
        const labelId = this.selectedFile!.label
        return this.http.get<string>(`${environment.databaseUrl}/labels/${labelId}`)
      }),
      tap(response=>{
        this.selectedLabel = JSON.parse(response)
        this.selectedLabel$.next(this.selectedLabel)
      })
    ).subscribe()
  }

  
}

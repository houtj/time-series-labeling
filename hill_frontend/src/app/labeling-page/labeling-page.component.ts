import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import * as Plotly from 'plotly.js-dist-min'
import { DataModel, FileModel, FolderModel, LabelModel, ProjectModel, UserModel } from '../model';
import { DatabaseService } from '../database/database.service';
import { Subscription, filter, first, switchMap, tap } from 'rxjs';
import { transition } from '@angular/animations';
import { LabelingDatabaseService } from './labeling-database.service';
import { ChartService } from './chart.service';
import { DialogService } from './dialog.service';
import { ToggleButtonChangeEvent } from 'primeng/togglebutton';
import { ConfirmationService, MessageService } from 'primeng/api';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { DomSanitizer } from '@angular/platform-browser';
import { setThrowInvalidWriteToSignalError } from '@angular/core/primitives/signals';
import { SplitterResizeEndEvent } from 'primeng/splitter';

@Component({
  selector: 'app-labeling-page',
  templateUrl: './labeling-page.component.html',
  styleUrl: './labeling-page.component.scss'
})
export class LabelingPageComponent implements OnInit, AfterViewInit, OnDestroy{

  @ViewChild('chart') plotlyChart!: ElementRef
  private router = inject(Router)
  private route = inject(ActivatedRoute)
  private databaseService = inject(DatabaseService)
  public labelingDatabaseService = inject(LabelingDatabaseService)
  private chartService = inject(ChartService)
  private dialogService = inject(DialogService)
  private confirmationService = inject(ConfirmationService)
  private messageService = inject(MessageService)
  private http = inject(HttpClient)
  private sanitizer = inject(DomSanitizer)
  private subscriptions = new Subscription()

  private data?: DataModel[]
  private startX?: string|number
  private endX?: string|number
  public fileId?: string|null;
  public folderId?: string|null;
  public labelToggleButton: boolean=false;
  public guidelineToggleButton: boolean=false;
  public fileInfo?: FileModel;
  public folderInfo?: FolderModel;
  public labelInfo?: LabelModel;
  public userInfo?: UserModel;
  public projectInfo?: ProjectModel;
  public nbClick: number = 0;
  public selectedYAxis?: {channelName: string, yaxis: Plotly.YAxisName, color: string}
  public guidelineSelectionDialogVisible: boolean = false;
  // public channelList?: {channelName: string, yaxis: Plotly.YAxisName, color: string}[] = [];
  public selectedButton?: string
  public labelSelectionDialogVisible: boolean = false;
  public classList?: ProjectModel['classes'];
  public selectedClass?: ProjectModel['classes'][0];
  public guideLines?: LabelModel['guidelines']
  public events?: LabelModel['events']
  public shareDialogVisible: boolean = false;
  public messageShared?: string;
  public usersList?: UserModel[];
  public selectedUser?: UserModel;
  downloadUri: any;
  public downloadDialogVisible: boolean= false;
  public descriptionDialogVisible: boolean=false;
  public selectedEventDescription?: string;
  public selectedEvent?: LabelModel['events'][0]
  public selectedEventIndex?: number;
  

  ngOnInit(): void {
    this.databaseService.updatePageLabel('Labeling')

    this.subscriptions.add(this.route.paramMap.pipe(
      tap(params=>{
        this.fileId = params.get('fileId')
        this.folderId = params.get('folderId')
        if (this.fileId!==null && this.folderId!==null) {
          this.databaseService.updateSelectedFolder(this.folderId!)
          this.databaseService.updateSelectedFile(this.fileId!)
        } else {
          this.databaseService.updateSelectedFolder('659c2360df5acff35f6da285')
          this.databaseService.updateSelectedFile('659c238ddf5acff35f6da287')
        }
        this.startX = undefined
        this.endX = undefined
        this.selectedButton = 'none'
        this.nbClick = 0
        this.guidelineToggleButton =false
        this.labelToggleButton = false
      }),
      switchMap(params=>this.databaseService.selectedFile$),
      filter(file=>file!==undefined),
      tap(file=>{
        this.fileInfo = file
        this.databaseService.updatePageTitle(this.fileInfo!.name)
      }),
      switchMap(file=>this.databaseService.userInfo$),
      filter(user=>user!==undefined),
      tap(userInfo=>{
        this.userInfo = userInfo}
        ),
      switchMap(userInfo=> this.databaseService.selectedFolder$),
      filter(folder=>folder!==undefined),
      tap(folder=>{
        this.folderInfo = folder
      }),
      switchMap(user=>{
        return this.http.put(`${environment.databaseUrl}/userRecentFiles`, {
          folderId: this.folderId, 
          fileId:this.fileId, 
          fileName: this.fileInfo!.name,
          folderName: this.folderInfo!.name,
          userInfo: this.userInfo!})
      }),
      switchMap(response=>this.databaseService.projectList$),
      filter(projects=>projects!==undefined),
      tap((projects: ProjectModel[])=>{
        const projectId = this.folderInfo!.project.id
        const projectInfo = projects!.find(p=>p._id?.$oid===projectId)
        this.classList = projectInfo?.classes
      })
    ).subscribe())

  }

  ngAfterViewInit(): void {
    this.subscriptions.add(
      this.databaseService.data$.pipe(
        filter(data=>data!==undefined),
        tap(data=>{
          this.data = data
          this.chartService.initializeChart(this.plotlyChart, data!, this.labelingDatabaseService.channelList!)
          this.plotlyChart.nativeElement.on('plotly_click', (data: Plotly.PlotMouseEvent)=>{
            this.plotlyClick(data)
          })
          this.plotlyChart.nativeElement.on('plotly_hover', (data: Plotly.PlotMouseEvent)=>{
            this.plotlyHover(data)
          })
        }), 
        switchMap(data=>this.databaseService.selectedLabel$),
        filter(label=>label!==undefined),
        tap(label=>{
          this.labelInfo = label
          this.labelingDatabaseService.updateLabels(this.labelInfo!)
        }),
        switchMap(label=>this.labelingDatabaseService.plotlyShapes$),
        filter(shapes=> shapes!==undefined),
        tap(shapes=>{
          this.chartService.updateShapes(shapes!)
        }),
        switchMap(shape=> this.labelingDatabaseService.plotlyAnnotations$),
        filter(annotations=>annotations!==undefined),
        tap(annotations=>{
          this.chartService.updateAnnotations(annotations!)
        })
      ).subscribe()
    )
    
    // this.subscriptions.add(
    //   this.databaseService.selectedLabel$.pipe(
    //     filter(label=>label!==undefined)
    //   ).subscribe(label=>{
    //     this.labelInfo = label
    //     this.labelingDatabaseService.updateLabels(this.labelInfo!)
    //   })
    // )
    
    
    // this.subscriptions.add(
    //   this.labelingDatabaseService.plotlyShapes$.pipe(
    //     filter(shapes=> shapes!==undefined)
    //   ).subscribe(shapes=>{
    //     this.layout.shapes = shapes!
    //     Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
    //   })  
    // )
    
    // this.subscriptions.add(
    //   this.labelingDatabaseService.plotlyAnnotations$.pipe(
    //     filter(annotations=>annotations!==undefined)
    //   ).subscribe(annotations=>{
    //     this.layout.annotations = annotations
    //     Plotly.relayout('myChartDiv', {annotations: this.layout.annotations})
    //   })
    // )
    
    this.subscriptions.add(
      this.labelingDatabaseService.selectedButton$.pipe(
        filter(b=>b!==undefined)
      ).subscribe(button=>{
        this.startX = undefined
        this.endX = undefined
        this.selectedButton = button
        this.chartService.removeTempShapes()
        this.nbClick = 0
        switch (button){
          case 'none':
            this.guidelineToggleButton =false
            this.labelToggleButton = false
            break
          case 'label':
            this.guidelineToggleButton = false
            this.nbClick = 0
            break
          case 'guideline':
            this.labelToggleButton = false
            this.nbClick = 0
            this.guidelineSelectionDialogVisible = true
        }
      })
    )
    

  }
  private plotlyClick(data: Plotly.PlotMouseEvent){
    if (this.selectedButton === 'guideline') {
      switch (this.nbClick){
        case 0:
          const newGuideline = this.chartService.createGuideline(this.selectedYAxis!)
          this.labelInfo!.guidelines.push(newGuideline)
          this.labelingDatabaseService.updateLabels(this.labelInfo!)
          this.labelingDatabaseService.updateSelectedButton('none')
          break
      }
    }
    if (this.selectedButton === 'label') {
      switch (this.nbClick) {
        case 0:
          this.startX = data.points[0].x as string|number
          this.nbClick++
          break
        case 1:
          this.nbClick = 0
          this.endX = data.points[0].x as string|number
          this.labelSelectionDialogVisible = true
          this.selectedEventDescription = ''
          this.selectedClass = this.classList![0]
      }
    }
  }
  private plotlyHover(data:Plotly.PlotMouseEvent){
    if (this.selectedButton === 'label') {
      this.chartService.handleLabelHover(data, this.nbClick, this.startX)
    }
    if (this.selectedButton === 'guideline'){
      switch (this.nbClick) {
        case 0:
          this.chartService.handleGuidelineHover(data, this.selectedYAxis!)
          break
      }
    }
  }

  onChangeGuidelineToggle($event: ToggleButtonChangeEvent) {
    if (this.guidelineToggleButton === true){
      this.labelingDatabaseService.updateSelectedButton('guideline')
      this.guidelineSelectionDialogVisible = true
      this.selectedYAxis = this.labelingDatabaseService.channelList![0]
    } else {
      this.labelingDatabaseService.updateSelectedButton('none')
    }
  }

  onChangeLabelToggle($event: ToggleButtonChangeEvent) {
    if (this.labelToggleButton === true){
      this.labelingDatabaseService.updateSelectedButton('label')
    } else {
      this.labelingDatabaseService.updateSelectedButton('none')
    }
    this.guidelineToggleButton = false
  }

  onClickSelectChannel($event: MouseEvent) {
    this.guidelineSelectionDialogVisible = false  
  }

  onClickSelectClass($event: MouseEvent) {
    const newEvent = this.dialogService.createEvent(
      this.selectedClass!,
      this.selectedEventDescription!,
      this.startX!,
      this.endX!,
      this.userInfo!
    )
    this.labelInfo!.events.push(newEvent)
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
    this.labelSelectionDialogVisible = false
    this.labelingDatabaseService.updateSelectedButton('none')
  }

  onClickDialogCancel($event: MouseEvent,dialog: string) {
    this.labelingDatabaseService.updateSelectedButton('none')
    switch (dialog){
      case 'guidelineSelectionDialog':
        this.guidelineSelectionDialogVisible = false
        break
      case 'labelSelectionDialog':
        this.labelSelectionDialogVisible = false
        break
      case 'shareFolder':
        this.shareDialogVisible =false
        break
      case 'download':
        this.downloadDialogVisible = false
        break
      case 'description':
        this.descriptionDialogVisible = false
        break
    }
  }

  onClickRemoveEvent($event: MouseEvent, event: LabelModel['events'][0]) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.labelInfo!.events = this.labelInfo!.events.filter(e=>e!==event)
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickHideEvent($event: MouseEvent, event: LabelModel['events'][0]) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const index = this.labelInfo!.events.findIndex(e=>e===event)
    this.labelInfo!.events[index].hide = !this.labelInfo!.events[index].hide
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickHideEvents($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.labelInfo!.events.forEach(e=>{
      e.hide=true
    })
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickUnhideEvents($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.labelInfo!.events.forEach(e=>{
      e.hide=false
    })
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickRemoveGuideline($event: MouseEvent, guideline: LabelModel['guidelines'][0]) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.labelInfo!.guidelines = this.labelInfo!.guidelines.filter(e=>e!==guideline)
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickHideGuideline($event: MouseEvent, guideline: LabelModel['guidelines'][0]) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const index = this.labelInfo!.guidelines.findIndex(e=>e===guideline)
    this.labelInfo!.guidelines[index].hide = !this.labelInfo!.guidelines[index].hide
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickHideGuidelines($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.labelInfo!.guidelines.forEach(e=>{
      e.hide=true
    })
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickUnhideGuidelines($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.labelInfo!.guidelines.forEach(e=>{
      e.hide=false
    })
    this.labelingDatabaseService.updateLabels(this.labelInfo!)
  }
  onClickRemoveEvents($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.dialogService.showRemoveEventsConfirmation($event, () => {
      this.labelInfo!.events = []
      this.labelingDatabaseService.updateLabels(this.labelInfo!)
    })
  }
  onClickRemoveGuidelines($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.dialogService.showRemoveGuidelinesConfirmation($event, () => {
      this.labelInfo!.guidelines = []
      this.labelingDatabaseService.updateLabels(this.labelInfo!)
    })
  }

  onClickSelectEvent($event: MouseEvent, event: LabelModel['events'][0]) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.chartService.zoomToEvent(event)
  }

  onClickNextFile($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const fileList = this.folderInfo!.fileList
    const index = this.folderInfo!.fileList.findIndex(fileId=> fileId===this.fileInfo!._id!.$oid)
    this.dialogService.showNextFileConfirmation($event, this.folderInfo!, fileList, index)
  }
  onClickPreviousFile($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const fileList = this.folderInfo!.fileList
    const index = this.folderInfo!.fileList.findIndex(fileId=> fileId===this.fileInfo!._id!.$oid)
    this.dialogService.showPreviousFileConfirmation($event, this.folderInfo!, fileList, index)
  }
  onClickDownload($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.downloadUri = this.dialogService.createDownloadUri(this.data)
    this.downloadDialogVisible = true
  }


  onClickExportLabel($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.databaseService.updateSelectedFile(this.fileInfo?._id?.$oid!)
    this.downloadUri = this.dialogService.createDownloadUri(this.labelInfo!.events)
    this.downloadDialogVisible = true
  }


  onChangeImportInput($event: Event) {
    this.dialogService.handleFileImport($event, this.labelInfo!, this.userInfo!, this.fileInfo!)
  }
  onClickImportLabelButton($event: MouseEvent) {
    this.dialogService.showImportLabelConfirmation($event)
  }

  onClickSaveLabel($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.dialogService.saveLabel(this.labelInfo!, this.userInfo!)
  }
  onClickRefresh($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.databaseService.updateSelectedFile(this.fileInfo?._id?.$oid!)
  }

  onClickParent($event: MouseEvent) {
    this.dialogService.navigateToParent(this.folderId!)
  }
  
  onClickShare($event: MouseEvent) {
    this.messageShared = `Please check this file: ${this.fileInfo?.name}`
    this.dialogService.loadUsers((users) => {
      this.shareDialogVisible = true
      this.usersList = users
      this.selectedUser = this.usersList![0]
    })
  }

  onClickShareOk($event: Event){
    this.dialogService.shareFolder(
      this.folderInfo!,
      this.selectedUser!,
      this.userInfo!,
      this.messageShared!,
      () => { this.shareDialogVisible = false },
      () => { this.shareDialogVisible = false }
    )
  }

  onClickEditDescription($event: MouseEvent, index: number, event: LabelModel['events'][0]) {
    this.selectedEvent = event
    this.selectedEventIndex = index
    this.selectedEventDescription = this.selectedEvent!.description
    this.descriptionDialogVisible = true
  }
  
  onClickEditDescriptionOK($event: MouseEvent) {
    this.descriptionDialogVisible = false
    this.selectedEvent!.description = this.selectedEventDescription!
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe()
    this.initPage()
  }

  private initPage(){
    this.databaseService.data$.next(undefined)
    this.databaseService.selectedLabel$.next(undefined)
    this.labelingDatabaseService.plotlyShapes$.next(undefined)
    this.labelingDatabaseService.plotlyAnnotations$.next(undefined)
    this.labelingDatabaseService.channelList = []
  }

  onResizePlot($event: SplitterResizeEndEvent) {
    this.chartService.resizeChart()
  }
}

import { AfterViewInit, Component, ElementRef, OnDestroy, OnInit, ViewChild, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import * as Plotly from 'plotly.js-dist-min'
import { DataModel, FileModel, FolderModel, LabelModel, ProjectModel, UserModel } from '../model';
import { DatabaseService } from '../database/database.service';
import { Subscription, filter, first, switchMap, tap } from 'rxjs';
import { transition } from '@angular/animations';
import { LabelingDatabaseService } from './labeling-database.service';
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
  private confirmationService = inject(ConfirmationService)
  private messageService = inject(MessageService)
  private http = inject(HttpClient)
  private sanitizer = inject(DomSanitizer)
  private subscriptions = new Subscription()

  private data?: DataModel[]
  private startX?: string|number
  private endX?: string|number
  private layout: Partial<Plotly.Layout> = {
    showlegend: true,
    legend: {
      x: 1,
      y: 1, 
      xanchor: 'right',
      bgcolor: '#c7ced9',
      font: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
      }
    },
    hovermode: 'x',
    dragmode: 'pan',
    paper_bgcolor: '#c7ced9',
    plot_bgcolor: '#e0e4ea',
    // autosize: true,
    // height: 400,
    margin: {
      t:20,
      r: 5,
      b: 20,
      l: 40
    },
    shapes: [],
    annotations: [],
    xaxis: {
      showgrid: true,
      color: '#222',
      tickfont:{
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"',
        size: 16,
        color:'#444e5c'
      },
    },
    hoverlabel:{
      font:{
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
      }
    },
    
  }
  private config: Partial<Plotly.Config> = {
    responsive: true,
    scrollZoom: true,
    displaylogo: false,
  }
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
          const x_trace = data!.find(c=>c.x===true)!
          const channels = data!.filter(c=>c.x===false)
          const traces: Plotly.Data[] = channels.map((c, index)=>{
            let k
            if (index===0){
              k = ''
            } else {
              k = index+1
            }
            // this.initLayout()
            //@ts-expect-error
            this.layout[`yaxis${k}`] = {
              title: {
                font: {
                  color: c.color,
                  family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
                },
                standoff: 0,
                text: `${c.name} - ${c.unit}`
              },
              tickfont: {
                color: c.color,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
              },
              overlaying: index===0? 'free': 'y',
              side: 'left',
              position: 0.04*index,
              showgrid: false,
              zeroline: false,
            }
            //@ts-expect-error
            this.labelingDatabaseService.channelList?.push({channelName: c.name, yaxis: `y${k}`, color: c.color})
            return {
            x: x_trace.data,
            y: c.data,
            yaxis: `y${k}`,
            name: c.name,
            type: 'scatter',
            mode: 'lines',
            line: {color: c.color},
            }
          })
          this.layout.xaxis!.domain = [channels.length*0.04-0.035, 0.94]
          this.layout.xaxis!.range = [x_trace.data[0], x_trace.data[x_trace.data.length-1]]
          Plotly.newPlot(this.plotlyChart.nativeElement, traces, this.layout, this.config)
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
          this.layout.shapes = shapes!
          Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
        }),
        switchMap(shape=> this.labelingDatabaseService.plotlyAnnotations$),
        filter(annotations=>annotations!==undefined),
        tap(annotations=>{
          this.layout.annotations = annotations
          Plotly.relayout('myChartDiv', {annotations: this.layout.annotations})
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
        this.removeTempShapes()
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
  private removeTempShapes() {
    //@ts-expect-error
    this.layout.shapes = this.layout.shapes!.filter(s=>s.temp!==true)
    Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
  }
  private plotlyClick(data: Plotly.PlotMouseEvent){
    if (this.selectedButton === 'guideline') {
      switch (this.nbClick){
        case 0:
          const newGuideline: LabelModel['guidelines'][0]={
            channelName: this.selectedYAxis!.channelName,
            color: this.selectedYAxis!.color,
            hide: false,
            y: this.layout.shapes![this.layout.shapes!.length-1].y0!,
            yaxis: this.layout.shapes![this.layout.shapes!.length-1].yref!
          }
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
      switch (this.nbClick) {
        case 0:
          //@ts-expect-error
          if (this.layout.shapes!.length!==0 && this.layout.shapes![this.layout.shapes!.length-1].temp!==undefined){
            const lastShape = this.layout.shapes![this.layout.shapes!.length-1]
            lastShape.x0 = data.points[0].x
            lastShape.x1 = data.points[0].x
            Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
          } else {
            const lastShape: Plotly.Shape = {
              type: 'line',
              xref: 'x',
              yref: 'paper',
              y0: 0,
              y1: 1,
              x0: data.points[0].x,
              x1: data.points[0].x,
              opacity: 0.5,
              line: {
                color: '#808080',
                width: 2,
                dash: 'dash'
              },
              //@ts-expect-error
              temp: true
            }
            this.layout.shapes?.push(lastShape)
            Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
          }
          break
        case 1:
          const lastShape = this.layout.shapes![this.layout.shapes!.length-1]
          lastShape.type ='rect'
          lastShape.x0 = this.startX!
          lastShape.x1 = data.points[0].x
          lastShape.fillcolor = '#808080'
          lastShape.line!.width = 4
          lastShape.line!.dash = 'dot'
          lastShape.opacity = 0.5
          Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
          break
      }
    }
    if (this.selectedButton === 'guideline'){
      switch (this.nbClick) {
        case 0:
          //@ts-expect-error
          if (this.layout.shapes!.length!==0 && this.layout.shapes![this.layout.shapes!.length-1].temp!==undefined){
            const lastShape = this.layout.shapes![this.layout.shapes!.length-1]
            lastShape.y0 = data.points.find(c=> c.data.yaxis===this.selectedYAxis!.yaxis)!.y
            lastShape.y1 = data.points.find(c=> c.data.yaxis===this.selectedYAxis!.yaxis)!.y
            Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
          } else {
            const lastShape: Plotly.Shape = {
              type: 'line',
              yref: this.selectedYAxis!.yaxis,
              xref: 'paper',
              x0: 0,
              x1: 1,
              y0: data.points.find(c=> c.data.yaxis===this.selectedYAxis!.yaxis)!.y,
              y1: data.points.find(c=> c.data.yaxis===this.selectedYAxis!.yaxis)!.y,
              opacity: 0.5,
              line: {
                color: this.selectedYAxis?.color,
                width: 2,
                dash: 'dash'
              },
              //@ts-expect-error
              temp: true
            }
            this.layout.shapes?.push(lastShape)
            Plotly.relayout('myChartDiv', {shapes: this.layout.shapes})
          }
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
    const newEvent: LabelModel['events'][0] = {
      className: this.selectedClass!.name,
      color: this.selectedClass!.color,
      description: this.selectedEventDescription!,
      start: this.startX!,
      end: this.endX!,
      hide: false,
      labeler: this.userInfo!.name,
    }
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
    this.confirmationService.confirm({
      target: $event.target as EventTarget,
      message: 'Are you sure you want to remove all the events?',
      icon: 'pi pi-info-circle',
      accept: ()=>{
        this.labelInfo!.events = []
        this.labelingDatabaseService.updateLabels(this.labelInfo!)
      }
    })
  }
  onClickRemoveGuidelines($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.confirmationService.confirm({
      target: $event.target as EventTarget,
      message: 'Are you sure you want to remove all the guidelines?',
      icon: 'pi pi-info-circle',
      accept: ()=>{
        this.labelInfo!.guidelines = []
        this.labelingDatabaseService.updateLabels(this.labelInfo!)
      }
    })
  }

  onClickSelectEvent($event: MouseEvent, event: LabelModel['events'][0]) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.layout.xaxis!.range![0]= event.start, 
    this.layout.xaxis!.range![1] = event.end
    Plotly.relayout('myChartDiv', {xaxis: this.layout.xaxis})
  }

  onClickNextFile($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const fileList = this.folderInfo!.fileList
    const index = this.folderInfo!.fileList.findIndex(fileId=> fileId===this.fileInfo!._id!.$oid)
    if (index!==fileList.length-1){
      this.confirmationService.confirm({
        target: $event.target as EventTarget,
        message: 'Are you sure you want to proceed? All the unsaved changes are disgarded!',
        icon: 'pi pi-exclamation-triangle',
        accept: ()=>{
          this.router.navigate(['/labeling', {folderId: this.folderInfo!._id!.$oid, fileId: fileList[index+1]}])
        }
      })
    } else {
      this.messageService.add({
        severity: 'warn',
        summary: 'The end',
        detail: 'No next file'
      })
    }
  }
  onClickPreviousFile($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const fileList = this.folderInfo!.fileList
    const index = this.folderInfo!.fileList.findIndex(fileId=> fileId===this.fileInfo!._id!.$oid)
    if (index!==0){
      this.confirmationService.confirm({
        target: $event.target as EventTarget,
        message: 'Are you sure you want to proceed? All the unsaved changes are disgarded!',
        icon: 'pi pi-exclamation-triangle',
        accept: ()=>{
          this.router.navigate(['/labeling', {folderId: this.folderInfo!._id!.$oid, fileId: fileList[index-1]}])
        }
      })
    } else {
      this.messageService.add({
        severity: 'warn',
        summary: 'The end',
        detail: 'No previous file'
      })
    }
  }
  onClickDownload($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    const json = JSON.stringify(this.data)
    const uri = this.sanitizer.bypassSecurityTrustUrl("data:text/json;charset=UTF-8,"+encodeURIComponent(json))
    this.downloadUri = uri
    this.downloadDialogVisible = true
  }


  onClickExportLabel($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.databaseService.updateSelectedFile(this.fileInfo?._id?.$oid!)
    const json = JSON.stringify(this.labelInfo!.events)
    const uri = this.sanitizer.bypassSecurityTrustUrl("data:text/json;charset=UTF-8,"+encodeURIComponent(json))
    this.downloadUri = uri
    this.downloadDialogVisible = true
  }


  onChangeImportInput($event: Event) {
    const target = $event.target as HTMLInputElement
    const file:File = (target!.files as FileList)[0]
    if (file){
      const formData: FormData = new FormData()
      formData.append('data', this.labelInfo?._id?.$oid!)
      formData.append('user', this.userInfo!.name)
      formData.append('file', file, file.name)
      this.http.post(`${environment.databaseUrl}/event`, formData).subscribe(res=>{
        this.databaseService.updateSelectedFile(this.fileInfo?._id?.$oid!)
      })
    }  
  }
  onClickImportLabelButton($event: MouseEvent) {
    this.confirmationService.confirm({
      target: $event.target!,
      message: 'All the current events will be replaced by the uploaded events',
      icon: 'pi pi-info-circle',
      accept: ()=>{
        document.getElementById('fileImportInput')?.click() 
      }
    })
  }

  onClickSaveLabel($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.http.put(`${environment.databaseUrl}/labels`, {label: this.labelInfo!, user: this.userInfo!.name}).subscribe(response=>{
      this.messageService.add({
        severity: 'success',
        summary: 'Saved',
        detail: 'Your label has been saved'
      })
    })
  }
  onClickRefresh($event: MouseEvent) {
    this.labelingDatabaseService.updateSelectedButton('none')
    this.databaseService.updateSelectedFile(this.fileInfo?._id?.$oid!)
  }

  onClickParent($event: MouseEvent) {
    this.router.navigate(['/files', {folderId: this.folderId}])
  }
  
  onClickShare($event: MouseEvent) {
    this.messageShared = `Please check this file: ${this.fileInfo?.name}`
    this.http.get<string>(`${environment.databaseUrl}/users`).subscribe(users=>{
      this.shareDialogVisible = true
      this.usersList = JSON.parse(users)
      this.selectedUser = this.usersList![0]
    })
  }

  onClickShareOk($event: Event){
    this.http.put<string>(`${environment.databaseUrl}/usersSharedFiles`, {folder: this.folderInfo, user: this.selectedUser, userName: this.userInfo!.name, message: this.messageShared}).subscribe(response=>{
      this.shareDialogVisible = false
      this.messageService.add({severity: 'success', summary: 'Folder Shared', detail: 'Folder Shared successfully'})
    }, error=>{
      this.shareDialogVisible = false
      this.messageService.add({severity:'error', summary:'Folder sharing failed.', detail:'Folder sharing failed.'})
    })
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
    window.dispatchEvent(new Event('resize'))
  }
}

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
  @ViewChild('chatMessages') chatMessagesElement!: ElementRef
  @ViewChild('chatInput') chatInputElement!: ElementRef
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
  public sidePanelVisible: boolean = false;
  
  // Chatbot properties
  public chatbotDrawerVisible: boolean = false;
  public chatHistory: any[] = [];
  public currentMessage: string = '';
  public isWaitingForResponse: boolean = false;
  private websocket?: WebSocket;
  

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

  onClickToggleChatbot($event: MouseEvent) {
    this.chatbotDrawerVisible = !this.chatbotDrawerVisible;
    if (this.chatbotDrawerVisible) {
      this.initializeChatbot();
    } else {
      this.closeChatbot();
    }
  }

  private initializeChatbot() {
    if (this.fileId) {
      // Reset UI state when opening
      this.resetChatbotState();
      // Load conversation history
      this.loadConversationHistory();
      // Connect to WebSocket
      this.connectWebSocket();
    }
  }

  private closeChatbot() {
    // Cancel any ongoing AI requests
    this.cancelOngoingRequest();
    // Disconnect WebSocket
    this.disconnectWebSocket();
    // Reset UI state
    this.resetChatbotState();
  }

  private resetChatbotState() {
    // Reset waiting state and enable send button
    this.isWaitingForResponse = false;
    // Clear current message input
    this.currentMessage = '';
  }

  private cancelOngoingRequest() {
    if (this.isWaitingForResponse && this.websocket) {
      // Send cancellation message to backend
      try {
        this.websocket.send(JSON.stringify({ 
          type: 'cancel_request',
          message: 'User closed chatbot' 
        }));
      } catch (error) {
        console.warn('Could not send cancellation message:', error);
      }
    }
  }

  onChatbotSidebarHide() {
    // This is called when the sidebar is closed by any means (X button, escape, etc.)
    this.closeChatbot();
  }

  private loadConversationHistory() {
    this.http.get<string>(`${environment.databaseUrl}/conversations/${this.fileId}`).subscribe({
      next: (response) => {
        const conversation = JSON.parse(response);
        this.chatHistory = conversation.history || [];
        this.scrollToBottom();
      },
      error: (error) => {
        console.error('Error loading conversation history:', error);
        this.chatHistory = [];
      }
    });
  }

  private connectWebSocket() {
    if (this.websocket) {
      this.websocket.close();
    }

    const wsUrl = `ws://localhost:8000/ws/chat/${this.fileId}`;
    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = () => {
      console.log('WebSocket connected');
    };

    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleWebSocketMessage(data);
    };

    this.websocket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'Connection Error',
        detail: 'Failed to connect to AI assistant'
      });
    };
  }

  private disconnectWebSocket() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = undefined;
    }
  }

  private handleWebSocketMessage(data: any) {
    console.log(data.type)
    switch (data.type) {
      case 'user_message_received':
        // Message was received and processed
        break;
      case 'ai_response':
        this.chatHistory.push(data.message);
        this.isWaitingForResponse = false;
        this.scrollToBottom();
        break;
      case 'event_added':
        // New event was added by AI - update immediately
        this.addEventToLocalData(data.data.event);
        this.messageService.add({
          severity: 'success',
          summary: 'Event Added',
          detail: data.data.message
        });
        break;
      case 'guideline_added':
        // New guideline was added by AI - update immediately
        this.addGuidelineToLocalData(data.data.guideline);
        this.messageService.add({
          severity: 'success',
          summary: 'Guideline Added',
          detail: data.data.message
        });
        break;
      case 'data_updated':
        // AI has updated the labels/guidelines - refresh the data
        this.refreshLabelsAndData();
        this.messageService.add({
          severity: 'success',
          summary: 'Data Updated',
          detail: data.message
        });
        console.log(data.message)
        break;
      case 'error':
        this.messageService.add({
          severity: 'error',
          summary: 'AI Error',
          detail: data.message
        });
        this.isWaitingForResponse = false;
        break;
    }
  }

  onClickSendMessage($event: MouseEvent) {
    this.sendMessage();
  }

  onChatInputKeydown($event: KeyboardEvent) {
    if ($event.key === 'Enter' && !$event.shiftKey) {
      $event.preventDefault();
      this.sendMessage();
    }
  }

  private sendMessage() {
    if (!this.currentMessage.trim() || this.isWaitingForResponse || !this.websocket) {
      return;
    }

    const message = {
      role: 'user',
      content: this.currentMessage,
      timestamp: new Date().toISOString()
    };

    // Add user message to chat history
    this.chatHistory.push(message);
    this.isWaitingForResponse = true;
    
    // Send message through WebSocket
    this.websocket.send(JSON.stringify({ message: this.currentMessage }));
    
    // Clear input
    this.currentMessage = '';
    this.scrollToBottom();
  }

  onClickClearChat($event: MouseEvent) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to clear the conversation history?',
      header: 'Clear Chat',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.clearConversationHistory();
      }
    });
  }

  private clearConversationHistory() {
    this.http.delete(`${environment.databaseUrl}/conversations/${this.fileId}`).subscribe({
      next: () => {
        this.chatHistory = [];
        this.messageService.add({
          severity: 'success',
          summary: 'Chat Cleared',
          detail: 'Conversation history has been cleared'
        });
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Clear Failed',
          detail: 'Failed to clear conversation history'
        });
      }
    });
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.chatMessagesElement) {
        const element = this.chatMessagesElement.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }

  private addEventToLocalData(event: any) {
    // Add event to local labelInfo immediately for instant UI update
    if (this.labelInfo) {
      if (!this.labelInfo.events) {
        this.labelInfo.events = [];
      }
      this.labelInfo.events.push(event);
      
      // Update the database service observables
      this.databaseService.selectedLabel$.next(this.labelInfo);
      
      // Trigger chart refresh by updating labels (this triggers the chart update pipeline)
      this.labelingDatabaseService.updateLabels(this.labelInfo);
    }
  }

  private addGuidelineToLocalData(guideline: any) {
    // Add guideline to local labelInfo immediately for instant UI update
    if (this.labelInfo) {
      if (!this.labelInfo.guidelines) {
        this.labelInfo.guidelines = [];
      }
      this.labelInfo.guidelines.push(guideline);
      
      // Update the database service observables
      this.databaseService.selectedLabel$.next(this.labelInfo);
      
      // Trigger chart refresh by updating labels (this triggers the chart update pipeline)
      this.labelingDatabaseService.updateLabels(this.labelInfo);
    }
  }

  private refreshLabelsAndData() {
    // Refresh the label data to show new events/guidelines added by AI
    if (this.fileInfo?.label) {
      this.http.get<string>(`${environment.databaseUrl}/labels/${this.fileInfo.label}`).subscribe({
        next: (response) => {
          const updatedLabel = JSON.parse(response);
          this.labelInfo = updatedLabel;
          
          // Update the database service observables
          this.databaseService.selectedLabel$.next(this.labelInfo);
          
          // Trigger chart refresh by updating labels (this triggers the chart update pipeline)
          if (this.labelInfo) {
            this.labelingDatabaseService.updateLabels(this.labelInfo);
          }
        },
        error: (error) => {
          console.error('Error refreshing labels:', error);
        }
      });
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe()
    this.disconnectWebSocket()
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

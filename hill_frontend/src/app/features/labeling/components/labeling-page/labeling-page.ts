import { Component, OnInit, OnDestroy, ViewChild, inject, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { Subscription } from 'rxjs';

// PrimeNG imports
import { Splitter } from 'primeng/splitter';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { Tabs, TabList, Tab, TabPanels, TabPanel } from 'primeng/tabs';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';

// Core imports
import { UserStateService } from '../../../../core/services';
import { LabelsRepository, UsersRepository, FilesRepository, ProjectsRepository, FoldersRepository } from '../../../../core/repositories';
import { FileModel, FolderModel, LabelModel, ProjectModel, DataModel, UserModel } from '../../../../core/models';
import { environment } from '../../../../../environments/environment';

// Feature services
import { LabelStateService, AutoDetectionService, LabelingActionsService } from '../../services';

// Shared services
import { AiChatService } from '../../../../shared/services';

// Feature models
import { ToolbarAction } from '../../models/toolbar-action.model';

// Shared components
import { ShareDialogComponent, DescriptionDialogComponent, ProjectDescriptionsDialogComponent } from '../../../../shared/components';

// Feature components
import { ChartComponent } from '../chart/chart';
import { LabelingToolbarComponent } from '../labeling-toolbar/labeling-toolbar';
import { EventsPanelComponent } from '../events-panel/events-panel';
import { GuidelinesPanelComponent } from '../guidelines-panel/guidelines-panel';
import { AiChatTabComponent } from '../ai-chat-tab/ai-chat-tab';
import { AutoDetectionPanelComponent } from '../auto-detection-panel/auto-detection-panel';

/**
 * Labeling Page Component
 * Main orchestrator page for interactive data labeling
 * Composes child components for chart, events, guidelines, toolbar, etc.
 */
@Component({
  selector: 'app-labeling-page',
  imports: [
    CommonModule,
    Splitter,
    ToastModule,
    Tabs,
    TabList,
    Tab,
    TabPanels,
    TabPanel,
    ButtonModule,
    TooltipModule,
    DialogModule,
    ChartComponent,
    LabelingToolbarComponent,
    EventsPanelComponent,
    GuidelinesPanelComponent,
    AiChatTabComponent,
    AutoDetectionPanelComponent,
    ShareDialogComponent,
    DescriptionDialogComponent,
    ProjectDescriptionsDialogComponent,
    ButtonModule,
    TooltipModule
  ],
  standalone: true,
  providers: [MessageService, LabelingActionsService],
  templateUrl: './labeling-page.html',
  styleUrl: './labeling-page.scss',
  host: {
    '(document:keydown)': 'handleKeyboardShortcut($event)',
    'tabindex': '0'
  }
})
export class LabelingPageComponent implements OnInit, OnDestroy {
  // ViewChild references to panel components
  @ViewChild(GuidelinesPanelComponent) guidelinesPanel?: GuidelinesPanelComponent;
  @ViewChild(EventsPanelComponent) eventsPanel?: EventsPanelComponent;
  @ViewChild(AiChatTabComponent) aiChatTab?: AiChatTabComponent;
  @ViewChild(AutoDetectionPanelComponent) autoDetectionPanel?: AutoDetectionPanelComponent;
  
  // Injected services
  private readonly route = inject(ActivatedRoute);
  private readonly userState = inject(UserStateService);
  private readonly labelState = inject(LabelStateService);
  private readonly projectsRepo = inject(ProjectsRepository);
  private readonly filesRepo = inject(FilesRepository);
  private readonly foldersRepo = inject(FoldersRepository);
  private readonly labelsRepo = inject(LabelsRepository);
  private readonly autoDetectionService = inject(AutoDetectionService);
  private readonly aiChatService = inject(AiChatService);
  private readonly labelingActions = inject(LabelingActionsService);
  private readonly messageService = inject(MessageService);
  
  private subscriptions = new Subscription();
  private previousFileId?: string;
  
  // Dialog visibility
  protected shareDialogVisible = false;
  protected descriptionDialogVisible = false;
  protected projectDescriptionsDialogVisible = false;
  protected downloadDialogVisible = false;
  protected downloadUri?: SafeResourceUrl;
  
  // Selected event for description editing
  protected selectedEvent?: LabelModel['events'][0];
  protected selectedEventIndex?: number;
  protected selectedEventDescription = '';
  
  // Panel visibility
  protected aiChatVisible = false;
  protected autoDetectionVisible = false;
  
  // Active tab (0 = Guidelines, 1 = AI Assistant, 2 = Auto-Detection)
  protected activeTab = '0';
  
  // Route parameters
  protected fileId?: string;
  protected folderId?: string;
  
  // Data from resolver
  protected fileInfo?: FileModel;
  protected folderInfo?: FolderModel;
  protected labelInfo?: LabelModel;
  protected data?: DataModel[];
  
  // Computed project info from user state
  protected projectInfo = computed(() => {
    const projectList = this.userState.projectList();
    if (this.folderInfo && projectList.length > 0) {
      const projectId = this.folderInfo.project.id;
      return projectList.find(p => p._id?.$oid === projectId);
    }
    return undefined;
  });
  
  constructor() {
    // Watch for auto-detection completion to refresh label data
    effect(() => {
      if (this.autoDetectionService.detectionCompleted()) {
        // Refresh label data to show newly detected events
        this.onRefreshPage();
        
        // Show success message
        this.messageService.add({
          severity: 'success',
          summary: 'Auto-Detection Complete',
          detail: 'New events have been added to the chart'
        });
      }
    });
  }
  
  ngOnInit(): void {
    this.userState.updatePageLabel('Labeling');
    
    // Get data from resolver (initial load only)
    this.subscriptions.add(
      this.route.data.subscribe((routeData) => {
        const resolvedData = routeData['labelingData'];
        if (resolvedData) {
          this.loadResolvedData(resolvedData);
        }
      })
    );
    
    // Watch for route parameter changes and reload data
    this.subscriptions.add(
      this.route.paramMap.subscribe(params => {
        const newFileId = params.get('fileId') || undefined;
        const newFolderId = params.get('folderId') || 
                           this.route.snapshot.queryParamMap.get('folderId') || undefined;
        
        // Check if fileId has changed (navigation between files)
        if (this.previousFileId && newFileId && this.previousFileId !== newFileId) {
          // File changed - reload all data
          this.reloadFileData(newFileId, newFolderId);
        } else {
          // First load - just store the IDs
          this.fileId = newFileId;
          this.folderId = newFolderId;
          this.previousFileId = newFileId;
        }
      })
    );
    
    // Watch for query parameter changes
    this.subscriptions.add(
      this.route.queryParamMap.subscribe(params => {
        const newFolderId = params.get('folderId') || undefined;
        if (newFolderId) {
          this.folderId = newFolderId;
        }
      })
    );
    
    // Listen for AI chat label updates
    this.subscriptions.add(
      this.aiChatService.labelUpdated$.subscribe(() => {
        // Reload label data when AI adds events/guidelines
        this.onRefreshPage();
      })
    );
  }
  
  /**
   * Load data from resolver
   */
  private loadResolvedData(resolvedData: any): void {
    this.fileInfo = resolvedData.file;
    this.folderInfo = resolvedData.folder;
    this.labelInfo = resolvedData.label;
    this.data = resolvedData.data;
    
    // Update page title with file name
    if (this.fileInfo) {
      this.userState.updatePageTitle(this.fileInfo.name);
    }
    
    // Update label state
    if (this.labelInfo) {
      this.labelState.updateLabel(this.labelInfo);
    }
  }
  
  /**
   * Reload all file data when navigating between files
   */
  private reloadFileData(fileId: string, folderId?: string): void {
    if (!folderId) {
      console.error('Folder ID is required to reload file data');
      return;
    }
    
    // Disconnect WebSocket services first
    if (this.autoDetectionService.isConnected()) {
      this.autoDetectionService.disconnect();
      this.autoDetectionVisible = false;
    }
    if (this.aiChatService.isConnected()) {
      this.aiChatService.disconnect();
      this.aiChatVisible = false;
    }
    
    // Reset dialog visibility
    this.shareDialogVisible = false;
    this.descriptionDialogVisible = false;
    this.projectDescriptionsDialogVisible = false;
    this.downloadDialogVisible = false;
    
    // Reset active tab
    this.activeTab = '0';
    
    // Load file data
    this.filesRepo.getFile(fileId).subscribe({
      next: (fileData) => {
        const file = fileData.fileInfo;
        const data = fileData.data;
        const labelId = file.label;
        
        // Load folder and label
        this.foldersRepo.getFolder(folderId).subscribe({
          next: (folder) => {
            this.folderInfo = folder;
            
            // Load label
            this.labelsRepo.getLabel(labelId).subscribe({
              next: (label) => {
                // Update all component state
                this.fileInfo = file;
                this.labelInfo = label;
                this.data = data;
                this.fileId = fileId;
                this.folderId = folderId;
                this.previousFileId = fileId;
                
                // Update page title
                this.userState.updatePageTitle(file.name);
                
                // Update label state (this will trigger chart update)
                this.labelState.updateLabel(label);
                
                // Reset selected event
                this.selectedEvent = undefined;
                this.selectedEventIndex = undefined;
                this.selectedEventDescription = '';
              },
              error: (error) => {
                console.error('Failed to load label:', error);
                this.messageService.add({
                  severity: 'error',
                  summary: 'Error',
                  detail: 'Failed to load label data'
                });
              }
            });
          },
          error: (error) => {
            console.error('Failed to load folder:', error);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'Failed to load folder data'
            });
          }
        });
      },
      error: (error) => {
        console.error('Failed to load file:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load file data'
        });
      }
    });
  }
  
  ngOnDestroy(): void {
    // Clean up subscriptions
    this.subscriptions.unsubscribe();
    
    // Disconnect WebSocket services to prevent stale connections
    if (this.autoDetectionService.isConnected()) {
      this.autoDetectionService.disconnect();
    }
    if (this.aiChatService.isConnected()) {
      this.aiChatService.disconnect();
    }
    
    // Reset label state
    this.labelState.reset();
  }
  
  /**
   * Handle plot resize event from splitter
   */
  onResizePlot(): void {
    // Dispatch window resize event to trigger chart resize
    // This is needed because ResizeObserver doesn't always catch splitter changes immediately
    window.dispatchEvent(new Event('resize'));
  }
  
  /**
   * Handle share folder
   */
  onShareFolder(): void {
    this.shareDialogVisible = true;
  }
  
  /**
   * Handle share folder confirmation
   */
  onShareFolderConfirm(event: { user: UserModel; message: string }): void {
    if (!this.folderInfo) return;
    
    this.subscriptions.add(
      this.labelingActions.shareFolder(this.folderInfo, event.user, event.message).subscribe({
        next: () => {
          this.shareDialogVisible = false;
        },
        error: () => {
          this.shareDialogVisible = false;
        }
      })
    );
  }
  
  /**
   * Handle import labels
   */
  onImportLabels(): void {
    const userInfo = this.userState.userInfo();
    
    if (!this.labelInfo || !userInfo || !this.fileInfo) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Missing required information'
      });
      return;
    }
    
    try {
      this.subscriptions.add(
        this.labelingActions.importLabels('fileImportInput', this.labelInfo, userInfo, this.fileInfo).subscribe({
          next: (freshLabel: LabelModel) => {
            // Update local reference with fresh label data
            this.labelInfo = freshLabel;
          }
        })
      );
    } catch (error) {
      // Error already handled by service
    }
  }
  
  /**
   * Handle export labels
   */
  onExportLabels(): void {
    if (!this.labelInfo) return;
    
    try {
      this.downloadUri = this.labelingActions.exportLabels(this.labelInfo);
      this.downloadDialogVisible = true;
    } catch (error) {
      // Error already handled by service
    }
  }
  
  /**
   * Handle download data
   */
  onDownloadData(): void {
    if (!this.fileId) return;
    
    this.subscriptions.add(
      this.labelingActions.downloadData(this.fileId).subscribe({
        next: (uri: SafeResourceUrl) => {
          this.downloadUri = uri;
          this.downloadDialogVisible = true;
        }
      })
    );
  }
  
  /**
   * Handle edit descriptions
   */
  onEditDescriptions(): void {
    if (!this.projectInfo()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Warning',
        detail: 'Project information not available'
      });
      return;
    }
    this.projectDescriptionsDialogVisible = true;
  }
  
  /**
   * Handle project descriptions save
   */
  onProjectDescriptionsSave(): void {
    // Reload project info to get updated descriptions
    const currentProject = this.projectInfo();
    if (currentProject?._id?.$oid) {
      this.projectsRepo.getProject(currentProject._id.$oid).subscribe({
        next: (updatedProject: ProjectModel) => {
          // Update the project in the userState's project list
          const currentProjectList = this.userState.projectList();
          const updatedList = currentProjectList.map(p => 
            p._id?.$oid === updatedProject._id?.$oid ? updatedProject : p
          );
          this.userState.setProjectList(updatedList);
        },
        error: (error: any) => {
          console.error('Failed to reload project:', error);
        }
      });
    }
  }
  
  /**
   * Handle auto-annotate
   */
  onAutoAnnotate(): void {
    this.autoDetectionVisible = true;
    
    // Switch to Auto-Detection tab (value depends on if AI chat is visible)
    this.activeTab = this.aiChatVisible ? '2' : '1';
    
    // Connect to auto-detection service if not already connected
    if (!this.autoDetectionService.isConnected()) {
      this.autoDetectionService.connectAutoDetection(this.fileId!, this.folderId!);
    }
  }
  
  /**
   * Handle toggle AI chat
   */
  onToggleAiChat(): void {
    this.aiChatVisible = true;
    
    // Switch to AI Assistant tab
    this.activeTab = '1';
    
    // Connect to AI chat service if not already connected
    if (!this.aiChatService.isConnected()) {
      this.aiChatService.connectChat(this.fileId!, {
        folderId: this.folderId,
        projectId: this.projectInfo()?._id?.$oid,
        userName: this.userState.userInfo()?.name
      });
    }
  }
  
  /**
   * Handle AI chat close
   */
  onAiChatClose(): void {
    this.aiChatVisible = false;
    this.aiChatService.disconnect();
    
    // If auto-detection is visible, switch to it, otherwise switch to Guidelines
    if (this.autoDetectionVisible) {
      this.activeTab = '1'; // Auto-detection becomes tab 1 when AI chat closes
    } else {
      this.activeTab = '0'; // Switch back to Guidelines
    }
  }
  
  /**
   * Handle auto-detection close
   */
  onAutoDetectionClose(): void {
    this.autoDetectionVisible = false;
    this.autoDetectionService.disconnect();
    
    // If AI chat is visible, switch to it, otherwise switch to Guidelines
    if (this.aiChatVisible) {
      this.activeTab = '1'; // AI chat is always tab 1
    } else {
      this.activeTab = '0'; // Switch back to Guidelines
    }
  }
  
  /**
   * Handle refresh (reload label data from backend)
   */
  onRefreshPage(): void {
    if (!this.fileInfo?._id?.$oid) return;
    
    const labelId = this.fileInfo.label;
    
    // Refetch label data using service
    this.subscriptions.add(
      this.labelingActions.refreshLabelData(labelId).subscribe({
        next: (label: LabelModel) => {
          this.labelInfo = label;
        }
      })
    );
  }
  
  /**
   * Handle edit event description
   */
  onEditEventDescription(event: { event: LabelModel['events'][0]; index: number }): void {
    this.selectedEvent = event.event;
    this.selectedEventIndex = event.index;
    this.selectedEventDescription = event.event.description || '';
    this.descriptionDialogVisible = true;
  }
  
  /**
   * Handle save event description
   */
  onSaveEventDescription(newDescription: string): void {
    if (this.selectedEvent && this.labelInfo && this.selectedEventIndex !== undefined) {
      // Update the description in the event at the correct index
      if (this.labelInfo.events && this.labelInfo.events[this.selectedEventIndex]) {
        this.labelInfo.events[this.selectedEventIndex].description = newDescription;
        
        // Also update the selected event reference
        this.selectedEvent.description = newDescription;
      }
      
      this.descriptionDialogVisible = false;
      
      // Update label in state
      this.labelState.updateLabel(this.labelInfo);
      
      // Auto-save to database
      this.labelingActions.saveLabel(this.labelInfo).subscribe();
    }
  }
  
  /**
   * Get toolbar actions for the current left tab
   */
  getLeftToolbarActions(): ToolbarAction[] {
    if (this.activeTab === '0') {
      return this.guidelinesPanel?.getToolbarActions() || [];
    }
    if (this.activeTab === '1') {
      if (this.aiChatVisible) {
        return this.aiChatTab?.getToolbarActions() || [];
      }
      if (this.autoDetectionVisible) {
        return this.autoDetectionPanel?.getToolbarActions() || [];
      }
    }
    if (this.activeTab === '2' && this.autoDetectionVisible) {
      return this.autoDetectionPanel?.getToolbarActions() || [];
    }
    return [];
  }
  
  /**
   * Get toolbar actions for the right tab (events)
   */
  getRightToolbarActions(): ToolbarAction[] {
    return this.eventsPanel?.getToolbarActions() || [];
  }
  
  /**
   * Handle keyboard shortcuts
   * E key: Toggle label mode
   * G key: Toggle guideline mode
   */
  handleKeyboardShortcut(event: KeyboardEvent): void {
    // Ignore shortcuts if user is typing in an input/textarea or dialog is open
    const target = event.target as HTMLElement;
    const isInputField = target.tagName === 'INPUT' || 
                        target.tagName === 'TEXTAREA' || 
                        target.isContentEditable;
    
    // Also ignore if any dialog is open
    const isDialogOpen = this.shareDialogVisible || 
                        this.descriptionDialogVisible || 
                        this.projectDescriptionsDialogVisible || 
                        this.downloadDialogVisible;
    
    if (isInputField || isDialogOpen) {
      return;
    }
    
    const key = event.key.toLowerCase();
    
    // E key: Toggle label mode
    if (key === 'e') {
      event.preventDefault();
      const currentButton = this.labelState.selectedButton();
      if (currentButton === 'label') {
        this.labelState.updateSelectedButton('none');
      } else {
        this.labelState.updateSelectedButton('label');
      }
    }
    
    // G key: Toggle guideline mode
    if (key === 'g') {
      event.preventDefault();
      const currentButton = this.labelState.selectedButton();
      if (currentButton === 'guideline') {
        this.labelState.updateSelectedButton('none');
      } else {
        this.labelState.updateSelectedButton('guideline');
      }
    }
  }
}

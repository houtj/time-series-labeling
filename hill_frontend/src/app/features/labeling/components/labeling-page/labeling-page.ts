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
import { LabelsRepository, UsersRepository, FilesRepository, ProjectsRepository } from '../../../../core/repositories';
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
  styleUrl: './labeling-page.scss'
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
  private readonly autoDetectionService = inject(AutoDetectionService);
  private readonly aiChatService = inject(AiChatService);
  private readonly labelingActions = inject(LabelingActionsService);
  private readonly messageService = inject(MessageService);
  
  private subscriptions = new Subscription();
  
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
    
    // Get data from resolver
    this.subscriptions.add(
      this.route.data.subscribe((routeData) => {
        const resolvedData = routeData['labelingData'];
        if (resolvedData) {
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
          
          // Note: projectInfo is now a computed signal that updates automatically
          // when projectList changes in userState
        }
      })
    );
    
    // Get route parameters
    this.subscriptions.add(
      this.route.paramMap.subscribe(params => {
        this.fileId = params.get('fileId') || undefined;
      })
    );
    
    this.subscriptions.add(
      this.route.queryParamMap.subscribe(params => {
        this.folderId = params.get('folderId') || undefined;
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
}

import { Component, OnInit, OnDestroy, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';

// PrimeNG imports
import { Splitter } from 'primeng/splitter';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

// Core imports
import { UserStateService } from '../../../../core/services';
import { LabelsRepository, UsersRepository } from '../../../../core/repositories';
import { FileModel, FolderModel, LabelModel, ProjectModel, DataModel, UserModel } from '../../../../core/models';

// Feature services
import { LabelStateService, AutoDetectionService } from '../../services';

// Shared services
import { AiChatService } from '../../../../shared/services';

// Shared components
import { ShareDialogComponent, DescriptionDialogComponent } from '../../../../shared/components';

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
    ChartComponent,
    LabelingToolbarComponent,
    EventsPanelComponent,
    GuidelinesPanelComponent,
    AiChatTabComponent,
    AutoDetectionPanelComponent,
    ShareDialogComponent,
    DescriptionDialogComponent
  ],
  standalone: true,
  providers: [MessageService],
  templateUrl: './labeling-page.html',
  styleUrl: './labeling-page.scss'
})
export class LabelingPageComponent implements OnInit, OnDestroy {
  // Injected services
  private readonly route = inject(ActivatedRoute);
  private readonly userState = inject(UserStateService);
  private readonly labelState = inject(LabelStateService);
  private readonly autoDetectionService = inject(AutoDetectionService);
  private readonly aiChatService = inject(AiChatService);
  private readonly labelsRepo = inject(LabelsRepository);
  private readonly usersRepo = inject(UsersRepository);
  private readonly messageService = inject(MessageService);
  
  private subscriptions = new Subscription();
  
  // Dialog visibility
  protected shareDialogVisible = false;
  protected descriptionDialogVisible = false;
  
  // Selected event for description editing
  protected selectedEvent?: LabelModel['events'][0];
  protected selectedEventDescription = '';
  
  // Panel visibility
  protected aiChatVisible = false;
  protected autoDetectionVisible = false;
  
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
  }
  
  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
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
   * Handle save labels
   */
  onSaveLabels(): void {
    if (!this.labelInfo) return;
    
    this.subscriptions.add(
      this.labelsRepo.saveLabel(this.labelInfo).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Labels saved successfully'
          });
        },
        error: (error: any) => {
          console.error('Failed to save labels:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to save labels'
          });
        }
      })
    );
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
    if (!this.folderInfo || !this.userState.userInfo()) return;
    
    const data = {
      folder: this.folderInfo,
      user: event.user,
      userName: this.userState.userInfo()!.name,
      message: event.message
    };
    
    this.subscriptions.add(
      this.usersRepo.shareFolderWithUser(data).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Folder shared successfully'
          });
          this.shareDialogVisible = false;
        },
        error: (error: any) => {
          console.error('Failed to share folder:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to share folder'
          });
          this.shareDialogVisible = false;
        }
      })
    );
  }
  
  /**
   * Handle import labels
   */
  onImportLabels(): void {
    // TODO: Implement import labels functionality
    this.messageService.add({
      severity: 'info',
      summary: 'Info',
      detail: 'Import functionality coming soon'
    });
  }
  
  /**
   * Handle export labels
   */
  onExportLabels(): void {
    // TODO: Implement export labels functionality
    this.messageService.add({
      severity: 'info',
      summary: 'Info',
      detail: 'Export functionality coming soon'
    });
  }
  
  /**
   * Handle download data
   */
  onDownloadData(): void {
    // TODO: Implement download data functionality
    this.messageService.add({
      severity: 'info',
      summary: 'Info',
      detail: 'Download functionality coming soon'
    });
  }
  
  /**
   * Handle edit descriptions
   */
  onEditDescriptions(): void {
    // TODO: Implement edit descriptions functionality (project class descriptions)
    this.messageService.add({
      severity: 'info',
      summary: 'Info',
      detail: 'Edit descriptions functionality coming soon'
    });
  }
  
  /**
   * Handle auto-annotate
   */
  onAutoAnnotate(): void {
    this.autoDetectionVisible = true;
    
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
    
    // Connect to AI chat service if not already connected
    if (!this.aiChatService.isConnected()) {
      this.aiChatService.connectChat(this.fileId!, {
        folderId: this.folderId,
        projectId: this.projectInfo()?._id?.$oid
      });
    }
  }
  
  /**
   * Handle AI chat close
   */
  onAiChatClose(): void {
    this.aiChatVisible = false;
    this.aiChatService.disconnect();
  }
  
  /**
   * Handle auto-detection close
   */
  onAutoDetectionClose(): void {
    this.autoDetectionVisible = false;
    this.autoDetectionService.disconnect();
  }
  
  /**
   * Handle refresh (reload page)
   */
  onRefreshPage(): void {
    window.location.reload();
  }
  
  /**
   * Handle edit event description
   */
  onEditEventDescription(event: { event: LabelModel['events'][0]; index: number }): void {
    this.selectedEvent = event.event;
    this.selectedEventDescription = event.event.description || '';
    this.descriptionDialogVisible = true;
  }
  
  /**
   * Handle save event description
   */
  onSaveEventDescription(newDescription: string): void {
    if (this.selectedEvent) {
      this.selectedEvent.description = newDescription;
      this.descriptionDialogVisible = false;
      
      // Update label in state
      if (this.labelInfo) {
        this.labelState.updateLabel(this.labelInfo);
      }
    }
  }
}

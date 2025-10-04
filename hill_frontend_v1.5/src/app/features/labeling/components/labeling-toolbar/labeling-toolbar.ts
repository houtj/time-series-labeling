import { Component, Input, Output, EventEmitter, inject, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';
import { Select } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';

// Core imports
import { FileModel, FolderModel, LabelModel, ProjectModel, UserModel } from '../../../../core/models';

// Feature services
import { LabelStateService, AutoDetectionService } from '../../services';

// Core services
import { UserStateService } from '../../../../core/services';

/**
 * Labeling Toolbar Component
 * Top toolbar with toggle buttons for label/guideline modes and action buttons
 */
@Component({
  selector: 'app-labeling-toolbar',
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    TooltipModule,
    DialogModule,
    Select,
    InputTextModule
  ],
  standalone: true,
  templateUrl: './labeling-toolbar.html',
  styleUrl: './labeling-toolbar.scss'
})
export class LabelingToolbarComponent {
  @Input() fileId?: string;
  @Input() folderId?: string;
  @Input() fileInfo?: FileModel;
  @Input() folderInfo?: FolderModel;
  @Input() labelInfo?: LabelModel;
  @Input() projectInfo?: ProjectModel;
  
  @Output() onSave = new EventEmitter<void>();
  @Output() onShare = new EventEmitter<void>();
  @Output() onImport = new EventEmitter<void>();
  @Output() onExport = new EventEmitter<void>();
  @Output() onDownload = new EventEmitter<void>();
  @Output() onEditDescriptions = new EventEmitter<void>();
  @Output() onAutoAnnotate = new EventEmitter<void>();
  @Output() onToggleAiChat = new EventEmitter<void>();
  
  private readonly labelState = inject(LabelStateService);
  private readonly autoDetectionService = inject(AutoDetectionService);
  private readonly userState = inject(UserStateService);
  
  // Local toggle button states
  protected labelToggleButton = false;
  protected guidelineToggleButton = false;
  
  // Dialog states
  protected labelSelectionDialogVisible = false;
  protected guidelineSelectionDialogVisible = false;
  
  // Dialog data
  protected selectedClass?: ProjectModel['classes'][0];
  protected selectedEventDescription = '';
  protected selectedYAxis?: { channelName: string; yaxis: string; color: string };
  
  // Get channel list from label state
  protected get channelList(): Array<{ channelName: string; yaxis: string; color: string }> {
    return this.labelState.channelList();
  }
  
  // Auto-annotation state from service
  protected readonly isAutoAnnotationRunning = this.autoDetectionService.isRunning;
  
  // Get class list from project
  protected get classList(): ProjectModel['classes'] {
    return this.projectInfo?.classes || [];
  }
  
  // Get user info
  protected get userInfo(): UserModel | undefined {
    return this.userState.userInfo();
  }
  
  constructor() {
    // Listen for label selection from chart (after two clicks)
    effect(() => {
      const start = this.labelState.labelSelectionStart();
      const end = this.labelState.labelSelectionEnd();
      
      if (start !== undefined && end !== undefined) {
        // Show dialog for class selection
        this.labelSelectionDialogVisible = true;
        this.selectedEventDescription = '';
        
        // Set default class if available
        if (this.classList && this.classList.length > 0) {
          this.selectedClass = this.classList[0];
        }
      }
    });
    
    // Listen for guideline mode activation
    effect(() => {
      const button = this.labelState.selectedButton();
      if (button === 'guideline') {
        // Show dialog for channel selection
        this.guidelineSelectionDialogVisible = true;
        if (this.channelList && this.channelList.length > 0) {
          this.selectedYAxis = this.channelList[0];
        }
      }
    });
    
    // Listen for button state changes and sync with toggle buttons
    effect(() => {
      const button = this.labelState.selectedButton();
      
      // Reset both buttons when mode is cleared
      if (button === 'none') {
        this.labelToggleButton = false;
        this.guidelineToggleButton = false;
      }
      // Only keep the active button pressed
      else if (button === 'label') {
        this.labelToggleButton = true;
        this.guidelineToggleButton = false;
      }
      else if (button === 'guideline') {
        this.labelToggleButton = false;
        this.guidelineToggleButton = true;
      }
    });
  }
  
  /**
   * Handle label toggle button change
   */
  onChangeLabelToggle(event: any): void {
    // Toggle the state
    this.labelToggleButton = !this.labelToggleButton;
    
    if (this.labelToggleButton) {
      this.labelState.updateSelectedButton('label');
      this.guidelineToggleButton = false;
    } else {
      this.labelState.updateSelectedButton('none');
    }
  }
  
  /**
   * Handle guideline toggle button change
   */
  onChangeGuidelineToggle(event: any): void {
    // Toggle the state
    this.guidelineToggleButton = !this.guidelineToggleButton;
    
    if (this.guidelineToggleButton) {
      this.labelState.updateSelectedButton('guideline');
      this.labelToggleButton = false;
    } else {
      this.labelState.updateSelectedButton('none');
    }
  }
  
  /**
   * Handle save button click
   */
  onClickSave(): void {
    this.onSave.emit();
  }
  
  /**
   * Handle share button click
   */
  onClickShare(): void {
    this.onShare.emit();
  }
  
  /**
   * Handle import button click
   */
  onClickImport(): void {
    // Trigger the hidden file input
    document.getElementById('fileImportInput')?.click();
  }
  
  /**
   * Handle file import input change
   */
  onChangeImportInput(event: Event): void {
    this.onImport.emit();
  }
  
  /**
   * Handle export button click
   */
  onClickExport(): void {
    this.onExport.emit();
  }
  
  /**
   * Handle download button click
   */
  onClickDownload(): void {
    this.onDownload.emit();
  }
  
  /**
   * Handle edit descriptions button click
   */
  onClickEditDescriptions(): void {
    this.onEditDescriptions.emit();
  }
  
  /**
   * Handle auto-annotate button click
   */
  onClickAutoAnnotate(): void {
    this.onAutoAnnotate.emit();
  }
  
  /**
   * Handle AI chat toggle button click
   */
  onClickToggleAiChat(): void {
    this.onToggleAiChat.emit();
  }
  
  /**
   * Handle class selection confirmation
   */
  onClickSelectClass(): void {
    if (!this.selectedClass || !this.labelInfo || !this.userInfo) return;
    
    const start = this.labelState.labelSelectionStart();
    const end = this.labelState.labelSelectionEnd();
    
    if (start === undefined || end === undefined) return;
    
    // Create new event
    const newEvent = {
      start,
      end,
      className: this.selectedClass.name,
      color: this.selectedClass.color,
      description: this.selectedEventDescription,
      labeler: this.userInfo.name,
      hide: false
    };
    
    // Add to label info
    this.labelInfo.events.push(newEvent);
    this.labelState.updateLabel(this.labelInfo);
    
    // Clear selection and close dialog
    this.labelState.clearLabelSelection();
    this.labelSelectionDialogVisible = false;
    this.labelState.updateSelectedButton('none');
  }
  
  /**
   * Handle dialog cancel
   */
  onClickDialogCancel(dialogType: 'label' | 'guideline'): void {
    if (dialogType === 'label') {
      this.labelSelectionDialogVisible = false;
      this.labelState.clearLabelSelection();
    } else {
      this.guidelineSelectionDialogVisible = false;
    }
    this.labelState.updateSelectedButton('none');
  }
  
  /**
   * Handle channel selection for guideline
   */
  onClickSelectChannel(): void {
    if (!this.selectedYAxis) return;
    
    this.labelState.setSelectedYAxis(this.selectedYAxis);
    this.guidelineSelectionDialogVisible = false;
  }
}

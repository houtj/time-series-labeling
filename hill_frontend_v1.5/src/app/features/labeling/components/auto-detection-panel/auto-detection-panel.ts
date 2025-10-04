import { Component, Input, Output, EventEmitter, inject, AfterViewChecked, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';

// PrimeNG imports
import { ButtonModule } from 'primeng/button';

// Feature services
import { AutoDetectionService } from '../../services';

// Feature models
import { ToolbarAction } from '../../models/toolbar-action.model';

/**
 * Auto-Detection Panel Component
 * Interface for auto-annotation agent
 */
@Component({
  selector: 'app-auto-detection-panel',
  imports: [
    CommonModule,
    ButtonModule
  ],
  standalone: true,
  templateUrl: './auto-detection-panel.html',
  styleUrl: './auto-detection-panel.scss'
})
export class AutoDetectionPanelComponent implements AfterViewChecked {
  @ViewChild('inferenceLog') inferenceLogElement?: ElementRef;
  
  @Input() fileId?: string;
  @Input() folderId?: string;
  @Input() projectId?: string;
  
  @Output() onClose = new EventEmitter<void>();
  
  private readonly autoDetectionService = inject(AutoDetectionService);
  private shouldScrollToBottom = false;
  
  // Auto-detection state from service
  protected readonly isRunning = this.autoDetectionService.isRunning;
  protected readonly inferenceHistory = this.autoDetectionService.inferenceHistory;
  
  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }
  
  /**
   * Get toolbar actions for this panel
   * Called by parent to render buttons in tab header
   */
  getToolbarActions(): ToolbarAction[] {
    const actions: ToolbarAction[] = [];
    
    // Start/Stop button (conditional)
    if (this.isRunning()) {
      actions.push({
        icon: 'pi pi-stop',
        label: 'Stop',
        severity: 'danger',
        action: () => this.onClickStopAutoAnnotation()
      });
    } else {
      actions.push({
        icon: 'pi pi-play',
        label: 'Start',
        severity: 'success',
        action: () => this.onClickStartAutoAnnotation()
      });
    }
    
    // Clear and Close buttons
    actions.push(
      {
        icon: 'pi pi-trash',
        label: 'Clear Log',
        action: () => this.onClearLog()
      },
      {
        icon: 'pi pi-times',
        label: 'Close',
        action: () => this.onClose.emit()
      }
    );
    
    return actions;
  }
  
  /**
   * Start auto-annotation
   */
  onClickStartAutoAnnotation(): void {
    if (!this.fileId || !this.folderId || !this.projectId) {
      console.error('Missing required IDs for auto-annotation');
      return;
    }
    
    this.autoDetectionService.startAutoAnnotation(
      this.fileId,
      this.folderId,
      this.projectId
    );
    this.shouldScrollToBottom = true;
  }
  
  /**
   * Stop auto-annotation
   */
  onClickStopAutoAnnotation(): void {
    this.autoDetectionService.stopAutoAnnotation();
  }
  
  /**
   * Clear inference log
   */
  onClickClearLog(): void {
    this.autoDetectionService.clearInferenceHistory();
  }
  
  /**
   * Clear log (alias for toolbar)
   */
  onClearLog(): void {
    this.onClickClearLog();
  }
  
  /**
   * Handle close button
   */
  onClickClose(): void {
    this.onClose.emit();
  }
  
  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: Date): string {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  }
  
  /**
   * Format details object for display
   */
  formatDetails(details: any): string {
    if (!details) return '';
    if (typeof details === 'string') return details;
    return JSON.stringify(details, null, 2);
  }
  
  /**
   * Get icon for log entry type
   */
  getLogIcon(type: string): string {
    switch (type) {
      case 'agent-header':
        return 'pi pi-robot';
      case 'sent-message':
        return 'pi pi-arrow-up';
      case 'received-message':
        return 'pi pi-arrow-down';
      case 'info':
        return 'pi pi-info-circle';
      case 'warning':
        return 'pi pi-exclamation-triangle';
      case 'error':
        return 'pi pi-times-circle';
      case 'success':
        return 'pi pi-check-circle';
      default:
        return 'pi pi-circle';
    }
  }
  
  /**
   * Scroll log to bottom
   */
  private scrollToBottom(): void {
    if (this.inferenceLogElement) {
      const element = this.inferenceLogElement.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }
}

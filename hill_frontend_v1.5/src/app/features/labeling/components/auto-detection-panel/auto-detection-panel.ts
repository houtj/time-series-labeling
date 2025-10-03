import { Component, Input, Output, EventEmitter, inject, AfterViewChecked, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';

// Feature services
import { AutoDetectionService } from '../../services';

/**
 * Auto-Detection Panel Component
 * Interface for auto-annotation agent
 */
@Component({
  selector: 'app-auto-detection-panel',
  imports: [
    CommonModule,
    CardModule,
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

import { Injectable, signal, inject } from '@angular/core';
import { WebSocketBaseService } from '../../../core/services/websocket/websocket-base.service';
import { environment } from '../../../../environments/environment';

/**
 * Auto-Detection Service
 * Handles WebSocket communication for auto-annotation agent
 */
@Injectable({
  providedIn: 'root'
})
export class AutoDetectionService extends WebSocketBaseService {
  // State
  readonly isRunning = signal<boolean>(false);
  readonly inferenceHistory = signal<any[]>([]);
  
  constructor() {
    super();
  }

  /**
   * Connect to auto-detection WebSocket
   */
  connectAutoDetection(fileId: string, folderId: string): void {
    const wsUrl = `${environment.wsUrl}/auto-detection/${fileId}`;
    this.connect(wsUrl);
  }

  /**
   * Start auto-annotation process
   */
  startAutoAnnotation(fileId: string, folderId: string, projectId: string): void {
    if (this.isConnected()) {
      this.isRunning.set(true);
      
      const message = {
        action: 'start',
        fileId,
        folderId,
        projectId,
        timestamp: new Date().toISOString()
      };
      
      this.send(JSON.stringify(message));
      
      this.addInferenceLog({
        type: 'agent-header',
        message: '🚀 Starting auto-annotation agent...',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Stop auto-annotation process
   */
  stopAutoAnnotation(): void {
    if (this.isConnected()) {
      this.send(JSON.stringify({ action: 'stop' }));
      this.isRunning.set(false);
      
      this.addInferenceLog({
        type: 'info',
        message: '⏹️ Auto-annotation stopped by user',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  protected override onMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      // Add to inference history
      this.addInferenceLog({
        type: data.type || 'received-message',
        message: data.message || event.data,
        details: data.details,
        timestamp: new Date().toISOString()
      });
      
      // Check if annotation is complete
      if (data.type === 'complete' || data.status === 'complete') {
        this.isRunning.set(false);
        this.addInferenceLog({
          type: 'success',
          message: '✅ Auto-annotation completed successfully',
          timestamp: new Date().toISOString()
        });
      }
      
      // Check for errors
      if (data.type === 'error') {
        this.isRunning.set(false);
        this.addInferenceLog({
          type: 'error',
          message: `❌ Error: ${data.message}`,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Failed to parse auto-detection message:', error);
    }
  }

  /**
   * Handle WebSocket errors
   */
  protected override onError(event: Event): void {
    super.onError(event);
    this.isRunning.set(false);
    this.addInferenceLog({
      type: 'error',
      message: '❌ WebSocket connection error',
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Handle WebSocket close
   */
  protected override onClose(event: CloseEvent): void {
    super.onClose(event);
    this.isRunning.set(false);
  }

  /**
   * Add log entry to inference history
   */
  private addInferenceLog(log: any): void {
    this.inferenceHistory.update(history => [...history, log]);
  }

  /**
   * Clear inference history
   */
  clearInferenceHistory(): void {
    this.inferenceHistory.set([]);
  }

  /**
   * Get formatted inference history for display
   */
  getFormattedHistory(): any[] {
    return this.inferenceHistory();
  }

  /**
   * Disconnect and cleanup
   */
  override disconnect(): void {
    this.isRunning.set(false);
    super.disconnect();
  }
}


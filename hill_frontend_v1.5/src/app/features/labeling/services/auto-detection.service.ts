import { Injectable, signal, inject } from '@angular/core';
import { WebSocketBaseService } from '../../../core/services/websocket/websocket-base.service';
import { environment } from '../../../../environments/environment';
import { ChartService } from './chart.service';

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
  
  private readonly chartService = inject(ChartService);
  
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
        command: 'start_auto_detection',
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
      this.send(JSON.stringify({ command: 'cancel_auto_detection' }));
      this.isRunning.set(false);
      
      // Remove view-sync shapes when stopping
      this.chartService.removeViewSyncShapes();
      
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
      
      // Handle plot view synchronization
      if (data.type === 'plot_view_sync' && data.data) {
        const { start_idx, end_idx, agent } = data.data;
        if (typeof start_idx === 'number' && typeof end_idx === 'number') {
          // Zoom the chart to the agent's current view window
          this.chartService.zoomToRange(start_idx, end_idx);
          
          // Log the view sync for transparency
          this.addInferenceLog({
            type: 'view-sync',
            message: `🔍 ${agent} is analyzing data range [${start_idx}, ${end_idx}]`,
            timestamp: new Date().toISOString()
          });
        }
        return; // Don't add to general history
      }
      
      // Format message based on type
      const formattedLog = this.formatMessage(data);
      if (formattedLog) {
        this.addInferenceLog(formattedLog);
      }
      
      // Update running state based on message type
      if (data.type === 'detection_completed' || data.type === 'detection_failed') {
        this.isRunning.set(false);
      }
    } catch (error) {
      console.error('Failed to parse auto-detection message:', error);
    }
  }
  
  /**
   * Format incoming messages for human-readable display
   */
  private formatMessage(data: any): any | null {
    const timestamp = new Date().toISOString();
    const messageData = data.data || {};
    
    switch (data.type) {
      case 'detection_started':
        return {
          type: 'info',
          message: '🚀 Starting multi-agent event detection system...',
          timestamp
        };
        
      case 'analysis_started':
        return {
          type: 'info',
          message: '🔬 Multi-agent analysis initiated - Planner → Identifier → Validator',
          timestamp
        };
        
      case 'analysis_progress':
        // Show progress updates
        return {
          type: 'info',
          message: `⚙️ ${messageData.message || 'Analysis in progress...'}`,
          details: messageData.token_usage ? { token_usage: messageData.token_usage } : undefined,
          timestamp
        };
        
      case 'analysis_completed':
        return {
          type: 'success',
          message: `✅ Analysis completed - Found ${messageData.events_found || 0} potential events`,
          timestamp
        };
        
      case 'detection_completed':
        // Remove view-sync shapes when detection completes
        this.chartService.removeViewSyncShapes();
        return {
          type: 'success',
          message: `🎉 Detection completed successfully! Saved ${messageData.total_events || 0} events to database`,
          timestamp
        };
        
      case 'detection_failed':
        // Remove view-sync shapes when detection fails
        this.chartService.removeViewSyncShapes();
        return {
          type: 'error',
          message: `❌ Detection failed: ${messageData.message || 'Unknown error'}`,
          timestamp
        };
        
      case 'events_saved':
        return {
          type: 'success',
          message: `💾 Saved ${messageData.events_count || 0} auto-detected events`,
          timestamp
        };
        
      case 'llm_interaction':
        // Format agent reasoning with clear labels
        const agent = messageData.agent || 'Agent';
        const agentIcon = this.getAgentIcon(agent);
        const tokenInfo = messageData.token_usage ? ` • ${messageData.token_usage} tokens` : '';
        
        return {
          type: 'agent-reasoning',
          message: `${agentIcon} ${agent} Agent Reasoning${tokenInfo}`,
          details: {
            '📤 Sent to LLM': messageData.sent_message || 'N/A',
            '📥 Received from LLM': messageData.received_message || 'N/A',
            'Total Token Usage': messageData.total_token_usage || messageData.token_usage || 0
          },
          timestamp
        };
        
      case 'error':
        this.isRunning.set(false);
        // Remove view-sync shapes on error
        this.chartService.removeViewSyncShapes();
        return {
          type: 'error',
          message: `❌ Error: ${messageData.message || 'Unknown error'}`,
          timestamp
        };
        
      default:
        // Handle unknown message types gracefully
        if (messageData.message) {
          return {
            type: 'info',
            message: messageData.message,
            timestamp
          };
        }
        return null;
    }
  }
  
  /**
   * Get emoji icon for specific agent
   */
  private getAgentIcon(agent: string): string {
    switch (agent.toLowerCase()) {
      case 'planner':
        return '📋';
      case 'identifier':
        return '🔍';
      case 'validator':
        return '✓';
      default:
        return '🤖';
    }
  }

  /**
   * Handle WebSocket errors
   */
  protected override onError(event: Event): void {
    super.onError(event);
    this.isRunning.set(false);
    
    // Remove view-sync shapes on WebSocket error
    this.chartService.removeViewSyncShapes();
    
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
    
    // Remove view-sync shapes when WebSocket closes
    this.chartService.removeViewSyncShapes();
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
    
    // Remove view-sync shapes when disconnecting
    this.chartService.removeViewSyncShapes();
    
    super.disconnect();
  }
}


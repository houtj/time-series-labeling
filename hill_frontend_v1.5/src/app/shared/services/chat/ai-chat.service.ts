import { Injectable, signal, inject } from '@angular/core';
import { WebSocketBaseService } from '../../../core/services/websocket/websocket-base.service';
import { environment } from '../../../../environments/environment';
import { Subject } from 'rxjs';

/**
 * AI Chat Service
 * Handles WebSocket communication for AI assistant chat
 * Shared service used by multiple pages (labeling, etc.)
 */
@Injectable({
  providedIn: 'root'
})
export class AiChatService extends WebSocketBaseService {
  // State
  readonly chatHistory = signal<any[]>([]);
  readonly isWaitingForResponse = signal<boolean>(false);
  readonly currentMessage = signal<string>('');
  
  // Observable for label updates (when AI adds events/guidelines)
  readonly labelUpdated$ = new Subject<void>();
  
  constructor() {
    super();
  }

  /**
   * Connect to AI chat WebSocket
   */
  connectChat(fileId: string, context?: { folderId?: string; projectId?: string }): void {
    const wsUrl = `${environment.wsUrl}/chat/${fileId}`;
    this.connect(wsUrl);
    
    // Send context if provided
    if (context && this.isConnected()) {
      this.send(JSON.stringify({
        action: 'set-context',
        context: { fileId, ...context }
      }));
    }
  }

  /**
   * Send a chat message
   */
  sendMessage(message: string): void {
    if (!this.isConnected()) {
      console.error('WebSocket is not connected');
      return;
    }

    this.isWaitingForResponse.set(true);
    this.currentMessage.set('');
    
    // Add user message to history
    this.addChatMessage({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });
    
    // Send to server
    this.send(JSON.stringify({
      action: 'chat',
      message,
      timestamp: new Date().toISOString()
    }));
  }

  /**
   * Handle incoming WebSocket messages
   */
  protected override onMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      switch (data.type) {
        case 'user_message_received':
          // Message was received and processed by backend
          break;
          
        case 'ai_response':
          // Backend sends the full message object
          this.addChatMessage(data.message);
          this.isWaitingForResponse.set(false);
          break;
          
        case 'event_added':
          // New event was added by AI
          this.addChatMessage({
            role: 'system',
            content: `✅ ${data.data.message}`,
            timestamp: new Date().toISOString()
          });
          // Notify labeling page to reload label data
          this.labelUpdated$.next();
          break;
          
        case 'guideline_added':
          // New guideline was added by AI
          this.addChatMessage({
            role: 'system',
            content: `✅ ${data.data.message}`,
            timestamp: new Date().toISOString()
          });
          // Notify labeling page to reload label data
          this.labelUpdated$.next();
          break;
          
        case 'data_updated':
          // AI has updated the labels/guidelines
          this.addChatMessage({
            role: 'system',
            content: `✅ ${data.message}`,
            timestamp: new Date().toISOString()
          });
          break;
          
        case 'error':
          this.addChatMessage({
            role: 'system',
            content: `❌ Error: ${data.message}`,
            timestamp: new Date().toISOString()
          });
          this.isWaitingForResponse.set(false);
          break;
          
        case 'thinking':
          // Optional: show typing indicator
          break;
          
        default:
          console.log('Unknown message type:', data);
      }
    } catch (error) {
      console.error('Failed to parse chat message:', error);
      this.isWaitingForResponse.set(false);
    }
  }

  /**
   * Handle WebSocket errors
   */
  protected override onError(event: Event): void {
    super.onError(event);
    this.isWaitingForResponse.set(false);
    this.addChatMessage({
      role: 'system',
      content: 'Connection error. Please try again.',
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Handle WebSocket close
   */
  protected override onClose(event: CloseEvent): void {
    super.onClose(event);
    this.isWaitingForResponse.set(false);
  }

  /**
   * Add message to chat history
   */
  private addChatMessage(message: any): void {
    this.chatHistory.update(history => [...history, message]);
  }

  /**
   * Clear chat history
   */
  clearChatHistory(): void {
    this.chatHistory.set([]);
  }

  /**
   * Update current message
   */
  updateCurrentMessage(message: string): void {
    this.currentMessage.set(message);
  }

  /**
   * Get formatted chat history for display
   */
  getFormattedHistory(): any[] {
    return this.chatHistory();
  }

  /**
   * Disconnect and cleanup
   */
  override disconnect(): void {
    this.isWaitingForResponse.set(false);
    super.disconnect();
  }
}


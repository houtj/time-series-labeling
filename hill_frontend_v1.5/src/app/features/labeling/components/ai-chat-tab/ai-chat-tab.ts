import { Component, Output, EventEmitter, inject, AfterViewChecked, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';

// Shared services
import { AiChatService } from '../../../../shared/services';

/**
 * AI Chat Tab Component
 * Chat interface for AI assistant
 */
@Component({
  selector: 'app-ai-chat-tab',
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule
  ],
  standalone: true,
  templateUrl: './ai-chat-tab.html',
  styleUrl: './ai-chat-tab.scss'
})
export class AiChatTabComponent implements AfterViewChecked {
  @ViewChild('chatMessages') chatMessagesElement?: ElementRef;
  
  @Output() onClose = new EventEmitter<void>();
  
  private readonly aiChatService = inject(AiChatService);
  private shouldScrollToBottom = false;
  
  // Chat state from service
  protected readonly chatHistory = this.aiChatService.chatHistory;
  protected readonly isWaitingForResponse = this.aiChatService.isWaitingForResponse;
  protected currentMessage = '';
  
  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }
  
  /**
   * Send message to AI assistant
   */
  onClickSendMessage(): void {
    if (!this.currentMessage.trim() || this.isWaitingForResponse()) return;
    
    this.aiChatService.sendMessage(this.currentMessage);
    this.currentMessage = '';
    this.shouldScrollToBottom = true;
  }
  
  /**
   * Handle keyboard shortcuts
   */
  onChatInputKeydown(event: KeyboardEvent): void {
    // Send on Enter (without Shift)
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onClickSendMessage();
    }
  }
  
  /**
   * Clear chat history
   */
  onClickClearChat(): void {
    this.aiChatService.clearChatHistory();
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
      minute: '2-digit' 
    });
  }
  
  /**
   * Scroll chat to bottom
   */
  private scrollToBottom(): void {
    if (this.chatMessagesElement) {
      const element = this.chatMessagesElement.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }
}

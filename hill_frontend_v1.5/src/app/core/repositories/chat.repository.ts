import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { ChatConversation, ChatMessage } from '../models';

/**
 * Chat Repository
 * Handles all chat conversation data access
 */
@Injectable({
  providedIn: 'root'
})
export class ChatRepository extends BaseRepository<ChatConversation> {
  protected readonly basePath = '/conversations/chat';

  /**
   * Get chat conversation for file
   */
  getChatConversation(fileId: string): Observable<ChatConversation> {
    return this.apiService.get<string>(`${this.basePath}/${fileId}`).pipe(
      map(response => this.parseResponse<ChatConversation>(response))
    );
  }

  /**
   * Clear chat conversation for file
   */
  clearChatConversation(fileId: string): Observable<string> {
    return this.apiService.delete(`${this.basePath}/${fileId}`);
  }

  /**
   * Get recent messages for file
   */
  getRecentMessages(fileId: string, limit: number = 10): Observable<ChatMessage[]> {
    const params = this.buildParams({ limit });
    return this.apiService.get<string>(`${this.basePath}/${fileId}/messages/recent`, params).pipe(
      map(response => this.parseResponse<ChatMessage[]>(response))
    );
  }
}


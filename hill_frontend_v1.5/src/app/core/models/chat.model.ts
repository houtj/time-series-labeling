import { BaseModel } from './common.model';

/**
 * Chat message role
 */
export type ChatRole = 'user' | 'assistant' | 'system';

/**
 * Individual chat message
 */
export interface ChatMessage {
  role: ChatRole;
  content: string;
  timestamp: string;
}

/**
 * Chat conversation model
 */
export interface ChatConversation extends BaseModel {
  fileId: string;
  messages: ChatMessage[];
  createdAt?: string;
  updatedAt?: string;
}



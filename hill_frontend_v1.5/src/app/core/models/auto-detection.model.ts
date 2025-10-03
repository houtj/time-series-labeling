import { BaseModel } from './common.model';

/**
 * Auto-detection message type
 */
export type AutoDetectionMessageType = 'status' | 'progress' | 'result' | 'error';

/**
 * Auto-detection status
 */
export type AutoDetectionStatus = 
  | 'idle' 
  | 'started' 
  | 'planning' 
  | 'identifying' 
  | 'validating' 
  | 'completed' 
  | 'failed';

/**
 * Auto-detection message from WebSocket
 */
export interface AutoDetectionMessage {
  type: AutoDetectionMessageType;
  status: string;
  message: string;
  timestamp: string;
  eventsDetected?: number;
  summary?: string;
  error?: string;
}

/**
 * Auto-detection conversation model
 */
export interface AutoDetectionConversation extends BaseModel {
  fileId: string;
  messages: AutoDetectionMessage[];
  status: AutoDetectionStatus;
  createdAt?: string;
  updatedAt?: string;
}



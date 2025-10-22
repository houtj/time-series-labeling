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
 * Plan item for auto-detection
 */
export interface PlanItem {
  task_id: string;
  task_description: string;
  task_type: 'identification' | 'verification';
  is_done: boolean;
}

/**
 * Auto-detection conversation model
 */
export interface AutoDetectionConversation extends BaseModel {
  fileId: string;
  messages: AutoDetectionMessage[];
  status: AutoDetectionStatus;
  plan?: PlanItem[];
  createdAt?: string;
  updatedAt?: string;
}



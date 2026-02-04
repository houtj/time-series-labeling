import { BaseModel, MongoDate } from './common.model';

/**
 * File model representing a data file for labeling
 */
export interface FileModel extends BaseModel {
  name: string;
  parsing: string;
  nbEvent: string;
  description: string;
  rawPath: string;
  jsonPath: string;
  label: string;
  lastUpdate: MongoDate;
  lastModifier: string;
  inputVisible?: boolean;
  chatConversationId?: string;
  autoDetectionConversationId?: string;
  
  // Large dataset optimization fields
  useBinaryFormat?: boolean;
  binaryPath?: string;
  metaPath?: string;
  overviewPath?: string;
  totalPoints?: number;
  
  // X-axis metadata for timestamp handling
  xType?: 'timestamp' | 'numeric';
  xFormat?: string;  // strftime format for display
  xMin?: number;     // Min x value (timestamp or numeric)
  xMax?: number;     // Max x value (timestamp or numeric)
}



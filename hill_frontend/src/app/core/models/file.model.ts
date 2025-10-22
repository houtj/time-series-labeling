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
}



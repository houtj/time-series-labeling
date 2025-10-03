import { BaseModel } from './common.model';

/**
 * X-axis configuration for data parsing
 */
export interface XAxisConfig {
  name: string;
  regex: string;
  isTime: boolean;
  unit: string;
}

/**
 * Channel configuration for data parsing
 */
export interface ChannelConfig {
  channelName: string;
  color: string;
  regex: string;
  mandatory: boolean;
  unit: string;
}

/**
 * Template model for parsing different file types
 */
export interface TemplateModel extends BaseModel {
  fileType: string;
  templateName: string;
  sheetName: string;
  headRow: number;
  skipRow: number;
  x: XAxisConfig;
  channels: ChannelConfig[];
}

/**
 * Assistant model for auto-detection
 */
export interface AssistantModel extends BaseModel {
  name: string;
  version: number;
  accuracy: number;
  projectName: string;
}



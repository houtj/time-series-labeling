import { BaseModel } from './common.model';

/**
 * Labeled event
 */
export interface LabeledEvent {
  className: string;
  color: string;
  description: string;
  labeler: string;
  start: string | number;
  end: string | number;
  hide: boolean;
}

/**
 * Guideline marker on chart
 */
export interface Guideline {
  yaxis: string; // Plotly.YAxisName | 'paper'
  y: string | number; // Plotly.Datum
  channelName: string;
  color: string;
  hide: boolean;
}

/**
 * Label model containing events and guidelines for a file
 */
export interface LabelModel extends BaseModel {
  events: LabeledEvent[];
  guidelines: Guideline[];
}

/**
 * Data model for chart rendering
 */
export interface DataModel {
  x: boolean;
  name: string;
  unit: string;
  color: string;
  data: string[] | number[];
}



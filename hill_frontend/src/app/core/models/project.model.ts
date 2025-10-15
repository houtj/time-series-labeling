import { BaseModel } from './common.model';

/**
 * Template reference in project
 */
export interface ProjectTemplateReference {
  id: string;
  name: string;
  fileType: string;
}

/**
 * Event class definition
 */
export interface EventClass {
  name: string;
  color: string;
  description: string;
}

/**
 * Project model representing a labeling project
 */
export interface ProjectModel extends BaseModel {
  projectName: string;
  templates: ProjectTemplateReference[];
  classes: EventClass[];
  general_pattern_description: string;
}



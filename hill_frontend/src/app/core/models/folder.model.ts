import { BaseModel } from './common.model';

/**
 * Project reference within a folder
 */
export interface ProjectReference {
  id: string;
  name: string;
}

/**
 * Template reference within a folder
 */
export interface TemplateReference {
  id: string;
  name: string;
}

/**
 * Folder model representing a collection of files
 */
export interface FolderModel extends BaseModel {
  name: string;
  project: ProjectReference;
  template: TemplateReference;
  nbLabeledFiles: number;
  nbTotalFiles: number;
  fileList: string[];
}



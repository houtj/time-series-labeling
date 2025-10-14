import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseRepository } from './base.repository';
import { TemplateModel } from '../models';

/**
 * Templates Repository
 * Handles all template-related data access
 */
@Injectable({
  providedIn: 'root'
})
export class TemplatesRepository extends BaseRepository<TemplateModel> {
  protected readonly basePath = '/templates';

  /**
   * Get multiple templates by IDs
   */
  getTemplates(templateIds: string[]): Observable<TemplateModel[]> {
    const params = this.buildParams({ templates: JSON.stringify(templateIds) });
    return this.getAll(params);
  }

  /**
   * Get single template by ID
   */
  getTemplate(templateId: string): Observable<TemplateModel> {
    return this.getById(templateId);
  }

  /**
   * Create new template
   */
  createTemplate(data: {
    projectId: string;
    templateName: string;
    fileType: string;
  }): Observable<string> {
    return this.apiService.post(this.basePath, data);
  }

  /**
   * Delete template
   */
  deleteTemplate(templateId: string, projectId: string): Observable<string> {
    const params = this.buildParams({ templateId, projectId });
    return this.apiService.delete(this.basePath, params);
  }

  /**
   * Update template
   */
  updateTemplate(projectId: string, template: TemplateModel): Observable<string> {
    return this.apiService.put(this.basePath, {
      projectId,
      request: template
    });
  }
  
  /**
   * Clone template
   */
  cloneTemplate(data: {
    projectId: string;
    templateId: string;
    newTemplateName: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/clone`, data);
  }
  
  /**
   * Extract columns from file
   */
  extractColumns(file: File, templateId: string): Observable<{ columns: any[] }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('templateId', templateId);
    return this.apiService.post(`${this.basePath}/extract-columns`, formData);
  }
}


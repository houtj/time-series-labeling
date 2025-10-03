import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { BaseRepository } from './base.repository';
import { ProjectModel } from '../models';

/**
 * Projects Repository
 * Handles all project-related data access
 */
@Injectable({
  providedIn: 'root'
})
export class ProjectsRepository extends BaseRepository<ProjectModel> {
  protected readonly basePath = '/projects';

  /**
   * Get multiple projects by IDs
   */
  getProjects(projectIds: string[]): Observable<ProjectModel[]> {
    const params = this.buildParams({ projects: JSON.stringify(projectIds) });
    return this.getAll(params);
  }

  /**
   * Get single project by ID
   */
  getProject(projectId: string): Observable<ProjectModel> {
    return this.getById(projectId);
  }

  /**
   * Create new project
   */
  createProject(data: {
    projectName: string;
    userId: string;
  }): Observable<string> {
    return this.create(data);
  }

  /**
   * Delete project
   */
  deleteProject(project: ProjectModel): Observable<string> {
    const params = this.buildParams({ project: JSON.stringify(project) });
    return this.apiService.delete(this.basePath, params);
  }

  /**
   * Update project description
   */
  updateDescription(projectId: string, description: string): Observable<string> {
    return this.apiService.put(`${this.basePath}/description`, {
      projectId,
      description
    });
  }

  /**
   * Add class to project
   */
  addClass(projectId: string, classData: {
    name: string;
    color: string;
    description: string;
  }): Observable<string> {
    return this.apiService.post(`${this.basePath}/classes`, {
      projectId,
      newClassName: classData.name,
      newClassColor: classData.color,
      description: classData.description
    });
  }

  /**
   * Update class in project
   */
  updateClass(projectId: string, className: string, updates: {
    newName?: string;
    color?: string;
    description?: string;
  }): Observable<string> {
    return this.apiService.put(`${this.basePath}/classes`, {
      projectId,
      updatingClassName: className,
      newClassName: updates.newName || className,
      newClassColor: updates.color || '#000000',
      description: updates.description || ''
    });
  }

  /**
   * Delete class from project
   */
  deleteClass(projectId: string, className: string): Observable<string> {
    return this.apiService.delete(`${this.basePath}/classes`, {
      projectId,
      className
    });
  }
}


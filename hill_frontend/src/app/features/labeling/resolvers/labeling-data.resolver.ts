import { inject } from '@angular/core';
import { ResolveFn, ActivatedRouteSnapshot } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { map, catchError, switchMap } from 'rxjs/operators';

// Core imports
import { UserStateService } from '../../../core/services';
import { FilesRepository, FoldersRepository, LabelsRepository, ProjectsRepository, UsersRepository } from '../../../core/repositories';
import { FileModel, FolderModel, LabelModel, DataModel } from '../../../core/models';

/**
 * Labeling Data Resolver
 * Pre-loads all necessary data before navigating to the labeling page
 * Ensures file, folder, label, and data are available
 */
export interface LabelingResolverData {
  file: FileModel;
  folder: FolderModel;
  label: LabelModel;
  data: DataModel[];
}

export const labelingDataResolver: ResolveFn<LabelingResolverData | null> = (
  route: ActivatedRouteSnapshot
) => {
  const filesRepo = inject(FilesRepository);
  const foldersRepo = inject(FoldersRepository);
  const labelsRepo = inject(LabelsRepository);
  const projectsRepo = inject(ProjectsRepository);
  const usersRepo = inject(UsersRepository);
  const userState = inject(UserStateService);

  // Get IDs from route parameters
  const fileId = route.paramMap.get('fileId');
  const folderId = route.queryParamMap.get('folderId');

  if (!fileId || !folderId) {
    console.error('Missing fileId or folderId in route');
    return of(null);
  }

  // Load user info first (if not already loaded), then load projects
  // This ensures projectInfo will be available for the toolbar
  return (userState.userInfo() 
    ? of(userState.userInfo()!) 
    : usersRepo.getUserInfo().pipe(
        map(user => {
          userState.setUserInfo(user);
          return user;
        })
      )
  ).pipe(
    // Then load projects if not already loaded
    switchMap(user => {
      if (userState.projectList().length > 0) {
        return of(null); // Projects already loaded
      }
      
      // Load projects if user has any
      if (user.projectList && user.projectList.length > 0) {
        return projectsRepo.getProjects(user.projectList).pipe(
          map(projects => {
            userState.setProjectList(projects);
            return null;
          }),
          catchError(error => {
            console.error('Failed to load projects:', error);
            return of(null);
          })
        );
      }
      
      return of(null);
    }),
    // Now load file data
    switchMap(() => filesRepo.getFile(fileId)),
    catchError(error => {
      console.error('Failed to load file:', error);
      return of(null);
    }),
    switchMap(fileData => {
      if (!fileData) {
        return of(null);
      }

      const file = fileData.fileInfo;
      const labelId = file.label;

      // Now load folder and label in parallel
      return forkJoin({
        fileData: of(fileData),
        folder: foldersRepo.getFolder(folderId).pipe(
          catchError(error => {
            console.error('Failed to load folder:', error);
            return of(null as any);
          })
        ),
        label: labelsRepo.getLabel(labelId).pipe(
          catchError(error => {
            console.error('Failed to load label:', error);
            // Return empty label if not found
            return of({
              _id: { $oid: '' },
              fileId: { $oid: fileId },
              events: [],
              guidelines: []
            } as LabelModel);
          })
        )
      });
    }),
  ).pipe(
    map(result => {
      if (!result || !result.fileData || !result.folder) {
        return null;
      }

      const file = result.fileData.fileInfo;
      const data = result.fileData.data;

      // Update user state with loaded data
      userState.selectFolder(result.folder);
      userState.selectFile(file);
      userState.setSelectedLabel(result.label);
      userState.setSelectedData(data);

      return {
        file,
        folder: result.folder,
        label: result.label,
        data
      };
    }),
    catchError(error => {
      console.error('Failed to resolve labeling data:', error);
      return of(null);
    })
  );
};


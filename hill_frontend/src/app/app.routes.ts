import { Routes } from '@angular/router';
import { labelingDataResolver } from './features/labeling/resolvers';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/folders',
    pathMatch: 'full'
  },
  {
    path: 'folders',
    loadComponent: () => import('./features/folders/folders-page/folders-page').then(m => m.FoldersPageComponent)
  },
  {
    path: 'files/:folderId',
    loadComponent: () => import('./features/files/components/files-page/files-page').then(m => m.FilesPageComponent)
  },
  {
    path: 'labeling/:fileId',
    loadComponent: () => import('./features/labeling/components/labeling-page/labeling-page').then(m => m.LabelingPageComponent),
    resolve: {
      labelingData: labelingDataResolver
    }
  },
  {
    path: 'projects',
    loadComponent: () => import('./features/projects/components/projects-page/projects-page').then(m => m.ProjectsPageComponent)
  },
  {
    path: 'profile',
    loadComponent: () => import('./features/profile/profile-page/profile-page').then(m => m.ProfilePageComponent)
  },
  {
    path: 'contact',
    loadComponent: () => import('./features/contact/contact-page/contact-page').then(m => m.ContactPageComponent)
  },
  {
    path: 'manual',
    loadComponent: () => import('./features/manual/manual-page/manual-page').then(m => m.ManualPageComponent)
  }
];

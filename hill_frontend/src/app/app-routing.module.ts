import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProfilePageComponent } from './profile-page/profile-page.component';
import { LabelingPageComponent } from './labeling-page/labeling-page.component';
import { FilesPageComponent } from './files-page/files-page.component';
import { ProjectPageComponent } from './project-page/project-page.component';
import { FoldersPageComponent } from './folders-page/folders-page.component';
import { ContactPageComponent } from './contact-page/contact-page.component';
import { ManualPageComponent } from './manual-page/manual-page.component';

const routes: Routes = [
  {
    path: 'profile',
    component: ProfilePageComponent,
  },
  {
    path: 'labeling',
    component: LabelingPageComponent,
  },
  {
    path: 'files',
    component: FilesPageComponent,
  },
  {
    path: 'folders',
    component: FoldersPageComponent,
  },
  {
    path: 'manual',
    component: ManualPageComponent,
  },
  {
    path: '',
    component: FoldersPageComponent,
  },
  {
    path: 'projects',
    component: ProjectPageComponent,
  },
  {
    path: 'contact',
    component: ContactPageComponent,
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }

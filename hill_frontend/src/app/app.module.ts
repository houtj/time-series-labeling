import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import {BrowserAnimationsModule, NoopAnimationsModule} from '@angular/platform-browser/animations'

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { ProfilePageComponent } from './profile-page/profile-page.component';
import { FilesPageComponent } from './files-page/files-page.component';
import { LabelingPageComponent } from './labeling-page/labeling-page.component';

import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { environment } from '../environments/environment';

import { ToolbarModule } from 'primeng/toolbar';
import { AvatarModule } from 'primeng/avatar';
import { AvatarGroupModule } from 'primeng/avatargroup';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { FormsModule } from '@angular/forms';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ConfirmationService } from 'primeng/api';
import { CheckboxModule } from 'primeng/checkbox';
import { ColorPickerModule } from 'primeng/colorpicker';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { SpeedDialModule } from 'primeng/speeddial';
import { FileUploadModule } from 'primeng/fileupload';
import { ProjectPageComponent } from './project-page/project-page.component';
import { FoldersPageComponent } from './folders-page/folders-page.component';
import { ToggleButtonModule } from 'primeng/togglebutton';
import { MenuModule } from 'primeng/menu';
import { ContactPageComponent } from './contact-page/contact-page.component';
import { ManualPageComponent } from './manual-page/manual-page.component';
import { DescriptionDialogComponent } from './description-dialog/description-dialog.component';
import { ListboxModule } from 'primeng/listbox';
import { TooltipModule } from 'primeng/tooltip';
import { SplitterModule } from 'primeng/splitter';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { SidebarModule } from 'primeng/sidebar';

@NgModule({
  declarations: [
    AppComponent,
    ProfilePageComponent,
    FilesPageComponent,
    LabelingPageComponent,
    ProjectPageComponent,
    FoldersPageComponent,
    ContactPageComponent,
    ManualPageComponent,
    DescriptionDialogComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    FormsModule,
    AppRoutingModule,
    NoopAnimationsModule,
    HttpClientModule,
    CardModule,
    TableModule,
    ButtonModule,
    DropdownModule,
    DialogModule,
    InputTextModule,
    ToastModule,
    CheckboxModule,
    ColorPickerModule,
    ConfirmPopupModule,
    SpeedDialModule,
    ToggleButtonModule,
    MenuModule,
    TooltipModule,
    ListboxModule,
    SplitterModule,
    FileUploadModule,
    InputTextareaModule,
    ProgressSpinnerModule,
    SidebarModule,
    ToolbarModule,
    AvatarModule,
    AvatarGroupModule,
  ],
  providers: [
    MessageService,
    ConfirmationService,
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }

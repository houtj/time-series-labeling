import { HttpClient } from '@angular/common/http';
import { Component, OnInit, Inject, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { environment } from '../environments/environment';
import { DatabaseService } from './database/database.service';
import { UserProfile } from './model';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmationService, MenuItem } from 'primeng/api';
import { Observable, Subject, filter, switchMap, takeUntil, tap } from 'rxjs';
import { setThrowInvalidWriteToSignalError } from '@angular/core/primitives/signals';
import { Location } from '@angular/common'


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  private http = inject(HttpClient)
  public databaseService = inject(DatabaseService)
  private router = inject(Router)
  private confirmationService = inject(ConfirmationService)
  private changeDetectorRef =inject(ChangeDetectorRef)
  private location = inject(Location)

  isIframe = false;
  loginDisplay = false;
  private readonly _destroying$ = new Subject<void>();

  pageTitle?: string;
  pageLabel?: string;
  version = 'v1.0.13'
  menuItems: MenuItem[]|undefined = [
    {
      label: 'Profile',
      icon: 'pi pi-fw pi-user',
      routerLink: ['/profile']
    },
    {
      label: 'Folders',
      icon: 'pi pi-fw pi-folder',
      routerLink: ['/folders']
    },
    {
      label: 'Project Setting',
      icon:'pi pi-fw pi-cog',
      routerLink: ['/projects'] 
    },
    {
      label: 'Contact us',
      icon: 'pi pi-fw pi-envelope',
      routerLink: ['/contact']
    },
    {
      label: 'Manual',
      icon: 'pi pi-fw pi-book',
      routerLink: ['/manual']
    }
  ];



  constructor(
  ) {
    this.databaseService.pageLabel$.pipe(
      filter(label=> label!==undefined),
      tap(label=>this.pageLabel = label),
      switchMap(label=>this.databaseService.pageTitle$),
      filter(title=>title!==undefined)
    ).subscribe(title=>{
      this.pageTitle = title
      this.changeDetectorRef.detectChanges()
    })
  }

  ngOnInit(): void {

    this.isIframe = window !== window.parent && !window.opener; // Remove this line to use Angular Universal
    this.databaseService.updateSelectedUser()
  }


  onClickParent($event: MouseEvent) {
    const urlTree = this.router.parseUrl(this.router.url);
    const urlWithoutParams = urlTree.root.children['primary'].segments.map(it => it.path).join('/');
    this.location.back()
    // switch (urlWithoutParams) {
    //   case 'files':
    //     this.router.navigate(['/folders'])
    //     break
    //   case 'labeling':
    //     const folderId = this.router.url.split(';')[1].split('=')[1]
    //     this.router.navigate(['/files', {folderId: folderId}])
    //     break
    //   default:
    //     this.location.back()
    // }
  }

  ngOnDestroy(): void {
  }
}

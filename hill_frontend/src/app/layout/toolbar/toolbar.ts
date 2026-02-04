import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ToolbarModule } from 'primeng/toolbar';
import { ButtonModule } from 'primeng/button';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { UserStateService } from '../../core/services';

/**
 * Toolbar Component
 * Application toolbar with navigation menu
 */
@Component({
  selector: 'app-toolbar',
  imports: [ToolbarModule, ButtonModule, MenuModule],
  standalone: true,
  templateUrl: './toolbar.html',
  styleUrl: './toolbar.scss'
})
export class ToolbarComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly userState = inject(UserStateService);

  readonly version = 'v2.0.8';
  readonly menuItems = signal<MenuItem[]>([]);

  ngOnInit() {
    this.menuItems.set([
      {
        label: 'Folders',
        icon: 'pi pi-fw pi-folder',
        command: () => this.router.navigate(['/folders'])
      },
      {
        label: 'Projects',
        icon: 'pi pi-fw pi-cog',
        command: () => this.router.navigate(['/projects'])
      },
      {
        label: 'Profile',
        icon: 'pi pi-fw pi-user',
        command: () => this.router.navigate(['/profile'])
      },
      {
        label: 'Contact',
        icon: 'pi pi-fw pi-envelope',
        command: () => this.router.navigate(['/contact'])
      },
      {
        label: 'Manual',
        icon: 'pi pi-fw pi-book',
        command: () => this.router.navigate(['/manual'])
      }
    ]);
  }

  get pageTitle() {
    return this.userState.pageTitle() || 'Hill Sequence';
  }

  get userName() {
    return this.userState.userInfo()?.name || 'Loading...';
  }
}

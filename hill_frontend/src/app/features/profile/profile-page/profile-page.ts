import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';

// Core imports
import { UserStateService } from '../../../core/services';
import { UserModel, FolderModel, ProjectModel } from '../../../core/models';

// Plotly
import * as Plotly from 'plotly.js-dist-min';

/**
 * Profile Page Component
 * Displays user profile information, statistics, recent activity, and contributions
 */
@Component({
  selector: 'app-profile-page',
  imports: [
    CommonModule,
    CardModule,
    TableModule,
    TooltipModule
  ],
  standalone: true,
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss'
})
export class ProfilePageComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chart') plotlyChart?: ElementRef;

  private readonly userState = inject(UserStateService);
  private readonly router = inject(Router);
  private subscriptions = new Subscription();

  // Computed signals from state
  protected readonly userInfo = this.userState.userInfo;
  protected readonly folderList = this.userState.folderList;
  protected readonly projectList = this.userState.projectList;

  // Component state
  protected badgeImageSrc = computed(() => {
    const badge = this.userInfo()?.badge || 'Iron';
    return `assets/img/${badge}.png`;
  });

  ngOnInit(): void {
    this.userState.updatePageTitle('Profile');
    
    // Load user data if not already loaded
    if (!this.userInfo()) {
      // In a real app, you would fetch user data here
      // For now, we rely on the toolbar's initialization
    }
  }

  ngAfterViewInit(): void {
    // Render contribution chart after view is initialized
    this.renderContributionChart();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  /**
   * Render contribution history chart using Plotly
   */
  private renderContributionChart(): void {
    if (!this.plotlyChart?.nativeElement) return;

    const history = this.userInfo()?.contributionHistory || [];
    
    const trace: Plotly.Data[] = [
      {
        x: history.map((h: any) => h.time),
        y: history.map((h: any) => h.nbEventsLabeled),
        type: 'bar',
        text: history.map((h: any) => h.nbEventsLabeled).map(String),
        hoverinfo: 'none',
        marker: {
          color: '#3b82f6' // Primary blue color
        }
      }
    ];

    const layout: Partial<Plotly.Layout> = {
      showlegend: false,
      hovermode: false,
      dragmode: false,
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      autosize: true,
      margin: {
        t: 20,
        r: 5,
        b: 20,
        l: 40
      },
      xaxis: {
        showgrid: false,
        color: 'var(--text-color)',
        tickfont: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
          size: 14,
          color: 'var(--text-color-secondary)'
        }
      },
      yaxis: {
        showgrid: true,
        gridcolor: 'rgba(255, 255, 255, 0.1)',
        color: 'var(--text-color)',
        tickfont: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
          size: 14,
          color: 'var(--text-color-secondary)'
        }
      }
    };

    const config: Partial<Plotly.Config> = {
      responsive: true,
      scrollZoom: false,
      displaylogo: false,
      displayModeBar: false
    };

    Plotly.newPlot(this.plotlyChart.nativeElement, trace, layout, config);
  }

  /**
   * Navigate to recent file for labeling
   */
  onClickRecentFile(event: MouseEvent, file: UserModel['recent'][0]): void {
    this.router.navigate(['/labeling', file.file], {
      queryParams: { folderId: file.folder }
    });
  }

  /**
   * Navigate to message location (file or folder)
   */
  onClickMessage(event: MouseEvent, message: UserModel['message'][0]): void {
    if (message.file) {
      this.router.navigate(['/labeling', message.file], {
        queryParams: { folderId: message.folder }
      });
    } else {
      this.router.navigate(['/files', message.folder]);
    }
  }

  /**
   * Format date for display
   */
  formatDate(date?: { $date: string }): string {
    if (!date?.$date) return 'N/A';
    return new Date(date.$date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
}

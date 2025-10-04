import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

// PrimeNG imports
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { ConfirmationService } from 'primeng/api';

// Core imports
import { LabelModel } from '../../../../core/models';

// Feature services
import { LabelStateService } from '../../services';

// Feature models
import { ToolbarAction } from '../../models/toolbar-action.model';

/**
 * Guidelines Panel Component
 * Displays and manages guidelines in a table
 */
@Component({
  selector: 'app-guidelines-panel',
  imports: [
    CommonModule,
    TableModule,
    ButtonModule,
    TooltipModule,
    ConfirmPopupModule
  ],
  standalone: true,
  providers: [ConfirmationService],
  templateUrl: './guidelines-panel.html',
  styleUrl: './guidelines-panel.scss'
})
export class GuidelinesPanelComponent {
  @Input() labelInfo?: LabelModel;
  
  @Output() onRefresh = new EventEmitter<void>();
  
  private readonly labelState = inject(LabelStateService);
  private readonly confirmationService = inject(ConfirmationService);
  
  // Get guidelines from label info
  get guidelines(): LabelModel['guidelines'] {
    return this.labelInfo?.guidelines || [];
  }
  
  /**
   * Get toolbar actions for this panel
   * Called by parent to render buttons in tab header
   */
  getToolbarActions(): ToolbarAction[] {
    return [
      {
        icon: 'pi pi-refresh',
        label: 'Refresh',
        action: () => this.onClickRefresh()
      },
      {
        icon: 'pi pi-eye',
        label: 'Show All',
        action: () => this.onClickUnhideAll()
      },
      {
        icon: 'pi pi-eye-slash',
        label: 'Hide All',
        action: () => this.onClickHideAll()
      },
      {
        icon: 'pi pi-trash',
        label: 'Remove All',
        severity: 'danger',
        action: (event?: Event) => this.onClickRemoveAll(event!)
      }
    ];
  }
  
  /**
   * Handle refresh button click
   */
  onClickRefresh(): void {
    this.onRefresh.emit();
  }
  
  /**
   * Handle show all guidelines
   */
  onClickUnhideAll(): void {
    if (!this.labelInfo) return;
    
    this.labelInfo.guidelines.forEach(g => g.hide = false);
    this.labelState.updateLabel(this.labelInfo);
  }
  
  /**
   * Handle hide all guidelines
   */
  onClickHideAll(): void {
    if (!this.labelInfo) return;
    
    this.labelInfo.guidelines.forEach(g => g.hide = true);
    this.labelState.updateLabel(this.labelInfo);
  }
  
  /**
   * Handle remove all guidelines
   */
  onClickRemoveAll(event: Event): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Remove all guidelines?',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        if (!this.labelInfo) return;
        this.labelInfo.guidelines = [];
        this.labelState.updateLabel(this.labelInfo);
      }
    });
  }
  
  /**
   * Handle toggle guideline visibility
   */
  onClickToggleHide(guideline: LabelModel['guidelines'][0]): void {
    if (!this.labelInfo) return;
    
    const index = this.labelInfo.guidelines.findIndex(g => g === guideline);
    if (index !== -1) {
      this.labelInfo.guidelines[index].hide = !this.labelInfo.guidelines[index].hide;
      this.labelState.updateLabel(this.labelInfo);
    }
  }
  
  /**
   * Handle remove guideline
   */
  onClickRemove(guidelineToRemove: LabelModel['guidelines'][0]): void {
    if (!this.labelInfo) return;
    
    this.labelInfo.guidelines = this.labelInfo.guidelines.filter(g => g !== guidelineToRemove);
    this.labelState.updateLabel(this.labelInfo);
  }
}

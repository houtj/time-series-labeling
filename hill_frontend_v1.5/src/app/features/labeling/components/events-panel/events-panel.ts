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
import { LabelStateService, ChartService, LabelingActionsService } from '../../services';

// Feature models
import { ToolbarAction } from '../../models/toolbar-action.model';

/**
 * Events Panel Component
 * Displays and manages labeled events in a table
 */
@Component({
  selector: 'app-events-panel',
  imports: [
    CommonModule,
    TableModule,
    ButtonModule,
    TooltipModule,
    ConfirmPopupModule
  ],
  standalone: true,
  providers: [ConfirmationService],
  templateUrl: './events-panel.html',
  styleUrl: './events-panel.scss'
})
export class EventsPanelComponent {
  @Input() labelInfo?: LabelModel;
  
  @Output() onRefresh = new EventEmitter<void>();
  @Output() onEditDescription = new EventEmitter<{ event: LabelModel['events'][0]; index: number }>();
  
  private readonly labelState = inject(LabelStateService);
  private readonly chartService = inject(ChartService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly labelingActions = inject(LabelingActionsService);
  
  // Get events from label info
  get events(): LabelModel['events'] {
    return this.labelInfo?.events || [];
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
   * Handle show all events
   */
  onClickUnhideAll(): void {
    if (!this.labelInfo) return;
    
    this.labelInfo.events.forEach(e => e.hide = false);
    this.labelState.updateLabel(this.labelInfo);
    
    // Auto-save to database
    this.labelingActions.queueAutoSave(this.labelInfo);
  }
  
  /**
   * Handle hide all events
   */
  onClickHideAll(): void {
    if (!this.labelInfo) return;
    
    this.labelInfo.events.forEach(e => e.hide = true);
    this.labelState.updateLabel(this.labelInfo);
    
    // Auto-save to database
    this.labelingActions.queueAutoSave(this.labelInfo);
  }
  
  /**
   * Handle remove all events
   */
  onClickRemoveAll(event: Event): void {
    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Remove all events?',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        if (!this.labelInfo) return;
        this.labelInfo.events = [];
        this.labelState.updateLabel(this.labelInfo);
        
        // Auto-save to database
        this.labelingActions.queueAutoSave(this.labelInfo);
      }
    });
  }
  
  /**
   * Handle select event (zoom to event on chart)
   */
  onClickSelectEvent(event: LabelModel['events'][0]): void {
    this.chartService.zoomToEvent(event);
  }
  
  /**
   * Handle toggle event visibility
   */
  onClickToggleHide(event: LabelModel['events'][0]): void {
    if (!this.labelInfo) return;
    
    const index = this.labelInfo.events.findIndex(e => e === event);
    if (index !== -1) {
      this.labelInfo.events[index].hide = !this.labelInfo.events[index].hide;
      this.labelState.updateLabel(this.labelInfo);
      
      // Auto-save to database
      this.labelingActions.queueAutoSave(this.labelInfo);
    }
  }
  
  /**
   * Handle remove event
   */
  onClickRemove(eventToRemove: LabelModel['events'][0]): void {
    if (!this.labelInfo) return;
    
    this.labelInfo.events = this.labelInfo.events.filter(e => e !== eventToRemove);
    this.labelState.updateLabel(this.labelInfo);
    
    // Auto-save to database
    this.labelingActions.queueAutoSave(this.labelInfo);
  }
  
  /**
   * Handle edit description
   */
  onClickEditDescription(event: LabelModel['events'][0], index: number): void {
    this.onEditDescription.emit({ event, index });
  }
}

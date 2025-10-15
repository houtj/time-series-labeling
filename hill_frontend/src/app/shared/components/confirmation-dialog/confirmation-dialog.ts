import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

// PrimeNG imports
import { Dialog } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';

/**
 * Generic Confirmation Dialog Component
 * Can be used for any confirmation scenario: delete, discard, logout, etc.
 */
@Component({
  selector: 'app-confirmation-dialog',
  imports: [
    CommonModule,
    Dialog,
    ButtonModule
  ],
  standalone: true,
  templateUrl: './confirmation-dialog.html',
  styleUrl: './confirmation-dialog.scss'
})
export class ConfirmationDialogComponent {
  @Input() visible = false;
  @Input() title = 'Confirmation';
  @Input() message = 'Are you sure you want to proceed?';
  @Input() icon = 'pi pi-exclamation-triangle';
  @Input() severity: 'info' | 'warning' | 'danger' | 'success' = 'warning';
  @Input() confirmLabel = 'Confirm';
  @Input() cancelLabel = 'Cancel';
  @Input() confirmIcon = 'pi pi-check';
  @Input() cancelIcon = 'pi pi-times';
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() onConfirm = new EventEmitter<void>();
  @Output() onCancel = new EventEmitter<void>();

  /**
   * Handle confirm action
   */
  onClickConfirm(): void {
    this.onConfirm.emit();
    this.closeDialog();
  }

  /**
   * Handle cancel action
   */
  onClickCancel(): void {
    this.onCancel.emit();
    this.closeDialog();
  }

  /**
   * Close dialog
   */
  private closeDialog(): void {
    this.visible = false;
    this.visibleChange.emit(false);
  }

  /**
   * Get severity class
   */
  getSeverityClass(): string {
    return `severity-${this.severity}`;
  }

  /**
   * Get confirm button severity
   */
  getConfirmButtonSeverity(): 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'help' | 'primary' | 'contrast' | null | undefined {
    switch (this.severity) {
      case 'danger':
        return 'danger';
      case 'warning':
        return 'warn';
      case 'success':
        return 'success';
      case 'info':
      default:
        return 'primary';
    }
  }
}

import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports
import { Dialog } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { Textarea } from 'primeng/textarea';

/**
 * Generic Description Dialog Component
 * Can be used to edit descriptions for files, projects, folders, etc.
 */
@Component({
  selector: 'app-description-dialog',
  imports: [
    CommonModule,
    FormsModule,
    Dialog,
    ButtonModule,
    Textarea
  ],
  standalone: true,
  templateUrl: './description-dialog.html',
  styleUrl: './description-dialog.scss'
})
export class DescriptionDialogComponent {
  @Input() visible = false;
  @Input() title = 'Edit Description';
  @Input() resourceName = '';
  @Input() description = '';
  @Input() placeholder = 'Enter description...';
  @Input() maxLength = 500;
  @Input() rows = 5;
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() descriptionChange = new EventEmitter<string>();
  @Output() onSave = new EventEmitter<string>();

  /**
   * Handle save action
   */
  onClickSave(): void {
    this.onSave.emit(this.description);
    this.closeDialog();
  }

  /**
   * Handle cancel action
   */
  onClickCancel(): void {
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
   * Get dialog title
   */
  getDialogTitle(): string {
    if (this.resourceName) {
      return `${this.title}: ${this.resourceName}`;
    }
    return this.title;
  }

  /**
   * Get remaining characters
   */
  getRemainingCharacters(): number {
    return this.maxLength - this.description.length;
  }

  /**
   * Check if description is too long
   */
  isTooLong(): boolean {
    return this.description.length > this.maxLength;
  }
}

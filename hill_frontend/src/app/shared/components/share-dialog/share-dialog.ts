import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG imports
import { Dialog } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { Select } from 'primeng/select';
import { InputText } from 'primeng/inputtext';
import { MessageService } from 'primeng/api';

// Core imports
import { UsersRepository } from '../../../core/repositories';
import { UserModel } from '../../../core/models';

/**
 * Generic Share Dialog Component
 * Can be used to share folders, projects, or any other resource
 */
@Component({
  selector: 'app-share-dialog',
  imports: [
    CommonModule,
    FormsModule,
    Dialog,
    ButtonModule,
    Select,
    InputText
  ],
  standalone: true,
  templateUrl: './share-dialog.html',
  styleUrl: './share-dialog.scss'
})
export class ShareDialogComponent implements OnChanges {
  @Input() visible = false;
  @Input() title = 'Share';
  @Input() resourceType: 'folder' | 'project' | 'file' = 'folder';
  @Input() resourceName = '';
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() onShare = new EventEmitter<{ user: UserModel; message: string }>();

  // Inject services
  private readonly usersRepo = inject(UsersRepository);
  private readonly messageService = inject(MessageService);

  // Component state
  usersList: UserModel[] = [];
  selectedUser?: UserModel;
  message = '';
  loading = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible && this.usersList.length === 0) {
      this.loadUsers();
    }
  }

  /**
   * Load users from backend
   */
  private loadUsers(): void {
    this.loading = true;
    this.usersRepo.getAllUsers().subscribe({
      next: (users) => {
        this.usersList = users;
        if (users.length > 0) {
          this.selectedUser = users[0];
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load users:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load users'
        });
        this.loading = false;
      }
    });
  }

  /**
   * Handle share action
   */
  onClickShare(): void {
    if (!this.selectedUser) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Validation Error',
        detail: 'Please select a user'
      });
      return;
    }

    this.onShare.emit({
      user: this.selectedUser,
      message: this.message
    });

    // Reset form
    this.message = '';
  }

  /**
   * Handle cancel action
   */
  onClickCancel(): void {
    this.message = '';
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
   * Get resource type label
   */
  getResourceTypeLabel(): string {
    switch (this.resourceType) {
      case 'folder':
        return 'folder';
      case 'project':
        return 'project';
      case 'file':
        return 'file';
      default:
        return 'resource';
    }
  }
}

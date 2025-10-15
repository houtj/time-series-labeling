import { CanDeactivateFn } from '@angular/router';
import { inject } from '@angular/core';
import { Observable } from 'rxjs';

/**
 * Interface for components that can have unsaved changes
 * Components must implement this to work with the guard
 */
export interface CanComponentDeactivate {
  canDeactivate: () => boolean | Observable<boolean> | Promise<boolean>;
}

/**
 * Unsaved Changes Guard (Functional - Angular 20)
 * 
 * Prevents navigation away from a component if there are unsaved changes
 * Shows browser confirmation dialog to user
 * 
 * Usage in routes:
 * {
 *   path: 'labeling/:fileId',
 *   component: LabelingPageComponent,
 *   canDeactivate: [unsavedChangesGuard]
 * }
 * 
 * Component must implement CanComponentDeactivate:
 * export class LabelingPageComponent implements CanComponentDeactivate {
 *   hasUnsavedChanges = signal<boolean>(false);
 *   
 *   canDeactivate(): boolean {
 *     if (this.hasUnsavedChanges()) {
 *       return confirm('You have unsaved changes. Do you want to leave?');
 *     }
 *     return true;
 *   }
 * }
 */
export const unsavedChangesGuard: CanDeactivateFn<CanComponentDeactivate> = (
  component,
  currentRoute,
  currentState,
  nextState
) => {
  // If component doesn't implement canDeactivate, allow navigation
  if (!component.canDeactivate) {
    return true;
  }

  // Call component's canDeactivate method
  const result = component.canDeactivate();

  // Handle different return types
  if (typeof result === 'boolean') {
    if (!result) {
      console.log('Navigation prevented: Unsaved changes detected');
    }
    return result;
  }

  // For Observable or Promise, let Angular handle it
  return result;
};

/**
 * Alternative: Custom confirmation dialog guard
 * Uses a service instead of browser confirm()
 */
export const unsavedChangesGuardWithDialog: CanDeactivateFn<CanComponentDeactivate> = async (
  component,
  currentRoute,
  currentState,
  nextState
) => {
  // If component doesn't implement canDeactivate, allow navigation
  if (!component.canDeactivate) {
    return true;
  }

  const result = component.canDeactivate();

  // Handle synchronous boolean
  if (typeof result === 'boolean') {
    if (!result) {
      // Could inject a dialog service here to show custom dialog
      // For now, use browser confirm
      return confirm('You have unsaved changes. Do you want to leave?');
    }
    return true;
  }

  // Handle Observable or Promise
  const canDeactivate = await Promise.resolve(result);
  if (!canDeactivate) {
    return confirm('You have unsaved changes. Do you want to leave?');
  }

  return true;
};


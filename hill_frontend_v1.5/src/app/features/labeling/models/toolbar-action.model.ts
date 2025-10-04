/**
 * Toolbar Action Model
 * Defines the structure for toolbar buttons in tab headers
 */
export interface ToolbarAction {
  icon: string;
  label: string;
  severity?: 'secondary' | 'success' | 'info' | 'warn' | 'danger' | 'contrast';
  action: (event?: Event) => void;
  disabled?: boolean;
}


import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ToolbarComponent } from '../toolbar/toolbar';

/**
 * Main Layout Component
 * Container for the entire application layout
 */
@Component({
  selector: 'app-main-layout',
  imports: [RouterOutlet, ToolbarComponent],
  standalone: true,
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss'
})
export class MainLayoutComponent {
}

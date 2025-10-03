import { Component } from '@angular/core';
import { MainLayoutComponent } from './layout/main-layout/main-layout';

@Component({
  selector: 'app-root',
  imports: [MainLayoutComponent],
  standalone: true,
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
}

import { Component, OnInit, inject } from '@angular/core';
import { CardModule } from 'primeng/card';
import { UserStateService } from '../../../core/services';

@Component({
  selector: 'app-manual-page',
  imports: [CardModule],
  standalone: true,
  templateUrl: './manual-page.html',
  styleUrl: './manual-page.scss'
})
export class ManualPageComponent implements OnInit {
  private readonly userState = inject(UserStateService);

  ngOnInit() {
    this.userState.updatePageTitle('Manual');
  }
}

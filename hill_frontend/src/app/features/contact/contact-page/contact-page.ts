import { Component, OnInit, inject } from '@angular/core';
import { CardModule } from 'primeng/card';
import { UserStateService } from '../../../core/services';

@Component({
  selector: 'app-contact-page',
  imports: [CardModule],
  standalone: true,
  templateUrl: './contact-page.html',
  styleUrl: './contact-page.scss'
})
export class ContactPageComponent implements OnInit {
  private readonly userState = inject(UserStateService);

  ngOnInit() {
    this.userState.updatePageTitle('Contact');
  }
}

import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManualPageComponent } from './manual-page.component';

describe('ManualPageComponent', () => {
  let component: ManualPageComponent;
  let fixture: ComponentFixture<ManualPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ManualPageComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ManualPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

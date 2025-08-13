import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LabelingPageComponent } from './labeling-page.component';

describe('LabelingPageComponent', () => {
  let component: LabelingPageComponent;
  let fixture: ComponentFixture<LabelingPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [LabelingPageComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(LabelingPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

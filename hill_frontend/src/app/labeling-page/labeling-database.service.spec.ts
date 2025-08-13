import { TestBed } from '@angular/core/testing';

import { LabelingDatabaseService } from './labeling-database.service';

describe('LabelingDatabaseService', () => {
  let service: LabelingDatabaseService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(LabelingDatabaseService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

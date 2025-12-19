import { Injectable, inject } from '@angular/core';
import { Observable, map, catchError, of } from 'rxjs';
import { ApiService } from '../../../core/services/http/api.service';

/**
 * Feature values for a single channel
 */
export interface ChannelFrequencyFeatures {
  bp_delta: number;
  bp_theta: number;
  bp_alpha: number;
  bp_beta: number;
  slow_ratio: number;
  fast_ratio: number;
}

export interface ChannelEnergyFeatures {
  rms: number;
  mean_envelope: number;
  std_envelope: number;
  max_envelope: number;
}

export interface ChannelMorphologyFeatures {
  peak_to_peak: number;
  zero_crossing_rate: number;
  max_slope: number;
  symmetry_estimate: number;
}

/**
 * Features grouped by channel name
 */
export interface WindowFeatures {
  frequency: Record<string, ChannelFrequencyFeatures>;
  energy: Record<string, ChannelEnergyFeatures>;
  morphology: Record<string, ChannelMorphologyFeatures>;
  window: {
    start: number;
    end: number;
    length: number;
  };
}

/**
 * Window Features Service
 * Fetches computed features for time-series windows
 */
@Injectable({
  providedIn: 'root'
})
export class WindowFeaturesService {
  private readonly apiService = inject(ApiService);

  /**
   * Get computed features for a time-series window
   * 
   * @param fileId - The file ID
   * @param start - Window start index
   * @param end - Window end index
   * @returns Observable of window features
   */
  getWindowFeatures(fileId: string, start: number, end: number): Observable<WindowFeatures | null> {
    return this.apiService.post<WindowFeatures>('/window-indicator/features', {
      file_id: fileId,
      start,
      end
    }).pipe(
      catchError(error => {
        console.error('Error fetching window features:', error);
        return of(null);
      })
    );
  }
}


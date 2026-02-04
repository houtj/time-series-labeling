import { Injectable, inject, signal } from '@angular/core';
import { Observable, Subject, from, throwError } from 'rxjs';
import { catchError, takeUntil, tap } from 'rxjs/operators';
import { BinaryParserService, ViewportResponse } from './binary-parser.service';
import { environment } from '../../../../environments/environment';

/**
 * Fetch Controller Service
 * Manages viewport data fetching with debouncing and request cancellation
 */
@Injectable({
  providedIn: 'root'
})
export class FetchControllerService {
  
  private readonly binaryParser = inject(BinaryParserService);
  private readonly apiUrl = environment.apiUrl;
  
  private currentController: AbortController | null = null;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly DEBOUNCE_MS = 50;
  
  /** Whether a fetch is currently in progress */
  readonly isLoading = signal(false);
  
  /** Cancel subject for RxJS streams */
  private cancelSubject = new Subject<void>();
  
  /**
   * Fetch viewport data from the backend
   * 
   * @param fileId The file ID
   * @param xMin Start of range
   * @param xMax End of range
   * @param maxPoints Target points per channel (default: 20000)
   */
  fetchViewport(
    fileId: string,
    xMin: number,
    xMax: number,
    maxPoints: number = 20000
  ): Observable<ViewportResponse> {
    // Cancel any in-flight request
    this.cancelPendingRequest();
    
    this.currentController = new AbortController();
    const signal = this.currentController.signal;
    
    const url = `${this.apiUrl}/files/${fileId}/viewport?x_min=${xMin}&x_max=${xMax}&max_points=${maxPoints}`;
    
    this.isLoading.set(true);
    
    return from(
      fetch(url, { signal })
        .then(async response => {
          if (!response.ok) {
            // Try to get error message from response
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${text}`);
          }
          
          // Check content type - if it's not binary, the backend returned an error
          const contentType = response.headers.get('Content-Type') || '';
          if (!contentType.includes('octet-stream')) {
            const text = await response.text();
            console.error('[FetchController] Expected binary data but got:', contentType, text.substring(0, 200));
            throw new Error(`Expected binary data but got ${contentType}: ${text.substring(0, 100)}`);
          }
          
          const buffer = await response.arrayBuffer();
          
          // Debug logging
          console.debug(`[FetchController] Received ${buffer.byteLength} bytes, headers:`, {
            totalPoints: response.headers.get('X-Total-Points'),
            returnedPoints: response.headers.get('X-Returned-Points'),
            numColumns: response.headers.get('X-Num-Columns'),
            channelNames: response.headers.get('X-Channel-Names')
          });
          
          return { buffer, headers: response.headers };
        })
        .then(({ buffer, headers }) => {
          return this.binaryParser.parseViewportResponse(buffer, headers);
        })
    ).pipe(
      tap(() => this.isLoading.set(false)),
      catchError(error => {
        this.isLoading.set(false);
        if (error.name === 'AbortError') {
          // Return empty observable for intentional cancellation
          return throwError(() => new Error('Request cancelled'));
        }
        return throwError(() => error);
      }),
      takeUntil(this.cancelSubject)
    );
  }
  
  /**
   * Fetch with debouncing - prevents rapid consecutive requests
   */
  debouncedFetch(
    fileId: string,
    xMin: number,
    xMax: number,
    maxPoints?: number
  ): Observable<ViewportResponse> {
    return new Observable(observer => {
      // Clear any existing debounce timer
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
      }
      
      this.debounceTimer = setTimeout(() => {
        this.fetchViewport(fileId, xMin, xMax, maxPoints)
          .subscribe({
            next: value => observer.next(value),
            error: err => observer.error(err),
            complete: () => observer.complete()
          });
      }, this.DEBOUNCE_MS);
      
      // Cleanup on unsubscribe
      return () => {
        if (this.debounceTimer) {
          clearTimeout(this.debounceTimer);
          this.debounceTimer = null;
        }
      };
    });
  }
  
  /**
   * Cancel any pending request
   */
  cancelPendingRequest(): void {
    if (this.currentController) {
      this.currentController.abort();
      this.currentController = null;
    }
    
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    
    // Emit cancel signal for RxJS subscriptions
    this.cancelSubject.next();
    
    this.isLoading.set(false);
  }
  
  /**
   * Cleanup on service destruction
   */
  ngOnDestroy(): void {
    this.cancelPendingRequest();
    this.cancelSubject.complete();
  }
}

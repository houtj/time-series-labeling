import { Injectable, inject, signal } from '@angular/core';
import { Observable, Subject, EMPTY, from } from 'rxjs';
import { catchError, debounceTime, switchMap, tap, finalize } from 'rxjs/operators';
import { BinaryParserService, ViewportResponse } from './binary-parser.service';
import { environment } from '../../../../environments/environment';

export interface ViewportRequest {
  fileId: string;
  xMin: number;
  xMax: number;
  maxPoints: number;
}

export interface ViewportResult {
  response: ViewportResponse;
  xMin: number;
  xMax: number;
}

/**
 * Fetch Controller Service
 * Manages viewport data fetching with debouncing and request cancellation
 * Uses switchMap to automatically cancel stale requests
 */
@Injectable({
  providedIn: 'root'
})
export class FetchControllerService {

  private readonly binaryParser = inject(BinaryParserService);
  private readonly apiUrl = environment.apiUrl;

  private currentController: AbortController | null = null;
  private readonly DEBOUNCE_MS = 150;

  /** Whether a fetch is currently in progress */
  readonly isLoading = signal(false);

  /** Subject for viewport requests */
  private viewportRequest$ = new Subject<ViewportRequest>();

  /** Observable of viewport results - subscribe once, emits latest data */
  readonly viewportData$: Observable<ViewportResult> = this.viewportRequest$.pipe(
    debounceTime(this.DEBOUNCE_MS),
    tap(() => this.isLoading.set(true)),
    switchMap(req => this.fetchViewport(req).pipe(
      catchError(error => {
        if (error.name !== 'AbortError') {
          console.error('[FetchController] Fetch error:', error);
        }
        this.isLoading.set(false);
        return EMPTY;
      })
    )),
    tap(() => this.isLoading.set(false))
  );

  /**
   * Request viewport data (debounced, auto-cancels previous requests)
   */
  requestViewport(fileId: string, xMin: number, xMax: number, maxPoints: number = 5000): void {
    this.viewportRequest$.next({ fileId, xMin, xMax, maxPoints });
  }

  /**
   * Fetch viewport data from the backend
   */
  private fetchViewport(req: ViewportRequest): Observable<ViewportResult> {
    // Abort any in-flight HTTP request
    if (this.currentController) {
      this.currentController.abort();
    }

    this.currentController = new AbortController();
    const signal = this.currentController.signal;

    const url = `${this.apiUrl}/files/${req.fileId}/viewport?x_min=${req.xMin}&x_max=${req.xMax}&max_points=${req.maxPoints}`;

    return from(
      fetch(url, { signal })
        .then(async response => {
          if (!response.ok) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${text}`);
          }

          const contentType = response.headers.get('Content-Type') || '';
          if (!contentType.includes('octet-stream')) {
            const text = await response.text();
            console.error('[FetchController] Expected binary data but got:', contentType, text.substring(0, 200));
            throw new Error(`Expected binary data but got ${contentType}: ${text.substring(0, 100)}`);
          }

          const buffer = await response.arrayBuffer();

          console.debug(`[FetchController] Received ${buffer.byteLength} bytes, headers:`, {
            totalPoints: response.headers.get('X-Total-Points'),
            returnedPoints: response.headers.get('X-Returned-Points'),
            numColumns: response.headers.get('X-Num-Columns'),
            channelNames: response.headers.get('X-Channel-Names')
          });

          return { buffer, headers: response.headers };
        })
        .then(({ buffer, headers }) => {
          const parsed = this.binaryParser.parseViewportResponse(buffer, headers);
          return { response: parsed, xMin: req.xMin, xMax: req.xMax } as ViewportResult;
        })
    ).pipe(
      finalize(() => {
        this.currentController = null;
      })
    );
  }

  /**
   * Cancel any pending request
   */
  cancelPendingRequest(): void {
    if (this.currentController) {
      this.currentController.abort();
      this.currentController = null;
    }

    this.isLoading.set(false);
  }

  /**
   * Cleanup on service destruction
   */
  ngOnDestroy(): void {
    this.cancelPendingRequest();
    this.viewportRequest$.complete();
  }
}

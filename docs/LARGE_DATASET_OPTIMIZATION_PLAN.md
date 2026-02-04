# Large Dataset Optimization Implementation Plan

> **Status: IMPLEMENTED** - All phases completed.

## Overview

This document outlines the implementation plan for optimizing the display of large time series datasets. The goal is to solve two problems:
1. **Loading**: Reduce data transfer time from backend to frontend
2. **Rendering**: Prevent browser lag when displaying millions of data points

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Interaction          Cache Layer              Display Layer        │
│  ┌──────────────┐    ┌───────────────────┐    ┌──────────────────────┐  │
│  │ Zoom/Pan     │───►│ Cache Manager     │───►│ Resample Service     │  │
│  │ (debounced)  │    │ (20k pts/channel) │    │ (5k pts/channel)     │  │
│  └──────────────┘    └─────────┬─────────┘    └──────────┬───────────┘  │
│                                │                         │               │
│                                ▼                         ▼               │
│                      ┌─────────────────┐        ┌──────────────────┐    │
│                      │ Fetch Controller│        │ Plotly Chart     │    │
│                      │ (cancel/retry)  │        │ (max 40k pts)    │    │
│                      └────────┬────────┘        └──────────────────┘    │
│                               │                                          │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │ Binary ArrayBuffer
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌───────────────────┐    ┌──────────────────┐   │
│  │ Viewport API    │───►│ Resample Service  │◄───│ Data Reader      │   │
│  │                 │    │ (MinMaxLTTB)      │    │ (Memory-mapped)  │   │
│  └─────────────────┘    └───────────────────┘    └──────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### Data Transfer
- **Format**: Binary ArrayBuffer (Float64Array)
- **Protocol**: HTTP with custom headers for metadata

### Storage Strategy
| Dataset Size | Storage Format |
|--------------|----------------|
| < 100k points | JSON (current format) |
| ≥ 100k points | Binary file (memory-mappable) + metadata JSON |

### Resampling Configuration
| Layer | Points per Channel | Max Total Points | Algorithm |
|-------|-------------------|------------------|-----------|
| Display (frontend) | 5,000 | 40,000 (8 channels) | MinMaxLTTB + Union |
| Cache (frontend) | 20,000 | 160,000 (8 channels) | MinMaxLTTB + Union |
| Backend response | 20,000 | 160,000 (8 channels) | MinMaxLTTB + Union |

### Cache Dimensions
- **Width**: 3x viewing window (from `view_start - window_size` to `view_end + window_size`)
- **Depth**: 20k points per channel, union of selected indices

---

## Implementation Tasks

### Phase 1: Backend - Data Storage & Parsing

#### Task 1.1: Modify File Parser to Generate Binary Format

**File**: `hill_workers/workers/file_parser.py`

**Changes**:
1. After parsing CSV, check point count
2. If points ≥ 100k: save as binary + metadata JSON
3. If points < 100k: save as JSON (current behavior)

**Binary File Structure**:
```
{file_id}.bin:
  [x_values: Float64][ch1_values: Float64][ch2_values: Float64]...
  
  Each array is contiguous, length = total_points
  Total size = total_points × num_columns × 8 bytes
```

**Metadata File Structure** (`{file_id}_meta.json`):
```json
{
  "format": "binary",
  "shape": [1000000, 6],
  "dtype": "float64",
  "totalPoints": 1000000,
  "xColumn": {
    "name": "timestamp",
    "unit": "s",
    "type": "time",
    "min": 0.0,
    "max": 999999.0
  },
  "channels": [
    {"name": "temperature", "unit": "°C", "color": "#FF0000", "column": 1},
    {"name": "humidity", "unit": "%", "color": "#00FF00", "column": 2}
  ]
}
```

**Database Schema Update**:
```python
# Add to file document
{
  "useBinaryFormat": True,  # or False for small files
  "binaryPath": "path/to/file.bin",
  "metaPath": "path/to/file_meta.json",
  "totalPoints": 1000000
}
```

#### Task 1.2: Implement Memory-Mapped File Reader

**File**: `hill_backend/services/data_reader.py` (new file)

```python
class MemoryMappedDataReader:
    """Efficiently read slices from large binary files."""
    
    def __init__(self, binary_path: str, meta_path: str):
        self.meta = load_metadata(meta_path)
        self.mmap = np.memmap(binary_path, dtype='float64', mode='r', 
                               shape=tuple(self.meta['shape']))
    
    def get_slice(self, x_min: float, x_max: float) -> tuple[np.ndarray, int]:
        """Return data slice and original point count in range."""
        x_col = self.mmap[:, 0]
        start_idx = np.searchsorted(x_col, x_min)
        end_idx = np.searchsorted(x_col, x_max, side='right')
        
        original_count = end_idx - start_idx
        data = self.mmap[start_idx:end_idx, :]
        
        return data, original_count
```

#### Task 1.3: Implement MinMaxLTTB Resampling Service

**File**: `hill_backend/services/resampler.py` (new file)

**Dependencies**: Add `tsdownsample` to `pyproject.toml`

```python
from tsdownsample import MinMaxLTTBDownsampler

class ResamplerService:
    """Downsample multi-channel time series using MinMaxLTTB with union of indices."""
    
    def __init__(self, target_points_per_channel: int = 20000):
        self.target_points = target_points_per_channel
        self.downsampler = MinMaxLTTBDownsampler()
    
    def resample(self, x: np.ndarray, channels: list[np.ndarray]) -> tuple[np.ndarray, list[np.ndarray]]:
        """
        Resample multiple channels, keeping union of important indices.
        
        Returns:
            x_out: Resampled x values
            channels_out: List of resampled channel arrays
        """
        if len(x) <= self.target_points:
            # No resampling needed
            return x, channels
        
        # Collect indices from each channel
        all_indices = set()
        for ch in channels:
            indices = self.downsampler.downsample(x, ch, n_out=self.target_points)
            all_indices.update(indices)
        
        # Sort and apply to all channels
        selected_indices = np.array(sorted(all_indices))
        x_out = x[selected_indices]
        channels_out = [ch[selected_indices] for ch in channels]
        
        return x_out, channels_out
```

---

### Phase 2: Backend - API Endpoints

#### Task 2.1: Create Viewport API Endpoint

**File**: `hill_backend/routes/files.py`

**Endpoint**: `GET /files/{file_id}/viewport`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| x_min | float | Yes | - | Start of range (in x-axis units) |
| x_max | float | Yes | - | End of range (in x-axis units) |
| max_points | int | No | 20000 | Target points per channel |
| channels | string | No | all | Comma-separated channel names |

**Response**:
- Content-Type: `application/octet-stream`
- Headers:
  - `X-Total-Points`: Original points in requested range
  - `X-Returned-Points`: Points after resampling
  - `X-Full-Resolution`: "true" if no resampling was applied
  - `X-Num-Columns`: Number of columns (1 + num_channels)
  - `X-X-Min`: Actual range start
  - `X-X-Max`: Actual range end
- Body: Binary data
  ```
  [x_array: Float64][ch1_array: Float64][ch2_array: Float64]...
  ```

**Implementation**:
```python
@router.get("/files/{file_id}/viewport")
async def get_viewport(
    file_id: str,
    x_min: float = Query(...),
    x_max: float = Query(...),
    max_points: int = Query(default=20000),
    channels: Optional[str] = Query(default=None)
):
    file_doc = await get_file_document(file_id)
    
    if not file_doc.get('useBinaryFormat'):
        # Small file: return full data as before
        return await get_full_file_data(file_id)
    
    # Large file: use memory-mapped reader
    reader = get_data_reader(file_doc)
    data, original_count = reader.get_slice(x_min, x_max)
    
    # Separate x and channels
    x = data[:, 0]
    channel_data = [data[:, i] for i in range(1, data.shape[1])]
    
    # Resample if needed
    if original_count > max_points * len(channel_data):
        resampler = ResamplerService(max_points)
        x_out, channels_out = resampler.resample(x, channel_data)
        is_full_resolution = False
    else:
        x_out, channels_out = x, channel_data
        is_full_resolution = True
    
    # Pack into binary response
    result = np.column_stack([x_out] + channels_out)
    
    return Response(
        content=result.tobytes(),
        media_type="application/octet-stream",
        headers={
            "X-Total-Points": str(original_count),
            "X-Returned-Points": str(len(x_out)),
            "X-Full-Resolution": str(is_full_resolution).lower(),
            "X-Num-Columns": str(result.shape[1]),
            "X-X-Min": str(float(x_out[0])),
            "X-X-Max": str(float(x_out[-1])),
        }
    )
```

#### Task 2.2: Modify Existing File Endpoint

**File**: `hill_backend/routes/files.py`

Modify `GET /files/{file_id}` to:
1. For small files: return as-is (current behavior)
2. For large files: return metadata + initial resampled data (5k per channel)

**Response for large files**:
```json
{
  "fileInfo": { ... },
  "useBinaryFormat": true,
  "metadata": {
    "totalPoints": 1000000,
    "xColumn": { "name": "timestamp", "unit": "s", "min": 0, "max": 999999 },
    "channels": [...]
  },
  "initialData": "<base64 encoded binary or inline Float64Array>"
}
```

---

### Phase 3: Frontend - Data Layer

#### Task 3.1: Create Binary Data Parser Service

**File**: `hill_frontend/src/app/core/services/binary-parser.service.ts` (new file)

```typescript
export interface ViewportResponse {
  x: Float64Array;
  channels: Map<string, Float64Array>;
  metadata: {
    totalPoints: number;
    returnedPoints: number;
    isFullResolution: boolean;
    xMin: number;
    xMax: number;
  };
}

@Injectable({ providedIn: 'root' })
export class BinaryParserService {
  
  parseViewportResponse(buffer: ArrayBuffer, headers: Headers, channelNames: string[]): ViewportResponse {
    const numColumns = parseInt(headers.get('X-Num-Columns') || '0');
    const returnedPoints = parseInt(headers.get('X-Returned-Points') || '0');
    
    const data = new Float64Array(buffer);
    const pointsPerColumn = returnedPoints;
    
    // Extract x and channels
    const x = data.subarray(0, pointsPerColumn);
    const channels = new Map<string, Float64Array>();
    
    for (let i = 0; i < channelNames.length; i++) {
      const start = (i + 1) * pointsPerColumn;
      const end = start + pointsPerColumn;
      channels.set(channelNames[i], data.subarray(start, end));
    }
    
    return {
      x,
      channels,
      metadata: {
        totalPoints: parseInt(headers.get('X-Total-Points') || '0'),
        returnedPoints,
        isFullResolution: headers.get('X-Full-Resolution') === 'true',
        xMin: parseFloat(headers.get('X-X-Min') || '0'),
        xMax: parseFloat(headers.get('X-X-Max') || '0'),
      }
    };
  }
}
```

#### Task 3.2: Create Cache Manager Service

**File**: `hill_frontend/src/app/features/labeling/services/cache-manager.service.ts` (new file)

```typescript
export interface CacheState {
  fileId: string;
  xMin: number;
  xMax: number;
  cachedPoints: number;
  isFullResolution: boolean;
  x: Float64Array;
  channels: Map<string, Float64Array>;
}

@Injectable({ providedIn: 'root' })
export class CacheManagerService {
  private cache: CacheState | null = null;
  
  updateCache(fileId: string, data: ViewportResponse): void {
    this.cache = {
      fileId,
      xMin: data.metadata.xMin,
      xMax: data.metadata.xMax,
      cachedPoints: data.metadata.returnedPoints,
      isFullResolution: data.metadata.isFullResolution,
      x: data.x,
      channels: data.channels,
    };
  }
  
  getSlice(viewMin: number, viewMax: number): { x: Float64Array; channels: Map<string, Float64Array> } | null {
    if (!this.cache) return null;
    
    // Binary search for indices
    const startIdx = this.binarySearch(this.cache.x, viewMin);
    const endIdx = this.binarySearch(this.cache.x, viewMax, 'right');
    
    return {
      x: this.cache.x.subarray(startIdx, endIdx),
      channels: new Map(
        [...this.cache.channels].map(([name, arr]) => [name, arr.subarray(startIdx, endIdx)])
      ),
    };
  }
  
  shouldFetchNewData(viewMin: number, viewMax: number, displayedPoints: number): { shouldFetch: boolean; reason: string } {
    if (!this.cache) {
      return { shouldFetch: true, reason: 'no_cache' };
    }
    
    // WIDTH check: is view within cache bounds?
    const viewWidth = viewMax - viewMin;
    const leftOut = Math.max(0, this.cache.xMin - viewMin);
    const rightOut = Math.max(0, viewMax - this.cache.xMax);
    
    if ((leftOut + rightOut) / viewWidth > 0.3) {
      return { shouldFetch: true, reason: 'out_of_bounds' };
    }
    
    // DEPTH check: is resolution sufficient?
    if (!this.cache.isFullResolution) {
      const cacheWidth = this.cache.xMax - this.cache.xMin;
      const viewRatio = viewWidth / cacheWidth;
      const cachedPointsInView = this.cache.cachedPoints * viewRatio;
      
      // If displayed points equals cached points (couldn't downsample), need more
      if (displayedPoints >= cachedPointsInView * 0.95) {
        return { shouldFetch: true, reason: 'insufficient_resolution' };
      }
    }
    
    return { shouldFetch: false, reason: 'cache_sufficient' };
  }
  
  calculateFetchRange(viewMin: number, viewMax: number): { xMin: number; xMax: number } {
    const viewWidth = viewMax - viewMin;
    return {
      xMin: viewMin - viewWidth,  // 3x total: 1x left buffer
      xMax: viewMax + viewWidth,  // 1x right buffer
    };
  }
  
  clearCache(): void {
    this.cache = null;
  }
  
  private binarySearch(arr: Float64Array, value: number, side: 'left' | 'right' = 'left'): number {
    let lo = 0;
    let hi = arr.length;
    
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (arr[mid] < value || (side === 'right' && arr[mid] === value)) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }
    return lo;
  }
}
```

#### Task 3.3: Create Fetch Controller Service

**File**: `hill_frontend/src/app/features/labeling/services/fetch-controller.service.ts` (new file)

```typescript
@Injectable({ providedIn: 'root' })
export class FetchControllerService {
  private currentController: AbortController | null = null;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly DEBOUNCE_MS = 50;
  
  constructor(
    private http: HttpClient,
    private binaryParser: BinaryParserService
  ) {}
  
  fetchViewport(
    fileId: string,
    xMin: number,
    xMax: number,
    channelNames: string[],
    maxPoints: number = 20000
  ): Observable<ViewportResponse> {
    // Cancel any in-flight request
    this.cancelPendingRequest();
    
    this.currentController = new AbortController();
    const signal = this.currentController.signal;
    
    const url = `/api/files/${fileId}/viewport?x_min=${xMin}&x_max=${xMax}&max_points=${maxPoints}`;
    
    return new Observable(observer => {
      fetch(url, { signal })
        .then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.arrayBuffer().then(buffer => ({ buffer, headers: response.headers }));
        })
        .then(({ buffer, headers }) => {
          const parsed = this.binaryParser.parseViewportResponse(buffer, headers, channelNames);
          observer.next(parsed);
          observer.complete();
        })
        .catch(error => {
          if (error.name === 'AbortError') {
            observer.complete();  // Intentional cancellation
          } else {
            observer.error(error);
          }
        });
      
      return () => this.cancelPendingRequest();
    });
  }
  
  debouncedFetch(
    fileId: string,
    xMin: number,
    xMax: number,
    channelNames: string[],
    maxPoints?: number
  ): Observable<ViewportResponse> {
    return new Observable(observer => {
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
      }
      
      this.debounceTimer = setTimeout(() => {
        this.fetchViewport(fileId, xMin, xMax, channelNames, maxPoints)
          .subscribe(observer);
      }, this.DEBOUNCE_MS);
      
      return () => {
        if (this.debounceTimer) {
          clearTimeout(this.debounceTimer);
        }
      };
    });
  }
  
  cancelPendingRequest(): void {
    if (this.currentController) {
      this.currentController.abort();
      this.currentController = null;
    }
  }
}
```

#### Task 3.4: Create Resampler Service (Frontend)

**File**: `hill_frontend/src/app/features/labeling/services/resampler.service.ts` (new file)

**Dependencies**: Add `lttb` npm package or implement MinMaxLTTB in TypeScript

```typescript
export interface ResampledData {
  x: Float64Array;
  channels: Map<string, Float64Array>;
  pointCount: number;
}

@Injectable({ providedIn: 'root' })
export class ResamplerService {
  private readonly TARGET_POINTS_PER_CHANNEL = 5000;
  
  resample(x: Float64Array, channels: Map<string, Float64Array>): ResampledData {
    const numPoints = x.length;
    
    // No resampling needed
    if (numPoints <= this.TARGET_POINTS_PER_CHANNEL) {
      return { x, channels, pointCount: numPoints };
    }
    
    // Collect indices from each channel using MinMaxLTTB
    const allIndices = new Set<number>();
    
    channels.forEach((values, name) => {
      const indices = this.minMaxLTTB(x, values, this.TARGET_POINTS_PER_CHANNEL);
      indices.forEach(i => allIndices.add(i));
    });
    
    // Sort indices
    const selectedIndices = Array.from(allIndices).sort((a, b) => a - b);
    
    // Extract values at selected indices
    const xOut = new Float64Array(selectedIndices.length);
    const channelsOut = new Map<string, Float64Array>();
    
    selectedIndices.forEach((idx, i) => {
      xOut[i] = x[idx];
    });
    
    channels.forEach((values, name) => {
      const out = new Float64Array(selectedIndices.length);
      selectedIndices.forEach((idx, i) => {
        out[i] = values[idx];
      });
      channelsOut.set(name, out);
    });
    
    return { x: xOut, channels: channelsOut, pointCount: selectedIndices.length };
  }
  
  private minMaxLTTB(x: Float64Array, y: Float64Array, targetPoints: number): number[] {
    // Implementation of MinMaxLTTB algorithm
    // ... (implement or use library)
  }
}
```

---

### Phase 4: Frontend - Integration

#### Task 4.1: Modify Chart Component

**File**: `hill_frontend/src/app/features/labeling/components/chart/chart.ts`

**Changes**:
1. Inject new services
2. Listen to Plotly relayout events
3. Implement viewport change handler

```typescript
@Component({...})
export class ChartComponent {
  private isLoading = signal(false);
  
  constructor(
    private cacheManager: CacheManagerService,
    private fetchController: FetchControllerService,
    private resampler: ResamplerService,
    private chartService: ChartService
  ) {}
  
  private initializeEventListeners(): void {
    this.chartElement.on('plotly_relayout', (event: any) => {
      const xMin = event['xaxis.range[0]'];
      const xMax = event['xaxis.range[1]'];
      
      if (xMin !== undefined && xMax !== undefined) {
        this.onViewportChange(xMin, xMax);
      }
    });
  }
  
  private onViewportChange(viewMin: number, viewMax: number): void {
    // Step 1: Get cached data and resample for display
    const cachedSlice = this.cacheManager.getSlice(viewMin, viewMax);
    
    if (cachedSlice) {
      const displayData = this.resampler.resample(cachedSlice.x, cachedSlice.channels);
      this.updateChart(displayData);
      
      // Step 2: Check if we need to fetch more data
      const { shouldFetch, reason } = this.cacheManager.shouldFetchNewData(
        viewMin,
        viewMax,
        displayData.pointCount
      );
      
      if (shouldFetch) {
        this.fetchNewData(viewMin, viewMax);
      }
    } else {
      // No cache, must fetch
      this.isLoading.set(true);
      this.fetchNewData(viewMin, viewMax);
    }
  }
  
  private fetchNewData(viewMin: number, viewMax: number): void {
    this.isLoading.set(true);
    
    const { xMin, xMax } = this.cacheManager.calculateFetchRange(viewMin, viewMax);
    
    this.fetchController.debouncedFetch(
      this.fileId,
      xMin,
      xMax,
      this.channelNames
    ).subscribe({
      next: (response) => {
        this.cacheManager.updateCache(this.fileId, response);
        
        // Re-render with new data
        const slice = this.cacheManager.getSlice(viewMin, viewMax);
        if (slice) {
          const displayData = this.resampler.resample(slice.x, slice.channels);
          this.updateChart(displayData);
        }
        
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to fetch viewport data:', err);
        this.isLoading.set(false);
      }
    });
  }
  
  private updateChart(data: ResampledData): void {
    // Convert to Plotly traces and update
    const traces = this.buildTraces(data);
    Plotly.react(this.chartElement, traces, this.layout);
  }
}
```

#### Task 4.2: Add Loading Indicator

**File**: `hill_frontend/src/app/features/labeling/components/chart/chart.html`

```html
<div class="chart-container">
  <div id="myChartDiv"></div>
  
  <!-- Small loading indicator in corner (Option B) -->
  @if (isLoading()) {
    <div class="loading-indicator">
      <mat-spinner diameter="24"></mat-spinner>
    </div>
  }
</div>
```

**File**: `hill_frontend/src/app/features/labeling/components/chart/chart.scss`

```scss
.chart-container {
  position: relative;
}

.loading-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  padding: 4px;
}
```

#### Task 4.3: Modify File Repository

**File**: `hill_frontend/src/app/core/repositories/files.repository.ts`

Add method to fetch viewport data:

```typescript
getViewport(
  fileId: string, 
  xMin: number, 
  xMax: number, 
  maxPoints?: number
): Observable<ArrayBuffer> {
  const params = new URLSearchParams({
    x_min: xMin.toString(),
    x_max: xMax.toString(),
  });
  if (maxPoints) {
    params.set('max_points', maxPoints.toString());
  }
  
  return this.http.get(`${this.apiUrl}/files/${fileId}/viewport?${params}`, {
    responseType: 'arraybuffer'
  });
}
```

---

### Phase 5: Edge Cases & Polish

#### Task 5.1: Handle Initial File Load

**Behavior**:
1. Fetch file info (includes `useBinaryFormat` flag)
2. If small file: load as JSON (current behavior)
3. If large file: 
   - Load initial data (5k per channel resampled) 
   - Render immediately
   - Initialize cache with initial data

#### Task 5.2: Handle File Switching

**Changes in `labeling-page.ts`**:
```typescript
onFileChange(newFileId: string): void {
  this.cacheManager.clearCache();
  this.fetchController.cancelPendingRequest();
  this.loadFile(newFileId);
}
```

#### Task 5.3: Handle Edge of Data

**In Cache Manager**:
```typescript
calculateFetchRange(viewMin: number, viewMax: number, fileMetadata: FileMetadata): { xMin: number; xMax: number } {
  const viewWidth = viewMax - viewMin;
  
  return {
    xMin: Math.max(fileMetadata.xMin, viewMin - viewWidth),
    xMax: Math.min(fileMetadata.xMax, viewMax + viewWidth),
  };
}
```

#### Task 5.4: Handle Network Errors

```typescript
private fetchNewData(...): void {
  this.fetchController.debouncedFetch(...).subscribe({
    error: (err) => {
      // Show error toast
      this.snackBar.open('Failed to load chart data. Please try again.', 'Dismiss', {
        duration: 5000
      });
      this.isLoading.set(false);
      // Keep showing cached data if available
    }
  });
}
```

---

## File Changes Summary

### New Files

| Path | Description |
|------|-------------|
| `hill_backend/services/data_reader.py` | Memory-mapped file reader |
| `hill_backend/services/resampler.py` | MinMaxLTTB resampling service |
| `hill_frontend/src/app/core/services/binary-parser.service.ts` | Parse binary responses |
| `hill_frontend/src/app/features/labeling/services/cache-manager.service.ts` | Cache management |
| `hill_frontend/src/app/features/labeling/services/fetch-controller.service.ts` | Request handling |
| `hill_frontend/src/app/features/labeling/services/resampler.service.ts` | Frontend resampling |

### Modified Files

| Path | Changes |
|------|---------|
| `hill_workers/workers/file_parser.py` | Add binary format generation |
| `hill_backend/routes/files.py` | Add viewport endpoint, modify file endpoint |
| `hill_backend/models.py` | Add new fields to file model |
| `hill_frontend/src/app/features/labeling/components/chart/chart.ts` | Integrate new services |
| `hill_frontend/src/app/features/labeling/components/chart/chart.html` | Add loading indicator |
| `hill_frontend/src/app/features/labeling/components/chart/chart.scss` | Loading indicator styles |
| `hill_frontend/src/app/core/repositories/files.repository.ts` | Add viewport method |

### New Dependencies

| Package | Location | Version |
|---------|----------|---------|
| `tsdownsample` | Backend (pyproject.toml) | latest |
| `lttb` or custom implementation | Frontend (package.json) | - |

---

## Testing Checklist

### Unit Tests
- [ ] Binary file parsing (backend)
- [ ] Memory-mapped file reading
- [ ] MinMaxLTTB resampling (both backend and frontend)
- [ ] Union of indices algorithm
- [ ] Cache invalidation logic
- [ ] Binary response parsing (frontend)

### Integration Tests
- [ ] Viewport API endpoint
- [ ] Large file upload → binary format generation
- [ ] Initial file load (small vs large)
- [ ] Zoom in/out triggers correct fetch behavior
- [ ] Pan left/right triggers correct fetch behavior
- [ ] Request cancellation on rapid interactions

### Manual Testing Scenarios
- [ ] Load file with 10k points (should use JSON, no viewport API)
- [ ] Load file with 500k points (should use binary, viewport API)
- [ ] Load file with 5M points (should use binary, heavy resampling)
- [ ] Zoom deep into 5M point file (should trigger resolution fetch)
- [ ] Rapid zoom in/out (should debounce and cancel requests)
- [ ] Switch between files (should clear cache)
- [ ] Network disconnect during fetch (should show error, keep cached data)

---

## Rollout Plan

1. **Phase 1**: Backend changes (can be deployed independently)
   - File parser generates binary format for new uploads
   - Viewport API available but not used

2. **Phase 2**: Frontend changes
   - New services integrated
   - Feature flag to enable/disable new behavior

3. **Phase 3**: Migration
   - Script to convert existing large files to binary format
   - Remove feature flag, enable for all users

---

## Future Enhancements (Not in Scope)

- WebSocket for streaming large initial loads
- Web Worker for off-main-thread resampling
- IndexedDB for persistent client-side cache
- Metrics/logging for performance monitoring

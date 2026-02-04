import { Injectable } from '@angular/core';

/**
 * Response from viewport API endpoint
 */
export interface ViewportResponse {
  x: Float64Array;
  channels: Map<string, Float64Array>;
  metadata: {
    totalPoints: number;
    returnedPoints: number;
    isFullResolution: boolean;
    xMin: number;
    xMax: number;
    numColumns: number;
    channelNames: string[];
    xType?: 'timestamp' | 'numeric';
    xFormat?: string;
  };
}

/**
 * Binary Parser Service
 * Parses binary ArrayBuffer responses from the viewport API
 */
@Injectable({
  providedIn: 'root'
})
export class BinaryParserService {

  /**
   * Parse a viewport response from the backend
   * 
   * @param buffer The binary ArrayBuffer from the response
   * @param headers The response headers containing metadata
   * @returns Parsed ViewportResponse with typed arrays
   */
  parseViewportResponse(buffer: ArrayBuffer, headers: Headers): ViewportResponse {
    // Check if buffer is valid
    if (!buffer || buffer.byteLength === 0) {
      console.warn('[BinaryParser] Empty buffer received');
      return this.createEmptyResponse();
    }
    
    // Check if buffer size is valid for Float64Array (must be multiple of 8)
    if (buffer.byteLength % 8 !== 0) {
      console.error(`[BinaryParser] Invalid buffer size: ${buffer.byteLength} bytes (not multiple of 8)`);
      throw new Error(`Invalid binary data: buffer size ${buffer.byteLength} is not a multiple of 8 bytes`);
    }
    
    // Parse headers - these might not be accessible if CORS isn't configured correctly
    const totalPoints = parseInt(headers.get('X-Total-Points') || '0', 10);
    let returnedPoints = parseInt(headers.get('X-Returned-Points') || '0', 10);
    const isFullResolution = headers.get('X-Full-Resolution') === 'true';
    const numColumns = parseInt(headers.get('X-Num-Columns') || '1', 10);
    const xMin = parseFloat(headers.get('X-X-Min') || '0');
    const xMax = parseFloat(headers.get('X-X-Max') || '0');
    const channelNamesStr = headers.get('X-Channel-Names') || '';
    const channelNames = channelNamesStr ? channelNamesStr.split(',').filter(n => n.length > 0) : [];
    const xType = (headers.get('X-X-Type') || 'numeric') as 'timestamp' | 'numeric';
    const xFormat = headers.get('X-X-Format') || undefined;
    
    // If headers weren't accessible (CORS issue), try to infer from buffer
    if (returnedPoints === 0 && buffer.byteLength > 0 && numColumns > 0) {
      // Total float64 values = buffer.byteLength / 8
      // Each column has the same number of points
      const totalValues = buffer.byteLength / 8;
      returnedPoints = Math.floor(totalValues / numColumns);
      console.warn(`[BinaryParser] Headers not accessible, inferred ${returnedPoints} points from ${numColumns} columns`);
    }
    
    // If we still can't determine the structure, use a fallback
    if (returnedPoints === 0 || numColumns === 0) {
      console.error('[BinaryParser] Cannot determine data structure from headers');
      // Assume single column (x only) as fallback
      const totalValues = buffer.byteLength / 8;
      returnedPoints = totalValues;
      console.warn(`[BinaryParser] Using fallback: ${returnedPoints} points as single column`);
    }

    // Parse binary data
    const data = new Float64Array(buffer);
    const pointsPerColumn = returnedPoints;

    // Extract x and channels
    // Layout: [x_values][ch1_values][ch2_values]...
    const x = data.subarray(0, pointsPerColumn);
    const channels = new Map<string, Float64Array>();

    for (let i = 0; i < channelNames.length; i++) {
      const start = (i + 1) * pointsPerColumn;
      const end = start + pointsPerColumn;
      if (end <= data.length) {
        channels.set(channelNames[i], data.subarray(start, end));
      } else {
        console.warn(`[BinaryParser] Channel ${channelNames[i]} out of bounds: ${start}-${end} > ${data.length}`);
      }
    }

    return {
      x,
      channels,
      metadata: {
        totalPoints,
        returnedPoints,
        isFullResolution,
        xMin,
        xMax,
        numColumns,
        channelNames,
        xType,
        xFormat
      }
    };
  }
  
  /**
   * Create an empty response for edge cases
   */
  private createEmptyResponse(): ViewportResponse {
    return {
      x: new Float64Array(0),
      channels: new Map(),
      metadata: {
        totalPoints: 0,
        returnedPoints: 0,
        isFullResolution: true,
        xMin: 0,
        xMax: 0,
        numColumns: 0,
        channelNames: [],
        xType: 'numeric',
        xFormat: undefined
      }
    };
  }

  /**
   * Convert Float64Array data back to the DataModel format expected by chart
   */
  toDataModelFormat(
    response: ViewportResponse,
    xName: string,
    xUnit: string,
    channelMeta: Array<{ name: string; unit: string; color: string }>
  ): any[] {
    const result: any[] = [];

    // X-axis trace
    result.push({
      x: true,
      name: xName,
      unit: xUnit,
      data: Array.from(response.x)
    });

    // Channel traces
    for (const meta of channelMeta) {
      const channelData = response.channels.get(meta.name);
      if (channelData) {
        result.push({
          x: false,
          name: meta.name,
          unit: meta.unit,
          color: meta.color,
          data: Array.from(channelData)
        });
      }
    }

    return result;
  }
}

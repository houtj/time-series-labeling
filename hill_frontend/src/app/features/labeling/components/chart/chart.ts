import { Component, OnInit, AfterViewInit, OnDestroy, ViewChild, ElementRef, input, inject, effect, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as Plotly from 'plotly.js-dist-min';

// PrimeNG imports
import { ProgressSpinnerModule } from 'primeng/progressspinner';

// Core imports
import { DataModel, LabelModel, FileModel } from '../../../../core/models';

// Feature services
import { 
  ChartService, 
  LabelStateService, 
  LabelingActionsService,
  FetchControllerService,
  BinaryParserService
} from '../../services';

/**
 * Chart Component
 * Handles Plotly chart visualization and user interactions for labeling
 * Supports dynamic loading for large datasets
 */
@Component({
  selector: 'app-chart',
  imports: [CommonModule, ProgressSpinnerModule],
  standalone: true,
  templateUrl: './chart.html',
  styleUrl: './chart.scss'
})
export class ChartComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartDiv') chartDiv?: ElementRef;
  
  // Use signal inputs for reactive updates
  data = input<DataModel[]>();
  labelInfo = input<LabelModel>();
  fileInfo = input<FileModel>();
  
  private readonly chartService = inject(ChartService);
  private readonly labelState = inject(LabelStateService);
  private readonly labelingActions = inject(LabelingActionsService);
  private readonly fetchController = inject(FetchControllerService);
  private readonly binaryParser = inject(BinaryParserService);
  
  private resizeObserver?: ResizeObserver;
  private isChartInitialized = false;
  
  // Track interaction state
  private nbClick = 0;
  private startX?: string | number;
  
  // Loading state for viewport fetching
  readonly isLoading = computed(() => this.fetchController.isLoading());
  
  // Channel metadata for resampling
  private channelMeta: Array<{ name: string; unit: string; color: string }> = [];
  private xMeta: { name: string; unit: string } = { name: '', unit: '' };
  
  // X-axis metadata from file
  private xType: 'timestamp' | 'numeric' = 'numeric';
  private xFormat: string | undefined;
  
  // Full data range (for reset axes)
  private fullXMin?: number;
  private fullXMax?: number;
  
  constructor() {
    // React to data changes - reinitialize chart when data changes
    effect(() => {
      const currentData = this.data();
      if (currentData && this.chartDiv && this.isChartInitialized) {
        // Data changed after initial load - reinitialize chart
        setTimeout(() => {
          this.initializeChart();
        }, 0);
      }
    });
    
    // React to file changes - cancel pending requests when file changes
    effect(() => {
      const file = this.fileInfo();
      if (file && file._id?.$oid) {
        this.fetchController.cancelPendingRequest();
      }
    });
    
    // React to label state changes
    effect(() => {
      const shapes = this.labelState.plotlyShapes();
      const annotations = this.labelState.plotlyAnnotations();
      
      if (this.chartDiv && shapes.length >= 0) {
        this.chartService.updateShapes(shapes);
      }
      
      if (this.chartDiv && annotations.length >= 0) {
        this.chartService.updateAnnotations(annotations);
      }
    });
    
    // React to button mode changes
    effect(() => {
      const button = this.labelState.selectedButton();
      if (button === 'none') {
        this.nbClick = 0;
        this.startX = undefined;
        this.chartService.removeTempShapes();
      }
    });
  }
  
  ngOnInit(): void {
    // Component initialization
  }
  
  ngAfterViewInit(): void {
    // Initialize chart after view is ready
    const currentData = this.data();
    if (this.chartDiv && currentData) {
      setTimeout(() => {
        this.initializeChart();
        this.setupResizeObserver();
        this.isChartInitialized = true;
      }, 100);
    }
  }
  
  ngOnDestroy(): void {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    
    // Cancel any pending fetch requests
    this.fetchController.cancelPendingRequest();
  }
  
  /**
   * Initialize the Plotly chart
   */
  private initializeChart(): void {
    const currentData = this.data();
    const currentLabelInfo = this.labelInfo();
    const currentFileInfo = this.fileInfo();
    if (!this.chartDiv || !currentData) return;
    
    // Store channel metadata for resampling
    this.extractChannelMetadata(currentData);
    
    // Clear existing channel list
    this.labelState.clearChannels();
    
    // Initialize chart and populate channel list
    // Pass xType for proper timestamp formatting on x-axis
    const channelList: any[] = [];
    this.chartService.initializeChart(
      this.chartDiv, 
      currentData, 
      channelList,
      currentFileInfo?.xType
    );
    
    // Store channels in state
    channelList.forEach(channel => this.labelState.addChannel(channel));
    
    // Update label visualizations if label info exists
    if (currentLabelInfo) {
      this.labelState.updateLabel(currentLabelInfo);
    }
    
    // Attach Plotly event listeners
    this.attachEventListeners();
  }
  
  /**
   * Extract channel metadata from data for later use
   */
  private extractChannelMetadata(data: DataModel[]): void {
    const xTrace = data.find(d => d.x);
    const channels = data.filter(d => !d.x);
    const file = this.fileInfo();
    
    if (xTrace) {
      this.xMeta = { name: xTrace.name, unit: xTrace.unit };
    }
    
    this.channelMeta = channels.map(ch => ({
      name: ch.name,
      unit: ch.unit,
      color: ch.color
    }));
    
    // Store x-axis type and format from file metadata
    this.xType = file?.xType || 'numeric';
    this.xFormat = file?.xFormat;
    
    // Store full x range from file metadata or from data
    if (file?.xMin !== undefined && file?.xMax !== undefined) {
      this.fullXMin = file.xMin;
      this.fullXMax = file.xMax;
    } else if (xTrace && Array.isArray(xTrace.data) && xTrace.data.length > 0) {
      // Fallback: get range from initial data
      const xData = xTrace.data as number[];
      this.fullXMin = xData[0];
      this.fullXMax = xData[xData.length - 1];
    }
    
  }
  
  /**
   * Attach Plotly event listeners
   */
  private attachEventListeners(): void {
    if (!this.chartDiv) return;
    
    const element = this.chartDiv.nativeElement;
    
    element.on('plotly_click', (data: Plotly.PlotMouseEvent) => {
      this.onPlotlyClick(data);
    });
    
    element.on('plotly_hover', (data: Plotly.PlotMouseEvent) => {
      this.onPlotlyHover(data);
    });
    
    // Handle viewport changes (zoom/pan) for large file optimization
    element.on('plotly_relayout', (eventData: any) => {
      this.onPlotlyRelayout(eventData);
    });
    
    // Handle double-click to reset axes
    element.on('plotly_doubleclick', () => {
      this.handleResetAxes();
    });
  }
  
  /**
   * Handle reset axes - fetch full range data
   */
  private handleResetAxes(): void {
    const currentFileInfo = this.fileInfo();
    
    if (!currentFileInfo?.useBinaryFormat || !currentFileInfo._id?.$oid) {
      return;
    }
    
    if (this.fullXMin !== undefined && this.fullXMax !== undefined) {
      this.handleViewportChange(this.fullXMin, this.fullXMax, currentFileInfo._id.$oid);
    }
  }
  
  /**
   * Handle Plotly relayout events (zoom/pan)
   * For large files, this triggers viewport data fetching
   * 
   * With the new format:
   * - X-axis values are timestamps (float64 seconds) or numeric values
   * - Plotly returns these values directly in relayout events
   * - No conversion needed - pass directly to viewport API
   */
  private onPlotlyRelayout(eventData: any): void {
    const currentFileInfo = this.fileInfo();
    
    // Only handle viewport updates for large files using binary format
    if (!currentFileInfo?.useBinaryFormat || !currentFileInfo._id?.$oid) {
      return;
    }
    
    // Check if this is a zoom/pan event with x-axis range change
    // Handle both formats: xaxis.range[0]/[1] and xaxis.range as array
    let xMin = eventData['xaxis.range[0]'];
    let xMax = eventData['xaxis.range[1]'];
    
    // Also check for xaxis.range as array
    if (xMin === undefined && xMax === undefined && Array.isArray(eventData['xaxis.range'])) {
      xMin = eventData['xaxis.range'][0];
      xMax = eventData['xaxis.range'][1];
    }
    
    // Handle autorange/autosize events (multiple possible formats)
    const xAutoRange = eventData['xaxis.autorange'] || eventData['autorange'] || eventData['autosize'];
    
    if (xMin === undefined && xMax === undefined && !xAutoRange) {
      return; // Not a viewport change event
    }
    
    // Get current viewport range from layout
    let viewMin: number;
    let viewMax: number;
    
    if (xMin !== undefined && xMax !== undefined) {
      // Convert x values to Unix timestamps (seconds) for API
      viewMin = this.convertToTimestamp(xMin);
      viewMax = this.convertToTimestamp(xMax);
      
      // Validate values
      if (isNaN(viewMin) || isNaN(viewMax)) {
        console.warn('[Chart] Invalid viewport values:', { xMin, xMax });
        return;
      }
    } else if (xAutoRange) {
      // Autorange/Autosize (Reset axes) - use stored full data range
      if (this.fullXMin !== undefined && this.fullXMax !== undefined) {
        viewMin = this.fullXMin;
        viewMax = this.fullXMax;
      } else {
        console.warn('[Chart] No full x range stored, cannot reset axes');
        return;
      }
    } else {
      return;
    }
    
    this.handleViewportChange(viewMin, viewMax, currentFileInfo._id.$oid);
  }
  
  /**
   * Convert a Plotly x-axis value to Unix timestamp (seconds)
   * Handles various formats: Date objects, date strings, and numbers
   */
  private convertToTimestamp(value: any): number {
    // If already a number
    if (typeof value === 'number') {
      return value;
    }
    
    // If it's a Date object
    if (value instanceof Date) {
      return value.getTime() / 1000;  // Convert ms to seconds
    }
    
    // If it's a string, try to parse it
    if (typeof value === 'string') {
      // Try parsing as ISO date string
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return date.getTime() / 1000;  // Convert ms to seconds
      }
      
      // Try parsing as number string
      const num = parseFloat(value);
      if (!isNaN(num)) {
        return num;
      }
    }
    
    console.warn('[Chart] Unable to convert value to timestamp:', value);
    return NaN;
  }
  
  /**
   * Handle viewport change - fetch resampled data from backend
   * 
   * Simplified flow:
   * 1. Send viewport range to backend
   * 2. Backend resamples to 5k points/channel
   * 3. Frontend renders directly
   */
  private handleViewportChange(viewMin: number, viewMax: number, fileId: string): void {
    console.debug('[Viewport] Fetching data for range:', { viewMin, viewMax });
    
    // Fetch resampled data from backend (with debounce)
    this.fetchController.debouncedFetch(fileId, viewMin, viewMax, 5000).subscribe({
      next: (response) => {
        console.debug('[Viewport] Received data:', {
          points: response.metadata.returnedPoints,
          channels: response.metadata.channelNames.length
        });
        
        // Convert to DataModel format
        const dataModels = this.binaryParser.toDataModelFormat(
          response,
          this.xMeta.name,
          this.xMeta.unit,
          this.channelMeta
        );
        
        // Update chart, preserving current viewport
        this.updateChartTracesWithRange(dataModels, viewMin, viewMax);
      },
      error: (err) => {
        if (err.message !== 'Request cancelled') {
          console.error('[Viewport] Failed to fetch data:', err);
        }
      }
    });
  }
  
  /**
   * Update chart traces with new data (without reinitializing)
   */
  private updateChartTraces(data: DataModel[]): void {
    this.updateChartTracesWithRange(data);
  }
  
  /**
   * Update chart traces with new data while preserving x-axis range
   * 
   * @param data New data to display
   * @param viewMin Optional - preserve this x-axis minimum
   * @param viewMax Optional - preserve this x-axis maximum
   */
  private updateChartTracesWithRange(
    data: DataModel[], 
    viewMin?: number, 
    viewMax?: number
  ): void {
    if (!this.chartDiv) return;
    
    const element = this.chartDiv.nativeElement;
    const xTrace = data.find(d => d.x);
    const channels = data.filter(d => !d.x);
    
    if (!xTrace) return;
    
    // Convert x data to Date objects if this is a timestamp x-axis
    // This ensures consistency with the initial chart setup
    let xData: (number | Date)[] = xTrace.data as number[];
    
    if (this.xType === 'timestamp') {
      const firstValue = xTrace.data[0];
      if (typeof firstValue === 'number' && firstValue > 1e9) {
        // Convert Unix timestamps (seconds) to Date objects
        xData = (xTrace.data as number[]).map(ts => new Date(ts * 1000));
      }
    }
    
    // Build update object for traces
    const traceUpdate: any = {
      x: channels.map(() => xData),
      y: channels.map(ch => ch.data)
    };
    
    // Update all traces
    const traceIndices = channels.map((_, i) => i);
    
    // If we need to preserve the viewport, also update layout
    if (viewMin !== undefined && viewMax !== undefined) {
      // Convert viewport to Date if needed for x-axis
      let rangeMin: number | Date = viewMin;
      let rangeMax: number | Date = viewMax;
      
      if (this.xType === 'timestamp' && viewMin > 1e9) {
        rangeMin = new Date(viewMin * 1000);
        rangeMax = new Date(viewMax * 1000);
      }
      
      // Use Plotly.react to update both data and layout atomically
      // This prevents the viewport from jumping
      const currentPlotData = (element as any).data;
      const currentLayout = (element as any).layout;
      
      // Update trace data
      for (let i = 0; i < traceIndices.length; i++) {
        if (currentPlotData[i]) {
          currentPlotData[i].x = xData;
          currentPlotData[i].y = channels[i].data;
        }
      }
      
      // Preserve x-axis range
      if (currentLayout.xaxis) {
        currentLayout.xaxis.range = [rangeMin, rangeMax];
        currentLayout.xaxis.autorange = false;
      }
      
      // Use react for atomic update
      Plotly.react(element, currentPlotData, currentLayout);
    } else {
      // Simple restyle without layout changes
      Plotly.restyle(element, traceUpdate, traceIndices);
    }
  }
  
  /**
   * Handle Plotly click events
   */
  private onPlotlyClick(data: Plotly.PlotMouseEvent): void {
    const button = this.labelState.selectedButton();
    
    if (button === 'guideline') {
      if (this.nbClick === 0) {
        const selectedYAxis = this.labelState.selectedYAxis();
        if (selectedYAxis) {
          const newGuideline = this.chartService.createGuideline(selectedYAxis);
          
          // Add guideline to label info (optimistic update)
          const currentLabelInfo = this.labelInfo();
          if (currentLabelInfo) {
            currentLabelInfo.guidelines.push(newGuideline);
            this.labelState.updateLabel(currentLabelInfo);
            
            // Auto-save to database
            this.labelingActions.queueAutoSave(currentLabelInfo);
          }
          
          // Reset button state
          this.labelState.updateSelectedButton('none');
        }
      }
    }
    
    if (button === 'label') {
      if (this.nbClick === 0) {
        // First click - set start point
        this.startX = data.points[0].x as string | number;
        this.nbClick++;
      } else if (this.nbClick === 1) {
        // Second click - set end point and emit event
        const endX = data.points[0].x as string | number;
        this.nbClick = 0;
        
        // Emit event to parent to show label selection dialog
        this.labelState.setLabelSelection(this.startX!, endX);
        this.startX = undefined;
      }
    }
  }
  
  /**
   * Handle Plotly hover events
   */
  private onPlotlyHover(data: Plotly.PlotMouseEvent): void {
    const button = this.labelState.selectedButton();
    
    if (button === 'label') {
      this.chartService.handleLabelHover(data, this.nbClick, this.startX);
    }
    
    if (button === 'guideline') {
      if (this.nbClick === 0) {
        const selectedYAxis = this.labelState.selectedYAxis();
        if (selectedYAxis) {
          this.chartService.handleGuidelineHover(data, selectedYAxis);
        }
      }
    }
  }
  
  /**
   * Setup resize observer for responsive chart
   */
  private setupResizeObserver(): void {
    if (!this.chartDiv) return;
    
    // Plotly's responsive:true config handles window resize events automatically
    // We just need a ResizeObserver for container size changes
    this.resizeObserver = new ResizeObserver(() => {
      // Dispatch window resize event to trigger Plotly's built-in resize handler
      window.dispatchEvent(new Event('resize'));
    });
    
    this.resizeObserver.observe(this.chartDiv.nativeElement);
  }
}

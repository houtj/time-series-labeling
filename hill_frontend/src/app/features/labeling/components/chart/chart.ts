import { Component, OnInit, AfterViewInit, OnDestroy, ViewChild, ElementRef, input, inject, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as Plotly from 'plotly.js-dist-min';

// Core imports
import { DataModel, LabelModel } from '../../../../core/models';

// Feature services
import { ChartService, LabelStateService, LabelingActionsService } from '../../services';

/**
 * Chart Component
 * Handles Plotly chart visualization and user interactions for labeling
 */
@Component({
  selector: 'app-chart',
  imports: [CommonModule],
  standalone: true,
  templateUrl: './chart.html',
  styleUrl: './chart.scss'
})
export class ChartComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartDiv') chartDiv?: ElementRef;
  
  // Use signal inputs for reactive updates
  data = input<DataModel[]>();
  labelInfo = input<LabelModel>();
  
  private readonly chartService = inject(ChartService);
  private readonly labelState = inject(LabelStateService);
  private readonly labelingActions = inject(LabelingActionsService);
  
  private resizeObserver?: ResizeObserver;
  private isChartInitialized = false;
  
  // Track interaction state
  private nbClick = 0;
  private startX?: string | number;
  
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
  }
  
  /**
   * Initialize the Plotly chart
   */
  private initializeChart(): void {
    const currentData = this.data();
    const currentLabelInfo = this.labelInfo();
    if (!this.chartDiv || !currentData) return;
    
    // Clear existing channel list
    this.labelState.clearChannels();
    
    // Initialize chart and populate channel list
    const channelList: any[] = [];
    this.chartService.initializeChart(this.chartDiv, currentData, channelList);
    
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

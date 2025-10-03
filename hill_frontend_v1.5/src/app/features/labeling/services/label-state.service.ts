import { Injectable, signal, computed } from '@angular/core';
import { LabelModel } from '../../../core/models';

/**
 * Label State Service
 * Manages labeling-specific state using Angular Signals
 * Replaces the old LabelingDatabaseService
 */
@Injectable({
  providedIn: 'root'
})
export class LabelStateService {
  // Chart-related state
  readonly channelList = signal<{ channelName: string; yaxis: string; color: string }[]>([]);
  readonly selectedButton = signal<'none' | 'label' | 'guideline'>('none');
  
  // Plotly visualization state
  readonly plotlyShapes = signal<Partial<Plotly.Shape>[]>([]);
  readonly plotlyAnnotations = signal<Partial<Plotly.Annotations>[]>([]);
  
  // Label data
  readonly currentLabel = signal<LabelModel | undefined>(undefined);
  readonly events = computed(() => this.currentLabel()?.events || []);
  readonly guidelines = computed(() => this.currentLabel()?.guidelines || []);
  
  // Selection state
  readonly selectedEvent = signal<LabelModel['events'][0] | undefined>(undefined);
  readonly selectedEventIndex = signal<number | undefined>(undefined);
  readonly selectedGuideline = signal<LabelModel['guidelines'][0] | undefined>(undefined);
  readonly selectedYAxis = signal<{ channelName: string; yaxis: string; color: string } | undefined>(undefined);
  
  // Label selection (for event creation)
  readonly labelSelectionStart = signal<string | number | undefined>(undefined);
  readonly labelSelectionEnd = signal<string | number | undefined>(undefined);
  
  /**
   * Update the selected button mode
   */
  updateSelectedButton(button: 'none' | 'label' | 'guideline'): void {
    this.selectedButton.set(button);
  }

  /**
   * Update the label information and recalculate shapes/annotations
   */
  updateLabel(labelInfo: LabelModel): void {
    this.currentLabel.set(labelInfo);
    const plotlyData = this.labels2PlotlyShapes(labelInfo);
    this.plotlyShapes.set(plotlyData.shapes);
    this.plotlyAnnotations.set(plotlyData.annotations);
  }

  /**
   * Convert label data to Plotly shapes and annotations
   */
  private labels2PlotlyShapes(labelInfo: LabelModel): {
    shapes: Partial<Plotly.Shape>[];
    annotations: Partial<Plotly.Annotations>[];
  } {
    const plotlyShapes: Partial<Plotly.Shape>[] = [];
    const plotlyAnnotations: Partial<Plotly.Annotations>[] = [];

    // Convert events to rectangles
    for (const event of labelInfo.events) {
      if (event.hide === false) {
        const rect: Partial<Plotly.Shape> = {
          type: 'rect',
          yref: 'paper',
          xref: 'x',
          y0: 1,
          y1: 0,
          x0: event.start,
          x1: event.end,
          fillcolor: event.color,
          opacity: 0.2,
          line: {
            color: event.color,
            width: 1,
            dash: 'dot'
          }
        };
        plotlyShapes.push(rect);

        // Add start annotation
        const annotationStart: Partial<Plotly.Annotations> = {
          showarrow: false,
          yref: 'paper',
          x: event.start,
          xanchor: 'center',
          y: 1,
          yanchor: 'bottom',
          text: 'start',
          bgcolor: 'rgba(149, 163, 184, 0.8)',
          font: {
            color: event.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
          }
        };

        // Add end annotation
        const annotationEnd: Partial<Plotly.Annotations> = {
          showarrow: false,
          yref: 'paper',
          x: event.end,
          xanchor: 'center',
          y: 1,
          yanchor: 'bottom',
          text: 'end',
          bgcolor: 'rgba(149, 163, 184, 0.8)',
          font: {
            color: event.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
          }
        };

        // Add event label annotation
        const midPoint = new Date(event.start).getTime() + 
          ((new Date(event.end).getTime() - new Date(event.start).getTime()) / 2);
        
        const annotationEvent: Partial<Plotly.Annotations> = {
          showarrow: false,
          yref: 'paper',
          x: midPoint,
          xanchor: 'center',
          y: 1,
          yanchor: 'bottom',
          text: `${event.className} - ${event.labeler}`,
          bgcolor: 'rgba(149, 163, 184, 0.8)',
          font: {
            color: event.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
          }
        };

        plotlyAnnotations.push(annotationStart, annotationEnd, annotationEvent);
      }
    }

    // Convert guidelines to horizontal lines
    for (const guide of labelInfo.guidelines) {
      if (guide.hide === false) {
        const guideline: Partial<Plotly.Shape> = {
          type: 'line',
          yref: guide.yaxis as any,
          xref: 'paper',
          x0: this.channelList().length * 0.04 - 0.03,
          x1: 0.95,
          y0: guide.y,
          y1: guide.y,
          opacity: 0.5,
          line: {
            color: guide.color,
            width: 1,
            dash: 'dash'
          }
        };
        plotlyShapes.push(guideline);

        // Add guideline annotation
        const guideAnnotation: Partial<Plotly.Annotations> = {
          showarrow: false,
          xref: 'paper',
          yref: guide.yaxis as any,
          x: 1,
          xanchor: 'right',
          y: guide.y as string | number,
          yanchor: 'middle',
          text: `${guide.channelName} - ${guide.y}`,
          bgcolor: 'rgba(149, 163, 184, 0.8)',
          font: {
            color: guide.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
          }
        };
        plotlyAnnotations.push(guideAnnotation);
      }
    }

    return {
      shapes: plotlyShapes,
      annotations: plotlyAnnotations
    };
  }

  /**
   * Add a new channel to the channel list
   */
  addChannel(channel: { channelName: string; yaxis: string; color: string }): void {
    this.channelList.update(list => [...list, channel]);
  }

  /**
   * Clear the channel list
   */
  clearChannels(): void {
    this.channelList.set([]);
  }

  /**
   * Select an event
   */
  selectEvent(event: LabelModel['events'][0], index: number): void {
    this.selectedEvent.set(event);
    this.selectedEventIndex.set(index);
  }

  /**
   * Clear event selection
   */
  clearEventSelection(): void {
    this.selectedEvent.set(undefined);
    this.selectedEventIndex.set(undefined);
  }

  /**
   * Select a guideline
   */
  selectGuideline(guideline: LabelModel['guidelines'][0]): void {
    this.selectedGuideline.set(guideline);
  }

  /**
   * Clear guideline selection
   */
  clearGuidelineSelection(): void {
    this.selectedGuideline.set(undefined);
  }

  /**
   * Set selected Y axis for guideline creation
   */
  setSelectedYAxis(yAxis: { channelName: string; yaxis: string; color: string }): void {
    this.selectedYAxis.set(yAxis);
  }

  /**
   * Set label selection coordinates for event creation
   */
  setLabelSelection(start: string | number, end: string | number): void {
    this.labelSelectionStart.set(start);
    this.labelSelectionEnd.set(end);
  }

  /**
   * Clear label selection
   */
  clearLabelSelection(): void {
    this.labelSelectionStart.set(undefined);
    this.labelSelectionEnd.set(undefined);
  }

  /**
   * Reset all state
   */
  reset(): void {
    this.channelList.set([]);
    this.selectedButton.set('none');
    this.plotlyShapes.set([]);
    this.plotlyAnnotations.set([]);
    this.currentLabel.set(undefined);
    this.selectedEvent.set(undefined);
    this.selectedEventIndex.set(undefined);
    this.selectedGuideline.set(undefined);
    this.selectedYAxis.set(undefined);
    this.labelSelectionStart.set(undefined);
    this.labelSelectionEnd.set(undefined);
  }
}


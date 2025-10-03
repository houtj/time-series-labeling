import { Injectable, ElementRef } from '@angular/core';
import * as Plotly from 'plotly.js-dist-min';
import { DataModel, LabelModel } from '../../../core/models';

/**
 * Chart Service
 * Manages Plotly chart initialization, updates, and interactions
 */
@Injectable({
  providedIn: 'root'
})
export class ChartService {
  private layout: Partial<Plotly.Layout> = {
    showlegend: true,
    legend: {
      x: 1,
      y: 1,
      xanchor: 'right',
      bgcolor: 'transparent',
      font: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
      }
    },
    hovermode: 'x',
    dragmode: 'pan',
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: {
      t: 20,
      r: 5,
      b: 20,
      l: 40
    },
    shapes: [],
    annotations: [],
    xaxis: {
      showgrid: true,
      color: 'var(--text-color)',
      tickfont: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        size: 14,
        color: 'var(--text-color-secondary)'
      }
    },
    hoverlabel: {
      font: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
      }
    }
  };

  private config: Partial<Plotly.Config> = {
    responsive: true,
    scrollZoom: true,
    displaylogo: false,
    displayModeBar: false
  };

  private plotlyChartElement?: HTMLElement;

  getLayout(): Partial<Plotly.Layout> {
    return this.layout;
  }

  getConfig(): Partial<Plotly.Config> {
    return this.config;
  }

  /**
   * Initialize the Plotly chart with data
   */
  initializeChart(plotlyChart: ElementRef, data: DataModel[], channelList: any[]): void {
    // Store reference to chart element
    this.plotlyChartElement = plotlyChart.nativeElement;
    
    const x_trace = data.find(c => c.x === true)!;
    const channels = data.filter(c => c.x === false);

    const traces: Plotly.Data[] = channels.map((c: any, index: number) => {
      let k;
      if (index === 0) {
        k = '';
      } else {
        k = index + 1;
      }

      // @ts-expect-error - Dynamic yaxis configuration
      this.layout[`yaxis${k}`] = {
        title: {
          font: {
            color: c.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
          },
          standoff: 0,
          text: `${c.name} - ${c.unit}`
        },
        tickfont: {
          color: c.color,
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
        },
        overlaying: index === 0 ? 'free' : 'y',
        side: 'left',
        position: 0.04 * index,
        showgrid: false,
        zeroline: false
      };

      channelList.push({ channelName: c.name, yaxis: `y${k}`, color: c.color });

      return {
        x: x_trace.data,
        y: c.data,
        yaxis: `y${k}`,
        name: c.name,
        type: 'scatter',
        mode: 'lines',
        line: { color: c.color }
      };
    });

    this.layout.xaxis!.domain = [channels.length * 0.04 - 0.035, 0.94];
    this.layout.xaxis!.range = [x_trace.data[0], x_trace.data[x_trace.data.length - 1]];

    Plotly.newPlot(plotlyChart.nativeElement, traces, this.layout, this.config);
  }

  /**
   * Remove temporary shapes from the chart
   */
  removeTempShapes(): void {
    if (!this.plotlyChartElement) {
      return; // Chart not initialized yet
    }
    this.layout.shapes = this.layout.shapes!.filter((s: any) => s.temp !== true);
    Plotly.relayout(this.plotlyChartElement, { shapes: this.layout.shapes });
  }

  /**
   * Handle hover interaction for label creation
   */
  handleLabelHover(data: Plotly.PlotMouseEvent, nbClick: number, startX?: string | number): void {
    switch (nbClick) {
      case 0:
        // @ts-expect-error - temp property is custom
        if (this.layout.shapes!.length !== 0 && this.layout.shapes![this.layout.shapes!.length - 1].temp !== undefined) {
          const lastShape: any = this.layout.shapes![this.layout.shapes!.length - 1];
          lastShape.x0 = data.points[0].x;
          lastShape.x1 = data.points[0].x;
          Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
        } else {
          const lastShape: any = {
            type: 'line',
            xref: 'x',
            yref: 'paper',
            y0: 0,
            y1: 1,
            x0: data.points[0].x,
            x1: data.points[0].x,
            opacity: 0.5,
            line: {
              color: '#808080',
              width: 2,
              dash: 'dash'
            },
            temp: true
          };
          this.layout.shapes?.push(lastShape);
          Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
        }
        break;
      case 1:
        const lastShape: any = this.layout.shapes![this.layout.shapes!.length - 1];
        lastShape.type = 'rect';
        lastShape.x0 = startX!;
        lastShape.x1 = data.points[0].x;
        lastShape.fillcolor = '#808080';
        lastShape.line!.width = 4;
        lastShape.line!.dash = 'dot';
        lastShape.opacity = 0.5;
        if (this.plotlyChartElement) {
          Plotly.relayout(this.plotlyChartElement, { shapes: this.layout.shapes });
        }
        break;
    }
  }

  /**
   * Handle hover interaction for guideline creation
   */
  handleGuidelineHover(data: Plotly.PlotMouseEvent, selectedYAxis: any): void {
    // @ts-expect-error - temp property is custom
    if (this.layout.shapes!.length !== 0 && this.layout.shapes![this.layout.shapes!.length - 1].temp !== undefined) {
      const lastShape: any = this.layout.shapes![this.layout.shapes!.length - 1];
      lastShape.y0 = data.points.find((c: any) => c.data.yaxis === selectedYAxis.yaxis)!.y;
      lastShape.y1 = data.points.find((c: any) => c.data.yaxis === selectedYAxis.yaxis)!.y;
      if (this.plotlyChartElement) {
        Plotly.relayout(this.plotlyChartElement, { shapes: this.layout.shapes });
      }
    } else {
      const lastShape: any = {
        type: 'line',
        yref: selectedYAxis.yaxis,
        xref: 'paper',
        x0: 0,
        x1: 1,
        y0: data.points.find((c: any) => c.data.yaxis === selectedYAxis.yaxis)!.y,
        y1: data.points.find((c: any) => c.data.yaxis === selectedYAxis.yaxis)!.y,
        opacity: 0.5,
        line: {
          color: selectedYAxis?.color,
          width: 2,
          dash: 'dash'
        },
        temp: true
      };
      this.layout.shapes?.push(lastShape);
      Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
    }
  }

  /**
   * Create a guideline from the current temp shape
   */
  createGuideline(selectedYAxis: any): LabelModel['guidelines'][0] {
    const lastShape: any = this.layout.shapes![this.layout.shapes!.length - 1];
    return {
      channelName: selectedYAxis.channelName,
      color: selectedYAxis.color,
      hide: false,
      y: lastShape.y0!,
      yaxis: lastShape.yref!
    };
  }

  /**
   * Update chart shapes
   */
  updateShapes(shapes: Partial<Plotly.Shape>[]): void {
    if (!this.plotlyChartElement) {
      return; // Chart not initialized yet
    }
    this.layout.shapes = shapes;
    Plotly.relayout(this.plotlyChartElement, { shapes: this.layout.shapes });
  }

  /**
   * Update chart annotations
   */
  updateAnnotations(annotations: Partial<Plotly.Annotations>[]): void {
    if (!this.plotlyChartElement) {
      return; // Chart not initialized yet
    }
    this.layout.annotations = annotations;
    Plotly.relayout(this.plotlyChartElement, { annotations: this.layout.annotations });
  }

  /**
   * Zoom chart to specific event
   */
  zoomToEvent(event: LabelModel['events'][0]): void {
    if (!this.plotlyChartElement) {
      return; // Chart not initialized yet
    }
    this.layout.xaxis!.range![0] = event.start as any;
    this.layout.xaxis!.range![1] = event.end as any;
    Plotly.relayout(this.plotlyChartElement, { xaxis: this.layout.xaxis });
  }

  /**
   * Trigger chart resize
   * Dispatches a window resize event which Plotly's responsive mode will catch
   */
  resizeChart(): void {
    window.dispatchEvent(new Event('resize'));
  }
}


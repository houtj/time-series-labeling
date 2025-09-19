import { Injectable, ElementRef } from '@angular/core';
import * as Plotly from 'plotly.js-dist-min';
import { DataModel, LabelModel, UserModel, ProjectModel } from '../model';

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
      bgcolor: '#c7ced9',
      font: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
      }
    },
    hovermode: 'x',
    dragmode: 'pan',
    paper_bgcolor: '#c7ced9',
    plot_bgcolor: '#e0e4ea',
    margin: {
      t:20,
      r: 5,
      b: 20,
      l: 40
    },
    shapes: [],
    annotations: [],
    xaxis: {
      showgrid: true,
      color: '#222',
      tickfont:{
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"',
        size: 16,
        color:'#444e5c'
      },
    },
    hoverlabel:{
      font:{
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
      }
    },
  };

  private config: Partial<Plotly.Config> = {
    responsive: true,
    scrollZoom: true,
    displaylogo: false,
  };

  constructor() { }

  getLayout(): Partial<Plotly.Layout> {
    return this.layout;
  }

  getConfig(): Partial<Plotly.Config> {
    return this.config;
  }

  initializeChart(plotlyChart: ElementRef, data: DataModel[], channelList: any[]): void {
    const x_trace = data.find(c => c.x === true)!;
    const channels = data.filter(c => c.x === false);
    
    const traces: Plotly.Data[] = channels.map((c, index) => {
      let k;
      if (index === 0) {
        k = '';
      } else {
        k = index + 1;
      }
      
      //@ts-expect-error
      this.layout[`yaxis${k}`] = {
        title: {
          font: {
            color: c.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
          },
          standoff: 0,
          text: `${c.name} - ${c.unit}`
        },
        tickfont: {
          color: c.color,
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
        },
        overlaying: index === 0 ? 'free' : 'y',
        side: 'left',
        position: 0.04 * index,
        showgrid: false,
        zeroline: false,
      };
      
      channelList.push({ channelName: c.name, yaxis: `y${k}`, color: c.color });
      
      return {
        x: x_trace.data,
        y: c.data,
        yaxis: `y${k}`,
        name: c.name,
        type: 'scatter',
        mode: 'lines',
        line: { color: c.color },
      };
    });

    this.layout.xaxis!.domain = [channels.length * 0.04 - 0.035, 0.94];
    this.layout.xaxis!.range = [x_trace.data[0], x_trace.data[x_trace.data.length - 1]];
    
    Plotly.newPlot(plotlyChart.nativeElement, traces, this.layout, this.config);
  }

  removeTempShapes(): void {
    //@ts-expect-error
    this.layout.shapes = this.layout.shapes!.filter(s => s.temp !== true);
    Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
  }

  handleLabelHover(data: Plotly.PlotMouseEvent, nbClick: number, startX?: string|number): void {
    switch (nbClick) {
      case 0:
        //@ts-expect-error
        if (this.layout.shapes!.length !== 0 && this.layout.shapes![this.layout.shapes!.length - 1].temp !== undefined) {
          const lastShape = this.layout.shapes![this.layout.shapes!.length - 1];
          lastShape.x0 = data.points[0].x;
          lastShape.x1 = data.points[0].x;
          Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
        } else {
          const lastShape: Plotly.Shape = {
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
            //@ts-expect-error
            temp: true
          };
          this.layout.shapes?.push(lastShape);
          Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
        }
        break;
      case 1:
        const lastShape = this.layout.shapes![this.layout.shapes!.length - 1];
        lastShape.type = 'rect';
        lastShape.x0 = startX!;
        lastShape.x1 = data.points[0].x;
        lastShape.fillcolor = '#808080';
        lastShape.line!.width = 4;
        lastShape.line!.dash = 'dot';
        lastShape.opacity = 0.5;
        Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
        break;
    }
  }

  handleGuidelineHover(data: Plotly.PlotMouseEvent, selectedYAxis: any): void {
    //@ts-expect-error
    if (this.layout.shapes!.length !== 0 && this.layout.shapes![this.layout.shapes!.length - 1].temp !== undefined) {
      const lastShape = this.layout.shapes![this.layout.shapes!.length - 1];
      lastShape.y0 = data.points.find(c => c.data.yaxis === selectedYAxis.yaxis)!.y;
      lastShape.y1 = data.points.find(c => c.data.yaxis === selectedYAxis.yaxis)!.y;
      Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
    } else {
      const lastShape: Plotly.Shape = {
        type: 'line',
        yref: selectedYAxis.yaxis,
        xref: 'paper',
        x0: 0,
        x1: 1,
        y0: data.points.find(c => c.data.yaxis === selectedYAxis.yaxis)!.y,
        y1: data.points.find(c => c.data.yaxis === selectedYAxis.yaxis)!.y,
        opacity: 0.5,
        line: {
          color: selectedYAxis?.color,
          width: 2,
          dash: 'dash'
        },
        //@ts-expect-error
        temp: true
      };
      this.layout.shapes?.push(lastShape);
      Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
    }
  }

  createGuideline(selectedYAxis: any): LabelModel['guidelines'][0] {
    return {
      channelName: selectedYAxis.channelName,
      color: selectedYAxis.color,
      hide: false,
      y: this.layout.shapes![this.layout.shapes!.length - 1].y0!,
      yaxis: this.layout.shapes![this.layout.shapes!.length - 1].yref!
    };
  }

  updateShapes(shapes: Partial<Plotly.Shape>[]): void {
    this.layout.shapes = shapes;
    Plotly.relayout('myChartDiv', { shapes: this.layout.shapes });
  }

  updateAnnotations(annotations: Partial<Plotly.Annotations>[]): void {
    this.layout.annotations = annotations;
    Plotly.relayout('myChartDiv', { annotations: this.layout.annotations });
  }

  zoomToEvent(event: LabelModel['events'][0]): void {
    this.layout.xaxis!.range![0] = event.start;
    this.layout.xaxis!.range![1] = event.end;
    Plotly.relayout('myChartDiv', { xaxis: this.layout.xaxis });
  }

  resizeChart(): void {
    window.dispatchEvent(new Event('resize'));
  }
}

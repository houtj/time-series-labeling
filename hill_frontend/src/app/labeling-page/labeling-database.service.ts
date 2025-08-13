import { Injectable } from '@angular/core';
import { LabelModel } from '../model';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LabelingDatabaseService {
  public plotlyShapes$ = new BehaviorSubject<Partial<Plotly.Shape>[]|undefined>(undefined)
  public plotlyAnnotations$ = new BehaviorSubject<Partial<Plotly.Annotations>[]|undefined>(undefined)
  public selectedButton$ = new BehaviorSubject<string|undefined>(undefined)
  public channelList?: {channelName: string, yaxis: Plotly.YAxisName, color: string}[] = [];

  constructor() { }

  public updateSelectedButton(button: string){
    this.selectedButton$.next(button)
  }

  public updateLabels(labelInfo: LabelModel){
    const plotlyShapeAnnotation = this.labels2PlotlyShapes(labelInfo)
    this.plotlyShapes$.next(plotlyShapeAnnotation.shapes)
    this.plotlyAnnotations$.next(plotlyShapeAnnotation.annotations)
  }

  public labels2PlotlyShapes(labelInfo: LabelModel){
    const plotlyShapes: Partial<Plotly.Shape>[] = []
    for (let event of labelInfo.events) {
      if (event.hide===false){
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
        }
        plotlyShapes.push(rect)
      }
    }
    for (let guide of labelInfo.guidelines) {
      if (guide.hide===false){
        const guideline: Partial<Plotly.Shape> = {
          type: 'line',
          yref: guide.yaxis,
          xref: 'paper',
          x0: this.channelList!.length*0.04-0.03,
          x1: 0.95,
          y0: guide.y,
          y1: guide.y,
          opacity: 0.5,
          line: {
            color: guide.color,
            width: 1,
            dash: 'dash'
          }
        }
        plotlyShapes.push(guideline)
      }
    }
    const plotlyAnnotations: Partial<Plotly.Annotations>[] = []
    for (let event of labelInfo.events) {
      if (event.hide === false){
        const annotationStart : Partial<Plotly.Annotations>={
          showarrow: false,
          yref: 'paper',
          x: event.start,
          xanchor: 'center',
          y: 1,
          yanchor: 'bottom',
          text: 'start',
          bgcolor: '#95a3b8',
          font: {
            color: event.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
          }
        }
        const annotationEnd: Partial<Plotly.Annotations> = {
          showarrow: false,
          yref: 'paper',
          x: event.end,
          xanchor: 'center',
          y: 1,
          yanchor: 'bottom',
          text: 'end',
          bgcolor: '#95a3b8',
          font: {
            color: event.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
          }
        }
        const annotationEvent: Partial<Plotly.Annotations> = {
          showarrow: false,
          yref: 'paper',
          x: new Date(event.start).getTime() + ((new Date(event.end)).getTime() - (new Date(event.start)).getTime()) / 2,
          xanchor: 'center',
          y: 1,
          yanchor: 'bottom',
          text: `${event.className} - ${event.labeler}`,
          bgcolor: '#95a3b8',
          font: {
            color: event.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
          }
        }
        plotlyAnnotations.push(annotationStart, annotationEnd, annotationEvent)
      }
    }
    for (let guide of labelInfo.guidelines) {
      if (guide.hide === false) {
        const guideAnnotation: Partial<Plotly.Annotations>={
          showarrow: false,
          xref: 'paper',
          yref: guide.yaxis,
          x: 1,
          xanchor: 'right',
          y: (guide.y as string|number),
          yanchor: 'middle',
          text: `${guide.channelName} - ${guide.y}`,
          bgcolor: '#95a3b8',
          font: {
            color: guide.color,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
          }
        }
        plotlyAnnotations.push(guideAnnotation)
      }
    }
    return {
      'shapes': plotlyShapes,
      'annotations': plotlyAnnotations
    }
  }
}

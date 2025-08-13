import { Component, ElementRef, Inject, OnDestroy, OnInit, ViewChild, inject, AfterViewInit } from '@angular/core';
import { DatabaseService } from '../database/database.service';
import { FolderModel, ProjectModel, UserModel } from '../model';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Subscription, filter, switchMap, tap } from 'rxjs';
import { ListboxClickEvent } from 'primeng/listbox';
import { Router } from '@angular/router';
import * as Plotly from 'plotly.js-dist-min'

@Component({
  selector: 'app-profile-page',
  templateUrl: './profile-page.component.html',
  styleUrl: './profile-page.component.scss'
})
export class ProfilePageComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('chart') plotlyChart!: ElementRef

  private http = inject(HttpClient)
  public databaseService = inject(DatabaseService)
  private router = inject(Router)
  private subscriptions = new Subscription()

  public userInfo?: UserModel
  public name?: string
  public folderList?: FolderModel[]
  // public assistantList?: UserModel["assistantList"]
  public projectList?: ProjectModel[]
  public newProjectDialogVisible: boolean = false;
  public newProjectName?: string;
  public imgSrc?: string;

  constructor(){}

  ngOnInit(): void {
    this.databaseService.updatePageLabel('Profile')
    this.databaseService.updatePageTitle('HILL - Human in the loop labeling tool - For sequence data')
    this.subscriptions.add(
      this.databaseService.userInfo$.pipe(
        filter(x=>x!==undefined),
      ).subscribe(user=>{
        this.userInfo = user
        this.imgSrc = `assets/img/${this.userInfo!.badge}.png`
        const history = this.userInfo!.contributionHistory
        // if (history!==undefined&&history.length!==0){
          const trace:Plotly.Data[] = [
            {
              x: history.map(h=>h.time),
              y: history.map(h=>h.nbEventsLabeled),
              type: 'bar',
              text: history.map(h=>h.nbEventsLabeled).map(String),
              hoverinfo: 'none'
            }
          ]
          const layout: Partial<Plotly.Layout> = {
            showlegend: false,
            hovermode: false,
            dragmode: false,
            paper_bgcolor: '#c7ced9',
            plot_bgcolor: '#e0e4ea',
            autosize: true,
            margin: {
              t:20,
              r: 5,
              b: 20,
              l: 40
            },
            xaxis: {
              showgrid: false,
              color: '#222',
              tickfont:{
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI",bRoboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"',
                size: 16,
                color:'#444e5c'
              },
            },
          }
          const config: Partial<Plotly.Config> = {
            responsive: true,
            scrollZoom: false,
            displaylogo: false,
          } 
          Plotly.newPlot(this.plotlyChart.nativeElement, trace, layout, config)
        // }
      })
    )
    this.subscriptions.add(
      this.databaseService.folderList$.pipe(
        filter(folders=> folders!==undefined)
      ).subscribe(folders=>{
        this.folderList = folders
      })
    )
    this.subscriptions.add(
      this.databaseService.projectList$.pipe(
        filter(x=>x!==undefined)
      ).subscribe(data=>{
        this.projectList = data!
      })
    )
    
  }

  ngAfterViewInit(): void {
    
  }

  onClickRecentFile($event: Event, file: UserModel['recent'][0]) {
    this.router.navigate(['/labeling', {folderId: file.folder, fileId: file.file}])
  }

  onClickMessage($event: Event, message: UserModel['message'][0]) {
    if (message.file!==undefined){
      this.router.navigate(['/labeling', {folderId: message.folder, fileId: message.file}])
    }
    else{
      this.router.navigate(['/files', {folderId: message.folder}])
    }
    
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe()
  }
}

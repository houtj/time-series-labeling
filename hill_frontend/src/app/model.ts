export interface UserProfile{
    displayName?: string;
    givenName?: string,
    surname?: string,
    userPrincipalName?: string,
    id?: string,
    mail?: string,
}

export interface UserModel {
    _id?: {$oid: string}
    name: string;
    activeSince: {$date: string};
    folderList: string[],
    projectList: string[],
    contributionHistory: {
        time: string,
        nbEventsLabeled: number
    }[],
    recent: {
        folder: string,
        file: string,
        displayText: string,
    }[],
    message: {
        folder: string,
        file: string,
        project: string,
        displayText: string
    }[],
    badge: string,
    mail: string,
    rank: number
}

export interface FolderModel{
    _id?: {$oid: string},
    name: string,
    project: {
        id: string,
        name: string
    },
    template: {
        id: string,
        name: string
    }
    nbLabeledFiles: number,
    nbTotalFiles: number,
    fileList: string[]
}

export interface FileModel{
    _id?: {$oid: string},
    name: string,
    parsing: string,
    nbEvent: string,
    description: string,
    rawPath: string,
    jsonPath: string,
    label: string,
    lastUpdate: {$date: string}
    lastModifier: string,
    inputVisible? :boolean
}

export interface AssistantModel {
    _id?: {$oid: string},
    name: string,
    version: number,
    accuracy: number, 
    projectName: string
}

export interface TemplateModel {
    _id?: {$oid: string},
    fileType: string,
    templateName: string,
    sheetName: string,
    headRow: number,
    skipRow: number,
    x: {
        name: string,
        regex: string,
        isTime: boolean,
        unit: string,
    },
    channels: {
        channelName: string,
        color: string,
        regex: string,
        mandatory: boolean,
        unit: string,
    }[]
}

export interface ProjectModel {
    _id?: {$oid: string}
    projectName: string,
    templates: {
        id: string,
        name: string,
        fileType: string,
    }[],
    classes: {
        name: string,
        color: string,
        description: string,
    }[]
    general_pattern_description: string,
}

export interface LabelModel {
    _id?: {$oid: string},
    events: {
        className: string,
        color: string,
        description: string,
        labeler: string,
        start: string|number,
        end: string|number,
        hide: boolean,
    }[]
    guidelines: {
        yaxis: Plotly.YAxisName|'paper',
        y: Plotly.Datum,
        channelName: string,
        color: string, 
        hide: boolean
    }[]
}

export interface DataModel {
    x: boolean,
    name: string,
    unit: string,
    color: string,
    data: string[]|number[]
}

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system',
    content: string,
    timestamp: string
}

export interface ChatConversation {
    _id?: {$oid: string},
    fileId: string,
    messages: ChatMessage[],
    createdAt?: string,
    updatedAt?: string
}

export interface AutoDetectionMessage {
    type: 'status' | 'progress' | 'result' | 'error',
    status: string,  // started, planning, identifying, validating, completed, failed
    message: string,
    timestamp: string,
    eventsDetected?: number,
    summary?: string,
    error?: string
}

export interface AutoDetectionConversation {
    _id?: {$oid: string},
    fileId: string,
    messages: AutoDetectionMessage[],
    status: 'idle' | 'started' | 'running' | 'completed' | 'failed',
    createdAt?: string,
    updatedAt?: string
}
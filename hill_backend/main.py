import time
import os
from fastapi import FastAPI, WebSocket, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pymongo
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from model import CloneTemplateModel, DownloadJsonFiles, NewClassModel, NewFolderModel, NewProjectModel, NewTemplateModel, ReparsingFiles, UpdateClassRequest, UpdateDescriptionModel, UpdateLabelModel, UpdateProjectDescriptionsModel, UpdateTemplateModel, UpdateUserRecentFilesModel, UpdateUserShareProjectModel, UpdateUserSharedFolderModel, ChatMessage, ConversationModel
from datetime import datetime, timezone
import simplejson as json
from typing import Annotated
from pathlib import Path
import shutil
import pandas as pd
import tempfile
from dotenv import load_dotenv

# Import from our new modules
from database import init_database, get_db, get_data_folder_path, get_conversation, clear_conversation
from websocket_handlers import handle_chat_websocket

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Increase file upload size limit to 100MB
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Set maximum file size to 100MB
        request.scope["max_content_size"] = 100 * 1024 * 1024  # 100MB
        response = await call_next(request)
        return response

app.add_middleware(LargeFileMiddleware)

# Initialize database connection
db = init_database()
data_folder_path = get_data_folder_path()


@app.post("/jsonfiles")
async def donwload_files(request: DownloadJsonFiles):
    project_id = request.projectId
    passwd = request.passwd
    if passwd != 'NPeGBxS4hmP8NJh4H4C0BDuQnR6B4pT2ySEHmiNVi0WDbeTJfHdiuT0BNtuyyMUN1cDenSkk9M2tKVJ0rSaxY8zo8OcGPg5o':
        return {'error': 'incorrect password'}
    data_folder_path = Path(data_folder_path)
    file_ids = [f.name for f in (data_folder_path/project_id).iterdir()]
    json_response = {}
    for file_id in file_ids:
        file_db = db['files'].find_one({'_id': ObjectId(file_id)})
        if file_db is not None and 'jsonPath' in file_db:
            filename = file_db['name']
            json_path = file_db['jsonPath']
            with open(data_folder_path/json_path) as f:
                data = json.load(f)
        else:
            data = 'none'
        if 'label' in file_db:
            label = db['labels'].find_one({'_id': ObjectId(file_db['label'])})
            if label is not None:
                label = json.loads(dumps(label))
            else:
                label = 'none'
        else:
            label = 'none'
        json_response[file_id] = {'name': filename, 'data': data, 'label': dumps(label)}
    return json_response

@app.get("/")
async def welcome():
    return {'hello':'world'}

@app.get("/userInfo")
async def get_userInfo():
    userInfo = db['users'].find_one({'mail': 'default@default.com'})
    if userInfo is None:
        userInfo = {
            'name': 'default',
            'mail': 'default@default.com',
            'activeSince': datetime.now(tz=timezone.utc),
            'projectList': [],
            'folderList':[],
            'assistantList':[],
            'contributionHistory': [],
            'recent': [],
            'message': [],
            'badge': 'Iron',
            'rank': 100            
        }
        result = db['users'].insert_one(userInfo)
        new_user_id = result.inserted_id
        userInfo['_id'] = new_user_id
    userInfo = dumps(userInfo)
    print(userInfo)
    return userInfo

@app.post("/projects")
async def add_project(project: NewProjectModel):
    new_project = {
        'projectName': project.projectName,
        'templates': [],
        'classes': [],
        'general_pattern_description': '',
    }
    result = db['projects'].insert_one(new_project)
    new_project_id = result.inserted_id
    new_project['_id'] = new_project_id
    print(project.userId)
    print(db['users'].find_one({'_id': ObjectId(project.userId)}))
    result = db['users'].update_one({'_id': ObjectId(project.userId)}, {'$push':{'projectList': str(new_project_id)}})
    return dumps(new_project)

@app.get("/projects")
async def get_all_projects(projects: str):
    projects = json.loads(projects)
    result = db['projects'].find({'_id': {'$in': [ObjectId(f) for f in projects]}})
    return dumps(result)

@app.post("/templates")
async def add_template(request: NewTemplateModel):
    projectId = ObjectId(request.projectId)
    newTemplateName = request.templateName
    fileType = request.fileType

    # add new template
    new_template = {
        'templateName': newTemplateName,
        'fileType': fileType,
        'channels': [],
        'x':{}
    }
    result = db['templates'].insert_one(new_template)
    new_template_id = result.inserted_id
    new_template['_id'] = new_template_id

    # add new template to project
    result = db['projects'].update_one({'_id': projectId}, {'$push': {'templates': {'id': str(new_template_id), 'name': newTemplateName, 'fileType': fileType}}})
    print(result)
    return str(new_template_id)

@app.get('/templates/{template_id}')
async def get_templates(template_id):
    templateInfo = db['templates'].find_one({'_id': ObjectId(template_id)})
    return dumps(templateInfo)

@app.post('/extract-columns')
async def extract_columns(file: UploadFile, templateId: Annotated[str, Form()]):
    try:
        # Get template information
        template = db['templates'].find_one({'_id': ObjectId(templateId)})
        if not template:
            return {'error': 'Template not found'}
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Read file based on file type
            file_type = template.get('fileType', '.xlsx')
            
            if file_type == '.xlsx':
                sheet_name = template.get('sheetName', 0)
                try:
                    sheet_name = int(sheet_name)
                except:
                    pass
                df = pd.read_excel(tmp_file_path, sheet_name=sheet_name, engine='openpyxl', 
                                 header=template.get('headRow', 0))
            elif file_type == '.xls':
                sheet_name = template.get('sheetName', 0)
                try:
                    sheet_name = int(sheet_name)
                except:
                    pass
                df = pd.read_excel(tmp_file_path, sheet_name=sheet_name, engine='xlrd', 
                                 header=template.get('headRow', 0))
            elif file_type == '.csv':
                df = pd.read_csv(tmp_file_path, header=template.get('headRow', 0))
            else:
                return {'error': 'Unsupported file type'}
            
            # Extract column information
            columns = []
            for i, column_name in enumerate(df.columns):
                # Get first non-null value as sample data
                sample_data = ""
                for value in df[column_name].dropna():
                    if pd.notna(value):
                        sample_data = str(value)
                        break
                
                columns.append({
                    'name': str(column_name),
                    'index': i,
                    'sampleData': sample_data
                })
            
            return {'columns': columns}
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        return {'error': f'Failed to process file: {str(e)}'}

@app.put('/templates_clone')
async def clone_template(request: CloneTemplateModel):
    result = db['templates'].find_one({'_id': ObjectId(request.templateId)})
    fileType=result['fileType']
    result['templateName'] = request.newTemplateName
    del result['_id']
    result = db['templates'].insert_one(result)
    
    new_template_id = result.inserted_id
    result = db['projects'].update_one({'_id': ObjectId(request.projectId)}, {'$push': {'templates': {'id': str(new_template_id), 'name': request.newTemplateName, 'fileType': fileType}}})
    return str(new_template_id)

@app.put('/templates')
async def update_template(request: UpdateTemplateModel):
    template = request.request
    project_id = request.projectId
    template_id = ObjectId(template['_id']['$oid'])
    del template['_id']
    template['headRow'] = int(template['headRow'])
    template['skipRow'] = int(template['skipRow'])
    result = db['templates'].update_one({'_id': template_id}, {'$set':template})
    result = db['projects'].update_one({
                                            '_id': ObjectId(project_id)
                                        }, 
                                        {
                                            '$set': 
                                                {'templates.$[elem].fileType': template['fileType']},
                                        }, 
                                        array_filters=[{'elem.id': str(template_id)}]
                                        )
    return 'done'

@app.post("/classes")
async def add_new_class(class_: NewClassModel):
    result = db['projects'].update_one({'_id': ObjectId(class_.projectId)}, {'$push': {'classes':{'name': class_.newClassName, 'color': class_.newClassColor, 'description': class_.description}}})
    return 'done'

@app.put("/classes")
async def update_class(newClass: UpdateClassRequest):
    result = db['projects'].update_one({'_id': ObjectId(newClass.projectId), 'classes.name': newClass.updatingClassName}, {'$set': {'classes.$':{'name':newClass.newClassName, 'color': newClass.newClassColor, 'description': newClass.description}}})
    return 'done'

@app.post("/folders")
async def add_new_folder(folder: NewFolderModel):
    print(folder)
    ## add new folder
    newFolder = {
        'name': folder.newFolderName,
        'project': {
            'id': folder.project['id'],
            'name': folder.project['name'],
        },
        'template': {
            'id': folder.template['id'],
            'name': folder.template['name']
        },
        'fileList': [],
        'nbLabeledFiles':0,
        'nbTotalFiles': 0,
    }
    result = db['folders'].insert_one(newFolder)
    newFolderId = result.inserted_id
    newFolder['_id'] = newFolderId

    ## update user
    result = db['users'].update_one({'_id': ObjectId(folder.userId)}, {'$push':{'folderList': str(newFolderId)}})
    return 'done'

@app.get("/users")
async def get_users():
    usersList = dumps(list(db['users'].find({})))
    return usersList

@app.put('/usersSharedFolders')
async def update_user_folder(request: UpdateUserSharedFolderModel):
    folder = request.folder
    user = request.user
    userName = request.userName
    message = request.message
    print(folder)
    user_folder = user['folderList']
    if folder['_id']['$oid'] not in user_folder:
        result = db['users'].update_one({'_id': ObjectId(user['_id']['$oid'])}, {'$push': {
            'folderList':folder['_id']['$oid'], 
            'message': {
                'folder': folder['_id']['$oid'],
                'displayText': f'From {userName}: Folder {folder["name"]} is shared to you. {message}'
            }
        }})
    project_id = folder['project']['id']
    if project_id not in user['projectList']:
        result = db['users'].update_one({'_id': ObjectId(user['_id']['$oid'])}, {'$push':{
            'projectList': project_id,
        }})
    return 'done'

### Same with usersSharedFolder, to be updated
@app.put('/usersSharedFiles')
async def update_user_file(request: UpdateUserSharedFolderModel):
    folder = request.folder
    user = request.user
    userName = request.userName
    message = request.message
    user_folder = user['folderList']
    if folder['_id']['$oid'] not in user_folder:
        result = db['users'].update_one({'_id': ObjectId(user['_id']['$oid'])}, {'$push': {
            'folderList':folder['_id']['$oid'], 
            'message': {
                'folder': folder['_id']['$oid'],
                'displayText': f'From {userName}: Folder {folder["name"]} is shared to you. {message}'
            }
        }})
    project_id = folder['project']['id']
    if project_id not in user['projectList']:
        result = db['users'].update_one({'_id': ObjectId(user['_id']['$oid'])}, {'$push':{
            'projectList': project_id,
        }})

    return 'done'

@app.put('/usersSharedProjects')
async def update_user_project(request: UpdateUserShareProjectModel):
    project = request.project
    user = request.user
    userName = request.userName
    message = request.message
    user_project = user['projectList']
    if project['_id']['$oid'] not in user_project:
        resut = db['users'].update_one({'_id': ObjectId(user['_id']['$oid'])}, {'$push': {
            'projectList':project['_id']['$oid'], 
            'message': {
                'project': project['_id']['$oid'],
                'displayText': f'From {userName}: Project {project["projectName"]} is shared to you. {message}'
            }
        }})
    return 'done'

@app.put('/userRecentFiles')
async def update_user(request: UpdateUserRecentFilesModel):
    result = db['users'].find_one({'_id': ObjectId(request.userInfo['_id']['$oid'])})
    recent_files = result['recent']
    if request.folderId in [r['folder'] for r in recent_files] and request.fileId in [r['file'] for r in recent_files]:
        return 'done'
    else:
        recent_files.append({'folder': request.folderId, 'file': request.fileId, 'displayText': request.folderName + ' - ' + request.fileName})
        recent_files = recent_files[-5:]
        result = db['users'].update_one({'_id': ObjectId(request.userInfo['_id']['$oid'])}, {'$set': {'recent': recent_files}})
        return 'done'

@app.delete('/folders')
async def delete_folder(folder: str):
    folder = json.loads(folder)
    files_id = folder['fileList']
    folder_id = folder['_id']['$oid']
    files = db['labels'].find({'_id': {'$in': [ObjectId(f) for f in files_id]}})
    labels = [file['label'] for file in files]
    result = db['lables'].delete_many({'_id':{'$in': [ObjectId(l) for l in labels]}})
    result = db['files'].delete_many({'_id': {'$in': [ObjectId(f) for f in files_id]}})
    result = db['users'].update_many({'folderList': folder['_id']['$oid']}, {'$pull': {'folderList': folder['_id']['$oid']}})
    result = db['folders'].delete_one({'_id': ObjectId(folder['_id']['$oid'])})
    shutil.rmtree(Path(data_folder_path)/folder_id, ignore_error=True)
    return 'done'

@app.get('/folders')
async def get_folders(folders: str):
    print(folders)
    folders = json.loads(folders)
    result = db['folders'].find({'_id': {'$in': [ObjectId(f) for f in folders]}})
    return dumps(result)

@app.get('/folders/{folder_id}')
async def get_folder(folder_id: str):
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    return dumps(result)

@app.get('/files')
async def get_files(filesId: str):
    filesId = json.loads(filesId)
    result = db['files'].find({'_id': {'$in': [ObjectId(f) for f in filesId]}})
    return dumps(result)

@app.delete('/files')
async def remove_file(file: str):
    file = json.loads(file)
    label_id = file['label']
    result = db['labels'].delete_one({'_id': ObjectId(label_id)})
    if file['nbEvent'] == 'unlabeled':
        update_dict = {'$pull':{'fileList': file['_id']['$oid']}, '$inc':{'nbTotalFiles': -1}}
    else:
        update_dict = {'$pull':{'fileList': file['_id']['$oid']}, '$inc':{'nbTotalFiles': -1, 'nbLabeledFiles': -1}}
    result = db['folders'].find_one({'fileList': file['_id']['$oid']})
    folder_id = str(result['_id'])
    result = db['folders'].update_many({'fileList': file['_id']['$oid']}, update_dict)
    result = db['files'].delete_one({'_id': ObjectId(file['_id']['$oid'])})
    shutil.rmtree(Path(data_folder_path)/folder_id/file['_id']['$oid'])
    return 'done'

@app.post('/event')
async def add_event(data: Annotated[str, Form()], user:Annotated[str, Form()], file: UploadFile):
    event_info = file.file.read()
    event_info = json.loads(event_info)
    label_id = data
    user_name = user
    result = db['labels'].update_one({'_id':ObjectId(label_id)}, {'$set': {'events': event_info}})

    file = db['files'].find_one({'label': label_id})
    previous_nbEvents = file['nbEvent']
    new_nbEvents = ''
    if len(event_info)==0:
        new_nbEvents = '0'
    else:
        labelers = list(set([e['labeler'] for e in event_info]))
        for labeler in labelers:
            events_labeler = [e for e in event_info if e['labeler']==labeler]
            new_nbEvents += f'{len(events_labeler)} by {labeler};'
        new_nbEvents = new_nbEvents.rstrip(';')
    result = db['files'].update_one({'label': label_id}, {'$set': {'nbEvent': new_nbEvents, 
                                                                   'lastModifier': user_name, 
                                                                   'lastUpdate':datetime.now(tz=timezone.utc)}})
    if previous_nbEvents == 'unlabeled':
        result = db['folders'].update_one({'fileList': str(file['_id'])}, {'$inc': {'nbLabeledFiles': 1}})
    return 'done'

@app.post('/events')
async def add_event(data: Annotated[str, Form()], user: Annotated[str, Form()], file: UploadFile):
    event_info_list = file.file.read()
    event_info_list = json.loads(event_info_list)
    folder_id = data
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_list = result['fileList']
    result = db['files'].find({'_id': {'$in': [ObjectId(id) for id in files_list]}})
    file_name_dict = {}
    for file in result:
        file_name_dict[file['name']] = file['label']

    for event in event_info_list:
        if event['file_name'] in file_name_dict:
            label_id = file_name_dict[event['file_name']]
            result = db['labels'].update_one({'_id':ObjectId(label_id)}, {'$set': {'events': event['events']}})

            file = db['files'].find_one({'label': label_id})
            previous_nbEvents = file['nbEvent']
            new_nbEvents = ''
            if len(event['events'])==0:
                new_nbEvents = '0'
            else:
                labelers = list(set([e['labeler'] for e in event['events']]))
                for labeler in labelers:
                    events_labeler = [e for e in event['events'] if e['labeler']==labeler]
                    new_nbEvents += f'{len(events_labeler)} by {labeler};'
                new_nbEvents = new_nbEvents.rstrip(';')
            result = db['files'].update_one({'label': label_id}, {'$set': {'nbEvent': new_nbEvents, 
                                                                           'lastModifier': user, 
                                                                           'lastUpdate': datetime.now(tz=timezone.utc)}})
            if previous_nbEvents == 'unlabeled':
                result = db['folders'].update_one({'fileList': str(file['_id'])}, {'$inc': {'nbLabeledFiles': 1}})
    return 'done'

@app.post('/files')
async def add_files(data: Annotated[str, Form()], user: Annotated[str, Form()], files: list[UploadFile]):
    folderId = data
    userName = user
    for file in files:
        ## add new label
        labelInfo = {
            'events': [],
            'guidelines': [],
        }
        result = db['labels'].insert_one(labelInfo)
        ## add new file
        newLabelId = result.inserted_id
        fileInfo = {
            'name': file.filename,
            'parsing': 'uploading',
            'nbEvent': 'unlabeled',
            'description': '',
            'rawPath': '',
            'jsonPath': '',
            'lastModifier': userName,
            'lastUpdate': datetime.now(tz=timezone.utc),
            'label': str(newLabelId),
        }
        result = db['files'].insert_one(fileInfo)
        newFileId = result.inserted_id
        ## save file with fileID
        Path(f'{data_folder_path}/{folderId}/{str(newFileId)}').mkdir(exist_ok=True, parents=True)
        with open(f'{data_folder_path}/{folderId}/{str(newFileId)}/{file.filename}', 'wb') as f:
            content = file.file.read()
            f.write(content)
        ## update file 
        fileInfo['rawPath'] = f'{folderId}/{str(newFileId)}/{file.filename}'
        fileInfo['parsing'] = 'parsing start'
        result = db['files'].update_one({'_id': newFileId}, {'$set': fileInfo})
        result = db['folders'].update_one({'_id': ObjectId(folderId)}, {'$push': {'fileList': str(newFileId)}, '$inc':{'nbTotalFiles': 1}})
    return 'done'

@app.get('/files/{file_id}')
async def get_file(file_id: str):
    result = db['files'].find_one({'_id': ObjectId(file_id)})
    json_path = result['jsonPath']
    file_path = f'{data_folder_path}/{json_path}'
    with open(file_path, 'r') as f:
        json_string = f.read()
    response = {'fileInfo': dumps(result), 'data': json_string}
    return json.dumps(response)

@app.get('/labels/{label_id}')
async def get_label(label_id: str):
    result = db['labels'].find_one({'_id': ObjectId(label_id)})
    return dumps(result)

@app.put('/labels')
async def update_label(request: UpdateLabelModel):
    label_info = request.label
    label_id = label_info['_id']['$oid']
    del label_info['_id']
    result = db['labels'].update_one({'_id': ObjectId(label_id)},  {'$set':label_info})
    file = db['files'].find_one({'label': label_id})
    previous_nbEvents = file['nbEvent']
    new_nbEvents = ''
    events = label_info['events']
    if len(events)==0:
        new_nbEvents = '0'
    else:
        labelers = list(set([e['labeler'] for e in events]))
        for labeler in labelers:
            events_labeler = [e for e in events if e['labeler']==labeler]
            new_nbEvents += f'{len(events_labeler)} by {labeler};'
        new_nbEvents = new_nbEvents.rstrip(';')
    result = db['files'].update_one({'label': label_id}, {'$set': {'nbEvent': new_nbEvents, 
                                                                   'lastModifier': request.user, 
                                                                   'lastUpdate': datetime.now(tz=timezone.utc)}})
    if previous_nbEvents == 'unlabeled':
        result = db['folders'].update_one({'fileList': str(file['_id'])}, {'$inc': {'nbLabeledFiles': 1}})
        
    return 'done'

@app.get('/files_data/{folder_id}')
async def get_files_data(folder_id: str):
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_id = result['fileList']
    result = db['files'].find({'_id': {'$in': [ObjectId(id) for id in files_id]}})
    json_path = []
    file_names = []
    for file in result:
        if file['parsing'] == 'parsed':
            json_path.append(file['jsonPath'])
            file_names.append(file['name'])
    response = []
    for idx, path in enumerate(json_path):
        local_json_path = f'{data_folder_path}/{path}'
        with open(local_json_path, 'r') as f:
            data = json.load(f)
        response.append({'file_name': file_names[idx], 'data': data})
    return dumps(response)

@app.get('/files_event/{folder_id}')
async def get_files_event(folder_id):
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_id = result['fileList']
    result = db['files'].find({'_id': {'$in': [ObjectId(id) for id in files_id]}})
    labels_id = []
    file_names = []
    for file in result:
        if file['parsing'] == 'parsed':
            labels_id.append(file['label'])
            file_names.append(file['name'])
    result = db['labels'].find({'_id': {'$in': [ObjectId(id) for id in labels_id]}})
    response = []
    for idx, label in enumerate(result):
        response.append({'file_name': file_names[idx], 'events': label['events']})
    return dumps(response)

@app.put('/descriptions')
async def update_descriptions(request:UpdateDescriptionModel):
    file_id = request.file_id
    description = request.description
    result = db['files'].update_one({'_id': ObjectId(file_id)}, {'$set': {'description': description}})
    return 'done'

@app.put('/reparsingFiles')
async def reparsing_files(request:ReparsingFiles):
    folder_id = request.folderId
    result = db['folders'].find_one({'_id': ObjectId(folder_id)})
    files_id = result['fileList']
    result = db['files'].update_many({'_id': {'$in':[ObjectId(id) for id in files_id]}}, {'$set':{'parsing': 'parsing start'}})
    return 'done'

@app.put('/project-descriptions')
async def update_project_descriptions(request: UpdateProjectDescriptionsModel):
    project_id = ObjectId(request.projectId)
    
    # Update general description
    result = db['projects'].update_one(
        {'_id': project_id}, 
        {'$set': {'general_pattern_description': request.generalDescription}}
    )
    
    # Update class descriptions
    for class_desc in request.classDescriptions:
        result = db['projects'].update_one(
            {
                '_id': project_id,
                'classes.name': class_desc['name']
            }, 
            {
                '$set': {
                    'classes.$.description': class_desc['description']
                }
            }
        )
    
    return 'done'

# Conversation endpoints
@app.get('/conversations/{file_id}')
async def get_conversation_endpoint(file_id: str):
    """Get conversation history for a file"""
    return get_conversation(file_id)

@app.delete('/conversations/{file_id}')
async def clear_conversation_endpoint(file_id: str):
    """Clear conversation history for a file"""
    return clear_conversation(file_id)

@app.websocket("/ws/chat/{file_id}")
async def websocket_chat_endpoint(websocket: WebSocket, file_id: str):
    """WebSocket endpoint for chat functionality"""
    await handle_chat_websocket(websocket, file_id)

if __name__=='__main__':
    import uvicorn
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
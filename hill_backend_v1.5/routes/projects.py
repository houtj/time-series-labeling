"""Project Routes"""
from fastapi import APIRouter
from bson.objectid import ObjectId
from bson.json_util import dumps
import simplejson as json

from database import get_db
from models import NewProjectRequest, UpdateProjectDescriptionsRequest

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("")
async def create_project(project: NewProjectRequest):
    """Create a new project"""
    db = get_db()
    new_project = {
        'projectName': project.projectName,
        'templates': [],
        'classes': [],
        'general_pattern_description': '',
    }
    result = db['projects'].insert_one(new_project)
    new_project['_id'] = result.inserted_id
    
    # Add project to user's list
    db['users'].update_one(
        {'_id': ObjectId(project.userId)}, 
        {'$push': {'projectList': str(result.inserted_id)}}
    )
    
    return dumps(new_project)


@router.get("")
async def get_projects(projects: str):
    """Get multiple projects"""
    db = get_db()
    projects = json.loads(projects)
    result = db['projects'].find({'_id': {'$in': [ObjectId(f) for f in projects]}})
    return dumps(result)


@router.put("/descriptions")
async def update_project_descriptions(request: UpdateProjectDescriptionsRequest):
    """Update project descriptions"""
    db = get_db()
    project_id = ObjectId(request.projectId)
    
    # Update general description
    db['projects'].update_one(
        {'_id': project_id}, 
        {'$set': {'general_pattern_description': request.generalDescription}}
    )
    
    # Update class descriptions
    for class_desc in request.classDescriptions:
        db['projects'].update_one(
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


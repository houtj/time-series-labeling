"""Template Routes"""
from fastapi import APIRouter, UploadFile, Form
from typing import Annotated
from bson.objectid import ObjectId
from bson.json_util import dumps
import tempfile
import pandas as pd
import os

from database import get_db
from models import NewTemplateRequest, UpdateTemplateRequest, CloneTemplateRequest

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("")
async def create_template(request: NewTemplateRequest):
    """Create new template"""
    db = get_db()
    projectId = ObjectId(request.projectId)
    
    # Add new template
    new_template = {
        'templateName': request.templateName,
        'fileType': request.fileType,
        'channels': [],
        'x': {},
        'headRow': 0,
        'skipRow': 0,
        'sheetName': 0
    }
    result = db['templates'].insert_one(new_template)
    new_template_id = result.inserted_id
    new_template['_id'] = new_template_id
    
    # Add template to project
    db['projects'].update_one(
        {'_id': projectId}, 
        {'$push': {'templates': {
            'id': str(new_template_id), 
            'name': request.templateName, 
            'fileType': request.fileType
        }}}
    )
    
    return str(new_template_id)


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get template by ID"""
    db = get_db()
    templateInfo = db['templates'].find_one({'_id': ObjectId(template_id)})
    return dumps(templateInfo)


@router.put("")
async def update_template(request: UpdateTemplateRequest):
    """Update template"""
    db = get_db()
    template = request.request
    project_id = request.projectId
    template_id = ObjectId(template['_id']['$oid'])
    
    del template['_id']
    template['headRow'] = int(template['headRow'])
    template['skipRow'] = int(template['skipRow'])
    
    db['templates'].update_one({'_id': template_id}, {'$set': template})
    db['projects'].update_one(
        {'_id': ObjectId(project_id)}, 
        {'$set': {'templates.$[elem].fileType': template['fileType']}}, 
        array_filters=[{'elem.id': str(template_id)}]
    )
    
    return 'done'


@router.put("/clone")
async def clone_template(request: CloneTemplateRequest):
    """Clone existing template"""
    db = get_db()
    result = db['templates'].find_one({'_id': ObjectId(request.templateId)})
    fileType = result['fileType']
    result['templateName'] = request.newTemplateName
    del result['_id']
    
    result = db['templates'].insert_one(result)
    new_template_id = result.inserted_id
    
    db['projects'].update_one(
        {'_id': ObjectId(request.projectId)}, 
        {'$push': {'templates': {
            'id': str(new_template_id), 
            'name': request.newTemplateName, 
            'fileType': fileType
        }}}
    )
    
    return str(new_template_id)


@router.post("/extract-columns")
async def extract_columns(file: UploadFile, templateId: Annotated[str, Form()]):
    """Extract columns from uploaded file"""
    db = get_db()
    try:
        # Get template information
        template = db['templates'].find_one({'_id': ObjectId(templateId)})
        if not template:
            return {'error': 'Template not found'}
        
        # Create temporary file
        file_ext = os.path.splitext(file.filename)[1] if file.filename else template.get('fileType', '.csv')
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
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
                df = pd.read_excel(
                    tmp_file_path, 
                    sheet_name=sheet_name, 
                    engine='openpyxl', 
                    header=template.get('headRow', 0)
                )
            elif file_type == '.xls':
                sheet_name = template.get('sheetName', 0)
                try:
                    sheet_name = int(sheet_name)
                except:
                    pass
                df = pd.read_excel(
                    tmp_file_path, 
                    sheet_name=sheet_name, 
                    engine='xlrd', 
                    header=template.get('headRow', 0)
                )
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


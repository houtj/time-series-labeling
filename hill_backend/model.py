from pydantic import BaseModel

class NewProjectModel(BaseModel):
    projectName: str
    userId: str

class NewTemplateModel(BaseModel):
    templateName: str
    projectId: str
    fileType: str

class UpdateTemplateModel(BaseModel):
    request: dict
    projectId: str

class CloneTemplateModel(BaseModel):
    newTemplateName: str
    projectId: str
    templateId: str

class NewClassModel(BaseModel):
    newClassName: str
    projectId: str
    newClassColor: str

class NewFolderModel(BaseModel):
    newFolderName: str
    project: dict
    template: dict
    userId: str

class UpdateUserSharedFolderModel(BaseModel):
    folder: dict
    user: dict
    userName: str
    message: str

class UpdateUserShareProjectModel(BaseModel):
    project: dict
    user: dict
    userName: str
    message: str

class UpdateLabelModel(BaseModel):
    label: dict
    user: str

class UpdateUserRecentFilesModel(BaseModel):
    folderId: str
    fileId: str
    fileName: str
    folderName: str
    userInfo: dict

class UpdateDescriptionModel(BaseModel):
    file_id: str
    description: str

class UpdateClassRequest(BaseModel):
    updatingClassName: str
    newClassName: str
    newClassColor: str
    projectId: str

class DownloadJsonFiles(BaseModel):
    projectId: str
    passwd: str

class ReparsingFiles(BaseModel):
    folderId: str
"""Label-related API routes"""

import logging

from bson.json_util import dumps
from fastapi import APIRouter

from app.api.dependencies import LabelServiceDep
from app.models.schemas import LabelUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("/{label_id}")
async def get_label(label_id: str, service: LabelServiceDep):
    """Get label by ID"""
    label = service.get_label(label_id)
    return dumps(label)


@router.put("")
async def update_label(request: LabelUpdate, service: LabelServiceDep):
    """Update a label"""
    label_data = request.label.copy()
    # Extract label ID from the nested structure
    if "_id" in label_data and "$oid" in label_data["_id"]:
        label_id = label_data["_id"]["$oid"]
        del label_data["_id"]
    else:
        label_id = str(label_data.get("_id", ""))
        if "_id" in label_data:
            del label_data["_id"]

    service.update_label(label_id, label_data, request.user)
    return "done"


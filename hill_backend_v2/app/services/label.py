"""Label service - Business logic for label/event operations"""

import logging
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundException
from app.repositories.file import FileRepository
from app.repositories.folder import FolderRepository
from app.repositories.label import LabelRepository

logger = logging.getLogger(__name__)


class LabelService:
    """Service for label-related business logic"""

    def __init__(
        self, label_repo: LabelRepository, file_repo: FileRepository, folder_repo: FolderRepository
    ):
        self.label_repo = label_repo
        self.file_repo = file_repo
        self.folder_repo = folder_repo

    def get_label(self, label_id: str) -> dict[str, Any]:
        """
        Get label by ID
        
        Args:
            label_id: Label ID
            
        Returns:
            Label data
            
        Raises:
            NotFoundException: If label not found
        """
        label = self.label_repo.find_by_id(label_id)
        if not label:
            raise NotFoundException("Label", label_id)
        return label

    def update_label(self, label_id: str, label_data: dict, user_name: str) -> dict[str, Any]:
        """
        Update a label and its associated file
        
        Args:
            label_id: Label ID
            label_data: Updated label data
            user_name: Name of the user making the update
            
        Returns:
            Update result information
            
        Raises:
            NotFoundException: If label or file not found
        """
        # Update label
        label = self.label_repo.find_by_id(label_id)
        if not label:
            raise NotFoundException("Label", label_id)

        self.label_repo.update_by_id(label_id, label_data)

        # Update associated file
        file = self.file_repo.find_by_label_id(label_id)
        if not file:
            raise NotFoundException("File", f"with label {label_id}")

        previous_nb_events = file.get("nbEvent", "unlabeled")
        events = label_data.get("events", [])
        new_nb_events = self._calculate_event_count(events)

        self.file_repo.update_by_id(
            str(file["_id"]),
            {
                "nbEvent": new_nb_events,
                "lastModifier": user_name,
                "lastUpdate": datetime.now(tz=timezone.utc),
            },
        )

        # Update folder if first label
        if previous_nb_events == "unlabeled" and new_nb_events != "0":
            folder = self.folder_repo.find_by_file_id(str(file["_id"]))
            if folder:
                self.folder_repo.increment_labeled_files(str(folder["_id"]))

        logger.info(f"Updated label {label_id}")
        return {"success": True, "events_count": len(events), "new_nb_events": new_nb_events}

    def add_events_to_label(
        self, label_id: str, events: list[dict], user_name: str
    ) -> dict[str, Any]:
        """
        Add events to a label
        
        Args:
            label_id: Label ID
            events: List of events to add
            user_name: Name of the user adding events
            
        Returns:
            Update result information
            
        Raises:
            NotFoundException: If label or file not found
        """
        # Get current label
        label = self.label_repo.find_by_id(label_id)
        if not label:
            raise NotFoundException("Label", label_id)

        # Update events
        self.label_repo.update_by_id(label_id, {"events": events})

        # Update file metadata
        file = self.file_repo.find_by_label_id(label_id)
        if not file:
            raise NotFoundException("File", f"with label {label_id}")

        previous_nb_events = file.get("nbEvent", "unlabeled")
        new_nb_events = self._calculate_event_count(events)

        self.file_repo.update_by_id(
            str(file["_id"]),
            {
                "nbEvent": new_nb_events,
                "lastModifier": user_name,
                "lastUpdate": datetime.now(tz=timezone.utc),
            },
        )

        # Update folder if first label
        if previous_nb_events == "unlabeled" and len(events) > 0:
            folder = self.folder_repo.find_by_file_id(str(file["_id"]))
            if folder:
                self.folder_repo.increment_labeled_files(str(folder["_id"]))

        logger.info(f"Added {len(events)} events to label {label_id}")
        return {"success": True, "events_count": len(events), "new_nb_events": new_nb_events}

    def add_events_batch(
        self, folder_id: str, events_list: list[dict], user_name: str
    ) -> dict[str, Any]:
        """
        Add events to multiple files in a folder
        
        Args:
            folder_id: Folder ID
            events_list: List of {file_name, events} dicts
            user_name: Name of the user adding events
            
        Returns:
            Batch operation results
            
        Raises:
            NotFoundException: If folder not found
        """
        # Get folder
        folder = self.folder_repo.find_by_id(folder_id)
        if not folder:
            raise NotFoundException("Folder", folder_id)

        # Get file name to label mapping
        files = self.file_repo.find_by_folder(folder["fileList"])
        file_name_to_label = {file["name"]: file["label"] for file in files}

        results = {"success": 0, "failed": 0, "errors": []}

        for event_data in events_list:
            file_name = event_data.get("file_name")
            events = event_data.get("events", [])

            if file_name not in file_name_to_label:
                results["failed"] += 1
                results["errors"].append(f"File '{file_name}' not found")
                continue

            try:
                label_id = file_name_to_label[file_name]
                self.add_events_to_label(label_id, events, user_name)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Error for {file_name}: {str(e)}")

        logger.info(f"Batch added events: {results['success']} success, {results['failed']} failed")
        return results

    def _calculate_event_count(self, events: list[dict]) -> str:
        """Calculate event count string by labeler"""
        if not events:
            return "0"

        labelers = list(set([e["labeler"] for e in events]))
        counts = []
        for labeler in labelers:
            count = len([e for e in events if e["labeler"] == labeler])
            counts.append(f"{count} by {labeler}")

        return ";".join(counts)


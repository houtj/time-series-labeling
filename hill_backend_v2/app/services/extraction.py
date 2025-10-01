"""Extraction service - Extract column info from uploaded files"""

import logging
import os
import tempfile
from typing import Any

import pandas as pd
from fastapi import UploadFile

from app.core.exceptions import NotFoundException, ValidationException
from app.repositories.template import TemplateRepository

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting data from files"""

    def __init__(self, template_repo: TemplateRepository):
        self.template_repo = template_repo

    async def extract_columns(self, file: UploadFile, template_id: str) -> dict[str, Any]:
        """
        Extract column information from an uploaded file
        
        Args:
            file: Uploaded file
            template_id: Template ID
            
        Returns:
            Dictionary with column information
            
        Raises:
            NotFoundException: If template not found
            ValidationException: If file processing fails
        """
        # Get template information
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise NotFoundException("Template", template_id)

        # Create temporary file
        suffix = file.filename if file.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            # Read file based on file type
            file_type = template.get("fileType", ".xlsx")

            if file_type == ".xlsx":
                df = self._read_excel(tmp_file_path, template, engine="openpyxl")
            elif file_type == ".xls":
                df = self._read_excel(tmp_file_path, template, engine="xlrd")
            elif file_type == ".csv":
                df = self._read_csv(tmp_file_path, template)
            else:
                raise ValidationException(f"Unsupported file type: {file_type}")

            # Extract column information
            columns = []
            for i, column_name in enumerate(df.columns):
                # Get first non-null value as sample data
                sample_data = ""
                for value in df[column_name].dropna():
                    if pd.notna(value):
                        sample_data = str(value)
                        break

                columns.append({"name": str(column_name), "index": i, "sampleData": sample_data})

            return {"columns": columns}

        except Exception as e:
            logger.error(f"Failed to process file: {e}")
            raise ValidationException(f"Failed to process file: {str(e)}")

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def _read_excel(
        self, file_path: str, template: dict, engine: str
    ) -> pd.DataFrame:
        """Read Excel file with template settings"""
        sheet_name = template.get("sheetName", 0)
        try:
            sheet_name = int(sheet_name)
        except (ValueError, TypeError):
            pass

        header = template.get("headRow", 0)

        return pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, header=header)

    def _read_csv(self, file_path: str, template: dict) -> pd.DataFrame:
        """Read CSV file with template settings"""
        header = template.get("headRow", 0)
        return pd.read_csv(file_path, header=header)


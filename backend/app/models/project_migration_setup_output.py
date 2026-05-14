from pydantic import BaseModel
from typing import Optional


class ProjectMigrationSetupOutput(BaseModel):
    valid: bool
    message: str
    target_folder_name: Optional[str] = None
    target_full_path: Optional[str] = None

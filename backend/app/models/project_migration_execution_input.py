from pydantic import BaseModel
from typing import Optional


class MigrationExecutionInput(BaseModel):
    file_path: str
    source_code: str
    migrated_code: Optional[str] = None
    user_comment: Optional[str] = None
    mode: str  # INITIAL | REPAIR

from pydantic import BaseModel
from typing import List, Optional


class FileExecution(BaseModel):
    path: str
    status: str
    original: str
    migrated: str
    justification: Optional[str] = None
    decision: Optional[str] = None
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    target_root: Optional[str] = None


class ExecutionResult(BaseModel):
    status: str
    files: List[FileExecution]


class MigrationExecutionOutput(BaseModel):
    executionResult: ExecutionResult

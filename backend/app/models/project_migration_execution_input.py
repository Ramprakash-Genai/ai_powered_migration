from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Literal

ExecutionMode = Literal["INITIAL_MIGRATION", "REVIEW_REPAIR", "FINALIZE_FILE"]


class MigrationExecutionInput(BaseModel):
    # which action to perform
    execution_mode: ExecutionMode

    # repository input
    source_repo_path: Optional[str] = None

    # target details from popup
    target_language: Optional[str] = None
    target_bdd: Optional[str] = None
    target_build_tool: Optional[str] = None
    target_runner: Optional[str] = None
    target_path: Optional[str] = None
    repo_name: Optional[str] = None

    # source details (from detection)
    source_language: Optional[str] = None
    source_bdd: Optional[str] = None

    # migration plan (Agent-3 output)
    migration_plan: Optional[Dict[str, Any]] = None

    # per-file actions
    file_path: Optional[str] = None
    original_source_code: Optional[str] = None
    migrated_code: Optional[str] = None
    user_feedback: Optional[str] = None

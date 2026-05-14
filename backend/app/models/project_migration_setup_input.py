from pydantic import BaseModel, Field
from typing import Literal


class ProjectMigrationSetupInput(BaseModel):
    target_language: Literal["java", "python", "csharp"]
    target_bdd_framework: str
    target_build_tool: str
    target_runner: str
    target_base_path: str = Field(
        ..., description="Absolute folder path where migrated project will be created"
    )
    new_repo_name: str = Field(
        ..., description="Base name for new repo (without suffix)"
    )

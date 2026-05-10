from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class FileGroup(BaseModel):
    count: int = 0
    files: List[str] = Field(default_factory=list)


class ScenarioPlan(BaseModel):
    scenario_name: str
    step_count: int = 0
    steps: List[str] = Field(default_factory=list)


class ProjectMigrationPlannerOutput(BaseModel):
    """
    Output from Agent-3 (shown to user for confirmation in UI later).
    """

    input_type: Literal["repository", "html_report"]
    source_path: str

    # Repository planning output
    feature_files: Optional[FileGroup] = None
    step_definition_files: Optional[FileGroup] = None
    support_files: Optional[FileGroup] = None
    config_files: Optional[FileGroup] = None

    # HTML planning output
    total_scenarios: Optional[int] = None
    scenarios: Optional[List[ScenarioPlan]] = None

    ready_for_conversion: bool = True

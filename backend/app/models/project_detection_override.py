from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any


class UserCorrection(BaseModel):
    """
    Structured correction submitted from the UI popup.
    Keep fields optional because HTML report won't have all fields.
    """

    corrected_language: Optional[Literal["java", "python", "csharp", "unknown"]] = None
    corrected_bdd_framework: Optional[str] = None
    corrected_build_tool: Optional[str] = None
    corrected_runner: Optional[str] = None
    reason: Optional[str] = Field(default=None, max_length=200)


class ProjectDetectionOverrideInput(BaseModel):
    """
    Payload for override arbitration.
    """

    input_type: Literal["repository", "html_report"]
    input_path: str
    user_project_style: Optional[str] = None

    # snapshot of what system detected earlier (as UI saw it)
    current_detection: Dict[str, Any]

    # user correction coming from popup dialog
    user_correction: UserCorrection

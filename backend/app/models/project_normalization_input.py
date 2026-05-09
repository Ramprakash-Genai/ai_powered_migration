from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ProjectNormalizationInput(BaseModel):
    input_type: str  # repository | html_report
    input_path: str

    # Detected info from Agent-1
    language: Optional[str] = None
    bdd_framework: Optional[str] = None
    build_tool: Optional[str] = None
    runner: Optional[str] = None

    # User intent & metadata
    user_project_style: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[List[str]] = None

    # Allow forward compatibility
    extra: Optional[Dict[str, Any]] = None

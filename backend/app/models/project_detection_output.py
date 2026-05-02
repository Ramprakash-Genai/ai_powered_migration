from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal


class ProjectDetectionOutput(BaseModel):
    input_type: Literal["repository", "html_report"]

    # UI intent echo
    user_project_style: Optional[str] = None

    # Common
    name: str = Field(description="Project name or report name")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)

    # Repository detection fields
    language: Optional[str] = None
    bdd_framework: Optional[str] = None
    build_tool: Optional[str] = None
    runner: Optional[str] = None
    signals: Optional[Dict[str, Any]] = None

    # HTML report extraction fields
    report_type: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    scenarios: List[str] = Field(default_factory=list)

    # ✅ New optional fields (do not break UI)
    intent_mismatch: Optional[bool] = None
    intent_mismatch_reasons: List[str] = Field(default_factory=list)
    validation_source: Optional[Literal["rule", "model"]] = "rule"

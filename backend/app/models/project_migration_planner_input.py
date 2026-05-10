from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class PlannerTechnology(BaseModel):
    language: Optional[str] = None  # java | python | csharp | unknown
    bdd_framework: Optional[str] = None
    build_tool: Optional[str] = None
    runner: Optional[str] = None


class ProjectMigrationPlannerInput(BaseModel):
    """
    Input to Agent-3 (Migration Planner / Step Extractor).

    Designed to consume NIM output from Agent-2.
    For html_report mode, optionally include scenarios/steps extracted by Agent-1.
    """

    context_type: Literal["repository", "html_report"]
    source_path: str

    technology: PlannerTechnology = Field(default_factory=PlannerTechnology)

    # Optional: when context_type == html_report, pass extracted artifacts for better planning
    report_type: Optional[str] = None
    scenarios: Optional[List[str]] = None
    steps: Optional[List[str]] = None

    # Optional passthrough (future-proof)
    meta: Optional[Dict[str, Any]] = None

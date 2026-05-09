from pydantic import BaseModel
from typing import Dict, Optional


class NormalizedTechnology(BaseModel):
    language: str
    bdd_framework: Optional[str] = None
    build_tool: Optional[str] = None
    runner: Optional[str] = None


class RepositorySummary(BaseModel):
    feature_count: int
    step_definition_language: Optional[str] = None
    hooks_present: bool = False


class ProjectNormalizationOutput(BaseModel):
    context_type: str  # repository | html_report
    source_path: str

    technology: NormalizedTechnology
    repo_summary: Optional[RepositorySummary] = None

    intent_confirmed: bool
    ready_for_migration: bool

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal


class ProjectDetectionOutput(BaseModel):
    """
    Output contract for Migration Overview panel (Step-4).

    We intentionally DO NOT return match/partial/conflict.
    UI will show only:
      - Yes correct, Go ahead for Migrate
      - No not correct, Don't Migrate
    """

    input_type: Literal["repository", "html_report"]

    # UI intent (echo)
    user_project_style: Optional[str] = None

    # Common
    name: str = Field(description="Project name or report name")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)

    # Repository detection fields
    language: Optional[str] = None  # java | python | csharp | unknown
    bdd_framework: Optional[str] = (
        None  # cucumber | behave | pytest-bdd | specflow | gauge | unknown
    )
    build_tool: Optional[str] = None  # maven | gradle | pip | poetry | dotnet | unknown
    runner: Optional[str] = (
        None  # junit | testng | pytest | behave | nunit | mstest | xunit | unknown
    )
    signals: Optional[Dict[str, Any]] = None

    # HTML report extraction fields
    report_type: Optional[str] = None  # allure | gauge | unknown
    steps: List[str] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    scenarios: List[str] = Field(default_factory=list)

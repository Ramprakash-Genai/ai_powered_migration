from pydantic import BaseModel, Field
from typing import Literal, Optional


class ProjectDetectionInput(BaseModel):
    """
    Input contract for Project Detection (Agent #1).

    - user_project_style: intent from UI step-1 (hint, not truth)
    - input_type: repository folder OR html report file
    - input_path: filesystem path on server/local machine
    """

    user_project_style: Optional[str] = Field(
        default=None,
        description="User-selected intent: java-selenium-bdd | python-selenium-bdd | csharp-selenium-bdd",
    )

    input_type: Literal["repository", "html_report"] = Field(
        description="repository folder OR html report file"
    )

    input_path: str = Field(
        description="Absolute or relative path to repository folder or html report file"
    )

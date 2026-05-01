from fastapi import APIRouter, HTTPException
from app.models.project_detection_input import ProjectDetectionInput
from app.agents.project_detection_agent import ProjectDetectionAgent

router = APIRouter(prefix="/api", tags=["project-detection"])


@router.post("/project-detection")
def detect_project(inp: ProjectDetectionInput):
    """
    Accepts:
      - input_type: repository | html_report
      - input_path: folder path OR html file path
      - user_project_style: optional intent hint

    Returns:
      ProjectDetectionOutput JSON (for Migration Overview panel)
    """
    agent = ProjectDetectionAgent()
    try:
        out = agent.run(inp)
        return out
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Project detection failed: {str(e)}"
        )

from fastapi import APIRouter, HTTPException
from app.models.project_normalization_input import ProjectNormalizationInput
from app.agents.project_normalization_agent import ProjectNormalizationAgent

router = APIRouter(
    prefix="/api/project-normalization",
    tags=["project-normalization"],
)


@router.post("/build")
def build_normalized_context(inp: ProjectNormalizationInput):
    """
    Builds Normalized Intermediate Model (NIM)
    from Project Detection output.
    """
    try:
        agent = ProjectNormalizationAgent()
        out = agent.run(inp)
        return out
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Project normalization failed: {str(e)}",
        )

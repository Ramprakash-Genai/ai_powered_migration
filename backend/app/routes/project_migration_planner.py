from fastapi import APIRouter, HTTPException
from app.models.project_migration_planner_input import ProjectMigrationPlannerInput
from app.agents.project_migration_planner_agent import ProjectMigrationPlannerAgent

router = APIRouter(
    prefix="/api/project-migration-planner",
    tags=["project-migration-planner"],
)

@router.post("/plan")
def plan_migration(inp: ProjectMigrationPlannerInput):
    """
    Agent-3: Rule-based Migration Planner / Step Extractor.
    Repository: lists features, step definitions, support, config.
    HTML report: lists scenarios and steps (from extracted data).
    """
    try:
        agent = ProjectMigrationPlannerAgent()
        return agent.run(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration planning failed: {str(e)}")

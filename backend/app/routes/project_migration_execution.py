from fastapi import APIRouter, HTTPException
from app.models.project_migration_execution_input import MigrationExecutionInput
from app.agents.project_migration_execution_agent import ProjectMigrationExecutionAgent

router = APIRouter(
    prefix="/api/project-migration-execution", tags=["project-migration-execution"]
)


@router.post("/execute")
def execute_migration(payload: MigrationExecutionInput):
    try:
        agent = ProjectMigrationExecutionAgent()
        return agent.execute(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

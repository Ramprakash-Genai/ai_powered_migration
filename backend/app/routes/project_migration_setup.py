from fastapi import APIRouter
from app.models.project_migration_setup_input import ProjectMigrationSetupInput
from app.agents.project_migration_setup_agent import ProjectMigrationSetupAgent

router = APIRouter(
    prefix="/api/project-migration-setup", tags=["project-migration-setup"]
)


@router.post("/validate")
def validate_setup(inp: ProjectMigrationSetupInput):
    agent = ProjectMigrationSetupAgent()
    return agent.validate(inp)

import os
import re
from pathlib import Path
from app.models.project_migration_setup_input import ProjectMigrationSetupInput
from app.models.project_migration_setup_output import ProjectMigrationSetupOutput

INVALID_NAME_CHARS = r'[<>:"/\\|?*\x00-\x1F]'


class ProjectMigrationSetupAgent:
    """
    Agent‑4 Setup Validator (no migration yet):
    - Validates target_base_path exists and is a directory
    - Validates repo name is safe
    - Returns computed target folder name + full path
    """

    def validate(self, inp: ProjectMigrationSetupInput) -> ProjectMigrationSetupOutput:
        base = Path(inp.target_base_path).expanduser().resolve()

        if not base.exists() or not base.is_dir():
            return ProjectMigrationSetupOutput(
                valid=False,
                message="Invalid absolute path. Please provide an existing folder path.",
            )

        repo = inp.new_repo_name.strip()

        if not repo:
            return ProjectMigrationSetupOutput(
                valid=False, message="Repository name is required."
            )

        if re.search(INVALID_NAME_CHARS, repo):
            return ProjectMigrationSetupOutput(
                valid=False,
                message="Repository name contains unsupported characters. Please provide a valid folder name.",
            )

        target_folder = f"{repo}_to_playwright_migrated"
        target_full = base / target_folder

        # Do not create folder yet (validation-only phase)
        return ProjectMigrationSetupOutput(
            valid=True,
            message="Validation successful. Ready to create migration project.",
            target_folder_name=target_folder,
            target_full_path=str(target_full),
        )

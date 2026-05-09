from app.models.project_normalization_input import ProjectNormalizationInput
from app.models.project_normalization_output import (
    ProjectNormalizationOutput,
    NormalizedTechnology,
    RepositorySummary,
)


class ProjectNormalizationAgent:
    """
    Agent-2: Normalization / NIM Agent
    Converts Project Detection output into a stable,
    migration-ready intermediate model.
    """

    def run(self, inp: ProjectNormalizationInput) -> ProjectNormalizationOutput:
        # Normalize technology layer
        technology = NormalizedTechnology(
            language=inp.language or "unknown",
            bdd_framework=inp.bdd_framework,
            build_tool=inp.build_tool,
            runner=inp.runner,
        )

        # Decide intent confirmation
        intent_confirmed = False
        if inp.user_project_style and inp.language:
            intent_confirmed = inp.language.lower() in inp.user_project_style.lower()

        # Build repo summary only for repository input
        repo_summary = None
        if inp.input_type == "repository":
            # NOTE: placeholders for now (can be extended later)
            repo_summary = RepositorySummary(
                feature_count=0,
                step_definition_language=inp.language,
                hooks_present=False,
            )

        output = ProjectNormalizationOutput(
            context_type=inp.input_type,
            source_path=inp.input_path,
            technology=technology,
            repo_summary=repo_summary,
            intent_confirmed=intent_confirmed,
            ready_for_migration=True,
        )

        # ✅ TEMP: Print NIM output for verification
        print("\n✅ NIM OUTPUT (Normalized Intermediate Model):")
        print(output.model_dump())
        print("✅ End of NIM output\n")

        return output

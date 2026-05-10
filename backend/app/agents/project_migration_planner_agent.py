from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Set, Tuple

from app.models.project_migration_planner_input import ProjectMigrationPlannerInput
from app.models.project_migration_planner_output import (
    ProjectMigrationPlannerOutput,
    FileGroup,
    ScenarioPlan,
)

# Safety: folders we usually do NOT want to scan
SKIP_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    ".gradle",
    ".m2",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

FEATURE_EXT = ".feature"

JAVA_STEP_PAT = re.compile(r"@(Given|When|Then)\b")
JAVA_HOOK_PAT = re.compile(r"@Before\b|@After\b")

PY_STEP_PAT = re.compile(r"@(given|when|then)\b", re.IGNORECASE)
CS_STEP_PAT = re.compile(r"\[(Given|When|Then)\b")
CS_HOOK_PAT = re.compile(
    r"\[(BeforeScenario|AfterScenario|BeforeTestRun|AfterTestRun)\b"
)

CONFIG_NAMES = {
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "requirements.txt",
    "pyproject.toml",
    "pytest.ini",
    "tox.ini",
    "behave.ini",
    "specflow.json",
    "testng.xml",
    "junit-platform.properties",
    "cucumber.properties",
    "cucumber.yml",
    ".runsettings",
    "app.config",
}


def _read_text_safely(path: Path, max_bytes: int = 300_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _iter_repo_files(repo_root: Path, max_files: int = 20000) -> List[Path]:
    files: List[Path] = []
    count = 0
    for root, dirnames, filenames in os.walk(repo_root):
        # prune unwanted directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fn in filenames:
            count += 1
            if count > max_files:
                return files
            files.append(Path(root) / fn)
    return files


def _rel(repo_root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(repo_root)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")


class ProjectMigrationPlannerAgent:
    """
    Agent-3: Project Migration Planner / Step Extractor (Rule-based).
    - Repository: enumerates feature files, step definition files, support files, config files.
    - HTML report: enumerates scenarios and steps (from provided extracted lists).
    No model/LLM is used here. 【1-6b281a】
    """

    def run(self, inp: ProjectMigrationPlannerInput) -> ProjectMigrationPlannerOutput:
        if inp.context_type == "repository":
            return self._plan_repository(inp)
        return self._plan_html_report(inp)

    def _plan_repository(
        self, inp: ProjectMigrationPlannerInput
    ) -> ProjectMigrationPlannerOutput:
        repo_root = Path(inp.source_path).resolve()
        if not repo_root.exists() or not repo_root.is_dir():
            # return empty plan but marked not ready
            return ProjectMigrationPlannerOutput(
                input_type="repository",
                source_path=inp.source_path,
                feature_files=FileGroup(count=0, files=[]),
                step_definition_files=FileGroup(count=0, files=[]),
                support_files=FileGroup(count=0, files=[]),
                config_files=FileGroup(count=0, files=[]),
                ready_for_conversion=False,
            )

        language = (inp.technology.language or "unknown").lower().strip()

        files = _iter_repo_files(repo_root)

        feature_files: Set[str] = set()
        step_defs: Set[str] = set()
        support_files: Set[str] = set()
        config_files: Set[str] = set()

        # Heuristic support folders
        support_folder_tokens = (
            "helper",
            "helpers",
            "util",
            "utils",
            "support",
            "page",
            "pages",
            "pageobject",
            "pageobjects",
        )

        for p in files:
            name_lower = p.name.lower()
            suf = p.suffix.lower()
            rel = _rel(repo_root, p)

            # Config files
            if name_lower in CONFIG_NAMES or suf in (".csproj", ".sln"):
                config_files.add(rel)

            # Feature files
            if suf == FEATURE_EXT:
                feature_files.add(rel)
                continue

            # Support file heuristic (folder names)
            if any(tok in rel.lower().split("/") for tok in support_folder_tokens):
                # only consider code-ish files
                if suf in (".java", ".py", ".cs", ".js", ".ts"):
                    support_files.add(rel)

            # Step definition / hooks heuristic by language
            if language == "java" and suf == ".java":
                txt = _read_text_safely(p)
                if JAVA_STEP_PAT.search(txt):
                    step_defs.add(rel)
                if JAVA_HOOK_PAT.search(txt) or "hooks" in name_lower:
                    support_files.add(rel)

            elif language == "python" and suf == ".py":
                txt = _read_text_safely(p)
                txt_low = txt.lower()
                if (
                    PY_STEP_PAT.search(txt)
                    or "pytest_bdd" in txt_low
                    or "from behave" in txt_low
                ):
                    step_defs.add(rel)
                if name_lower in ("environment.py", "conftest.py"):
                    support_files.add(rel)

            elif language == "csharp" and suf == ".cs":
                txt = _read_text_safely(p)
                if CS_STEP_PAT.search(txt):
                    step_defs.add(rel)
                if CS_HOOK_PAT.search(txt) or "hooks" in name_lower:
                    support_files.add(rel)

        # Build output groups (sorted for stable UI)
        f_list = sorted(feature_files)
        s_list = sorted(step_defs)
        sup_list = sorted(
            support_files - step_defs
        )  # avoid duplicates: step defs are not support
        c_list = sorted(config_files)

        return ProjectMigrationPlannerOutput(
            input_type="repository",
            source_path=str(repo_root),
            feature_files=FileGroup(count=len(f_list), files=f_list),
            step_definition_files=FileGroup(count=len(s_list), files=s_list),
            support_files=FileGroup(count=len(sup_list), files=sup_list),
            config_files=FileGroup(count=len(c_list), files=c_list),
            ready_for_conversion=True
            if (len(f_list) > 0 or len(s_list) > 0)
            else False,
        )

    def _plan_html_report(
        self, inp: ProjectMigrationPlannerInput
    ) -> ProjectMigrationPlannerOutput:
        # For HTML report mode, we rely on scenarios/steps passed from Agent-1 detection output.
        scenarios = inp.scenarios or []
        steps = inp.steps or []

        # If we have scenarios but no mapping per scenario, we still present totals safely.
        # (Later, we can enhance html parser to map scenario->steps.)
        scenario_plans: List[ScenarioPlan] = []

        if scenarios:
            # Put the SAME step list under each scenario for now only if there is a single scenario.
            # If multiple scenarios, we show step list only at first scenario to avoid misleading split.
            if len(scenarios) == 1:
                scenario_plans.append(
                    ScenarioPlan(
                        scenario_name=scenarios[0],
                        step_count=len(steps),
                        steps=steps,
                    )
                )
            else:
                # Multiple scenarios but unknown distribution: show names with step_count=0
                for sc in scenarios:
                    scenario_plans.append(
                        ScenarioPlan(
                            scenario_name=sc,
                            step_count=0,
                            steps=[],
                        )
                    )
        else:
            # No scenarios, but steps exist: treat as one unnamed scenario
            if steps:
                scenario_plans.append(
                    ScenarioPlan(
                        scenario_name="Scenario 1",
                        step_count=len(steps),
                        steps=steps,
                    )
                )

        return ProjectMigrationPlannerOutput(
            input_type="html_report",
            source_path=inp.source_path,
            total_scenarios=len(scenario_plans),
            scenarios=scenario_plans,
            ready_for_conversion=True
            if (len(steps) > 0 or len(scenario_plans) > 0)
            else False,
        )

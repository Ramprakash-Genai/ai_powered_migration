from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.parsers.html_report_parser import parse_html_report
from app.models.project_detection_input import ProjectDetectionInput
from app.models.project_detection_output import ProjectDetectionOutput

# Optional CrewAI import (safe)
try:
    from crewai import Agent as CrewAgent  # type: ignore
except Exception:
    CrewAgent = None

# Optional LangGraph import (safe)
try:
    from langgraph.graph import StateGraph, END  # type: ignore
except Exception:
    StateGraph = None
    END = None


@dataclass
class AgentControls:
    temperature: float = 0.0
    max_iterations: int = 1
    strict_deterministic: bool = True


@dataclass
class AgentMemory:
    last_inputs: List[Dict[str, Any]] = field(default_factory=list)
    last_outputs: List[Dict[str, Any]] = field(default_factory=list)

    def remember(self, inp: Dict[str, Any], out: Dict[str, Any]) -> None:
        self.last_inputs.append(inp)
        self.last_outputs.append(out)
        if len(self.last_inputs) > 20:
            self.last_inputs.pop(0)
        if len(self.last_outputs) > 20:
            self.last_outputs.pop(0)


FEATURE_EXT = ".feature"


def _walk_files(repo_path: Path, max_files: int = 20000) -> List[Path]:
    files: List[Path] = []
    count = 0
    for root, _, filenames in os.walk(repo_path):
        for fn in filenames:
            count += 1
            if count > max_files:
                return files
            files.append(Path(root) / fn)
    return files


def _read_text_safely(path: Path, max_bytes: int = 300_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _detect_repository(repo_path: str) -> Dict[str, Any]:
    repo = Path(repo_path).resolve()
    evidence: List[str] = []

    result: Dict[str, Any] = {
        "name": repo.name,
        "language": "unknown",
        "bdd_framework": "unknown",
        "build_tool": "unknown",
        "runner": "unknown",
        "signals": {
            "feature_files_found": 0,
            "step_definition_files_found": 0,
            "hooks_files_found": 0,
        },
        "evidence": evidence,
        "confidence": 0.0,
    }

    if not repo.exists() or not repo.is_dir():
        evidence.append("Invalid repository path (not found or not a folder)")
        return result

    files = _walk_files(repo)

    # Build/Language strong signals
    has_pom = (repo / "pom.xml").exists()
    has_gradle = (repo / "build.gradle").exists() or (
        repo / "build.gradle.kts"
    ).exists()
    has_req = (repo / "requirements.txt").exists()
    has_pyproject = (repo / "pyproject.toml").exists()
    csproj = [p for p in files if p.suffix.lower() == ".csproj"]
    sln = [p for p in files if p.suffix.lower() == ".sln"]

    if has_pom:
        result["language"] = "java"
        result["build_tool"] = "maven"
        evidence.append("Found pom.xml → Java/Maven")
    elif has_gradle:
        result["language"] = "java"
        result["build_tool"] = "gradle"
        evidence.append("Found build.gradle → Java/Gradle")
    elif csproj or sln:
        result["language"] = "csharp"
        result["build_tool"] = "dotnet"
        evidence.append("Found .csproj/.sln → C#/.NET")
    elif has_req or has_pyproject:
        result["language"] = "python"
        result["build_tool"] = "poetry" if has_pyproject else "pip"
        evidence.append("Found requirements.txt/pyproject.toml → Python")
    else:
        evidence.append(
            "No strong build files found (pom.xml/build.gradle/requirements.txt/pyproject/.csproj/.sln)"
        )

    # Feature files
    feature_files = [p for p in files if p.suffix.lower() == FEATURE_EXT]
    result["signals"]["feature_files_found"] = len(feature_files)
    if feature_files:
        evidence.append(f"Found {len(feature_files)} .feature files")

    # Framework detection from manifests
    pom = repo / "pom.xml"
    if pom.exists():
        txt = _read_text_safely(pom).lower()
        if "cucumber" in txt:
            result["bdd_framework"] = "cucumber"
            evidence.append("pom.xml mentions cucumber → Cucumber JVM")
        if "testng" in txt:
            result["runner"] = "testng"
            evidence.append("pom.xml mentions testng → TestNG runner")
        if "junit" in txt and result["runner"] == "unknown":
            result["runner"] = "junit"
            evidence.append("pom.xml mentions junit → JUnit runner")

    req = repo / "requirements.txt"
    if req.exists():
        txt = _read_text_safely(req).lower()
        if "behave" in txt:
            result["bdd_framework"] = "behave"
            result["runner"] = "behave"
            evidence.append("requirements.txt mentions behave → Behave BDD")
        if "pytest-bdd" in txt:
            result["bdd_framework"] = "pytest-bdd"
            result["runner"] = "pytest"
            evidence.append("requirements.txt mentions pytest-bdd → pytest-bdd")
        if "pytest" in txt and result["runner"] == "unknown":
            result["runner"] = "pytest"
            evidence.append("requirements.txt mentions pytest → pytest runner")

    # SpecFlow detection
    if result["language"] == "csharp":
        specflow_json = [p for p in files if p.name.lower() == "specflow.json"]
        if specflow_json:
            result["bdd_framework"] = "specflow"
            evidence.append("Found specflow.json → SpecFlow")
        for p in csproj[:10]:
            txt = _read_text_safely(p).lower()
            if "specflow" in txt:
                result["bdd_framework"] = "specflow"
                evidence.append(f"{p.name} mentions specflow")
                break
            if "nunit" in txt:
                result["runner"] = "nunit"
                evidence.append(f"{p.name} mentions nunit")
            if "mstest" in txt and result["runner"] == "unknown":
                result["runner"] = "mstest"
                evidence.append(f"{p.name} mentions mstest")
            if "xunit" in txt and result["runner"] == "unknown":
                result["runner"] = "xunit"
                evidence.append(f"{p.name} mentions xunit")

    # Step definitions / hooks heuristic
    step_files: List[Path] = []
    hook_files: List[Path] = []

    # Java annotations
    for p in [x for x in files if x.suffix.lower() == ".java"][:5000]:
        txt = _read_text_safely(p)
        if re.search(r"@(Given|When|Then)\b", txt):
            step_files.append(p)
        if re.search(r"@Before\b|@After\b", txt) or "Hooks" in p.name:
            hook_files.append(p)

    # Python decorators / behave / pytest-bdd
    for p in [x for x in files if x.suffix.lower() == ".py"][:5000]:
        txt = _read_text_safely(p).lower()
        if (
            re.search(r"@(given|when|then)\b", txt)
            or "from behave" in txt
            or "pytest_bdd" in txt
        ):
            step_files.append(p)
        if p.name.lower() in ("environment.py", "conftest.py"):
            hook_files.append(p)

    # C# attributes
    for p in [x for x in files if x.suffix.lower() == ".cs"][:5000]:
        txt = _read_text_safely(p)
        if re.search(r"\[(Given|When|Then)\b", txt):
            step_files.append(p)
        if (
            re.search(
                r"\[(BeforeScenario|AfterScenario|BeforeTestRun|AfterTestRun)\b", txt
            )
            or "Hooks" in p.name
        ):
            hook_files.append(p)

    step_files = list(dict.fromkeys(step_files))
    hook_files = list(dict.fromkeys(hook_files))
    result["signals"]["step_definition_files_found"] = len(step_files)
    result["signals"]["hooks_files_found"] = len(hook_files)

    if step_files:
        evidence.append(f"Detected {len(step_files)} step definition files (heuristic)")
    if hook_files:
        evidence.append(f"Detected {len(hook_files)} hook/config files (heuristic)")

    # Confidence scoring (deterministic)
    score = 0.0
    if result["language"] != "unknown":
        score += 0.25
    if result["build_tool"] != "unknown":
        score += 0.15
    if result["bdd_framework"] != "unknown":
        score += 0.25
    if result["signals"]["feature_files_found"] > 0:
        score += 0.15
    if result["signals"]["step_definition_files_found"] > 0:
        score += 0.15
    if result["signals"]["hooks_files_found"] > 0:
        score += 0.05

    result["confidence"] = round(min(score, 1.0), 2)
    return result


class ProjectDetectionAgent:
    """
    Role: Project Detection Agent (Agent #1)
    Behavior:
      - If input_type == repository: detect project language/framework/tooling from folder structure.
      - If input_type == html_report: extract step list + screenshot refs from HTML (no structure scan).
    """

    def __init__(
        self,
        controls: Optional[AgentControls] = None,
        memory: Optional[AgentMemory] = None,
    ):
        self.controls = controls or AgentControls()
        self.memory = memory or AgentMemory()

        # CrewAI wrapper (optional, metadata only)
        self.crewai_agent = None
        if CrewAgent is not None:
            self.crewai_agent = CrewAgent(
                role="Project Detection Agent",
                goal="Detect project setup (repo) OR extract steps/screenshots (html report) with evidence. No guessing.",
                backstory="You are evidence-first and deterministic. You never invent missing facts.",
                allow_delegation=False,
                verbose=False,
            )

    def run(self, inp: ProjectDetectionInput) -> ProjectDetectionOutput:
        if inp.input_type == "repository":
            detected = _detect_repository(inp.input_path)

            out = ProjectDetectionOutput(
                input_type="repository",
                user_project_style=inp.user_project_style,
                name=detected["name"],
                language=detected["language"],
                bdd_framework=detected["bdd_framework"],
                build_tool=detected["build_tool"],
                runner=detected["runner"],
                signals=detected["signals"],
                evidence=detected["evidence"],
                confidence=detected["confidence"],
            )
            self.memory.remember(inp.model_dump(), out.model_dump())
            return out

        # html_report mode (step + screenshot extraction)
        parsed = parse_html_report(inp.input_path)

        out = ProjectDetectionOutput(
            input_type="html_report",
            user_project_style=inp.user_project_style,
            name=parsed["name"],
            report_type=parsed["report_type"],
            steps=parsed["steps"],
            screenshots=parsed["screenshots"],
            scenarios=parsed["scenarios"],
            evidence=parsed["evidence"],
            confidence=parsed["confidence"],
        )
        self.memory.remember(inp.model_dump(), out.model_dump())
        return out


# LangGraph node (orchestration-ready)
def project_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input state expects:
      {
        "user_project_style": "...",
        "input_type": "repository|html_report",
        "input_path": "..."
      }
    Output adds:
      { "project_detection": <ProjectDetectionOutput dict> }
    """
    inp = ProjectDetectionInput(**state)
    agent = ProjectDetectionAgent()
    out = agent.run(inp)
    return {**state, "project_detection": out.model_dump()}


def build_project_detection_graph():
    if StateGraph is None:
        raise RuntimeError("langgraph not available")

    graph = StateGraph(dict)
    graph.add_node("project_detection", project_detection_node)
    graph.set_entry_point("project_detection")
    graph.add_edge("project_detection", END)
    return graph.compile()

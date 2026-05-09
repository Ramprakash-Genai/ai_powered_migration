from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.parsers.html_report_parser import parse_html_report
from app.models.project_detection_input import ProjectDetectionInput
from app.models.project_detection_output import ProjectDetectionOutput
from app.models.project_detection_override import ProjectDetectionOverrideInput

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
    """
    Summary of walk files:
        sample_repo/
        ├── pom.xml
        ├── README.md
        ├── src/
        │   └── test/
        │       └── java/
        │           └── LoginTest.java
        └── features/
            └── login.feature

    How the below program works:
        First iteration:
        root = "C:/Projects/sample_repo"
        filenames = ["pom.xml", "README.md"]
        ie
        File: 1
           fn = "pom.xml"
            count = 1
            files.append(Path("C:/Projects/sample_repo/pom.xml"))
        File:2
            fn = "README.md"
            count = 2
            files.append(Path("C:/Projects/sample_repo/README.md"))
            \.....\---similarly each iteration get the file names and its count from the repo folder
            Finally
            return files = [
                        Path("C:/Projects/sample_repo/pom.xml"),
                        Path("C:/Projects/sample_repo/README.md"),
                        Path("C:/Projects/sample_repo/src/test/java/LoginTest.java"),
                        Path("C:/Projects/sample_repo/features/login.feature")
                    ]
            Note: on final step the count get increased to the number of Files (ie 4 as per above eg)
            In For loop :
            root - current folder
            _ - sub folder
            filenames - Files in the folder
    """
    # initialized with empty list and zero count
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


def _expected_language_from_intent(intent: Optional[str]) -> Optional[str]:
    if intent == "java-selenium-bdd":
        return "java"
    if intent == "python-selenium-bdd":
        return "python"
    if intent == "csharp-selenium-bdd":
        return "csharp"
    return None


def _detect_repository(repo_path: str) -> Dict[str, Any]:
    """
    Detect repository working Summary:
    Detecting the repository based on the different level of validation and strong walk through inside with
    each folder and files from the root folder and return the results
    """

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
      - Repository: deterministic detection + authoritative intent mismatch evidence (rules only).
      - HTML report: deterministic extraction; language/tool cannot be validated (trust user intent).
    """

    def __init__(
        self,
        controls: Optional[AgentControls] = None,
        memory: Optional[AgentMemory] = None,
    ):
        self.controls = controls or AgentControls()
        self.memory = memory or AgentMemory()

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
            detected: Dict[str, Any] = _detect_repository(inp.input_path)
            expected_lang: str | None = _expected_language_from_intent(
                inp.user_project_style
            )

            intent_mismatch = False
            mismatch_reasons: List[str] = []

            if (
                expected_lang
                and detected["language"] != "unknown"
                and detected["language"] != expected_lang
            ):
                intent_mismatch = True
                mismatch_reasons.append(
                    f"User selected '{expected_lang}' style but repository appears '{detected['language']}'"
                )
                detected["evidence"].insert(
                    0,
                    f"⚠️ Intent mismatch: User selected '{expected_lang}' style but repository appears '{detected['language']}'.",
                )
                # reduce confidence slightly (still deterministic)
                detected["confidence"] = max(
                    0.0, round(detected["confidence"] - 0.2, 2)
                )

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
                intent_mismatch=intent_mismatch,
                intent_mismatch_reasons=mismatch_reasons,
                validation_source="rule",
            )
            self.memory.remember(inp.model_dump(), out.model_dump())
            return out

        # html_report mode
        parsed = parse_html_report(inp.input_path)

        # Explicitly state limitation if user intent exists
        # HTML report evidence handling (confidence-aware)
        ev = list(parsed.get("evidence", []))

        confidence = parsed.get("confidence", 0.0)

        if confidence >= 0.9:
            ev.insert(
                0,
                "✅ HTML report parsed successfully with high confidence. Extracted details are sufficient to proceed with migration.",
            )
        else:
            ev.insert(
                0,
                "ℹ️ HTML report does not contain reliable language/build metadata; proceeding based on user-selected project style.",
            )
        out = ProjectDetectionOutput(
            input_type="html_report",
            user_project_style=inp.user_project_style,
            name=parsed["name"],
            report_type=parsed["report_type"],
            steps=parsed["steps"],
            screenshots=parsed["screenshots"],
            scenarios=parsed["scenarios"],
            evidence=ev,
            confidence=parsed["confidence"],
            intent_mismatch=False,
            intent_mismatch_reasons=[],
            validation_source="rule",
        )
        self.memory.remember(inp.model_dump(), out.model_dump())
        return out

    def arbitrate_override(self, inp: ProjectDetectionOverrideInput) -> Dict[str, Any]:
        """
        Rules-first arbitration.
        Returns dict: { decision, updated_detection, validation_source, evidence }
        """
        input_type = inp.input_type
        user_style = inp.user_project_style
        correction = inp.user_correction
        current = inp.current_detection or {}

        # Default updated detection = current (we may replace)
        updated_detection = dict(current)
        evidence: List[str] = (
            list(current.get("evidence", []))
            if isinstance(current.get("evidence", []), list)
            else []
        )

        # Repository arbitration: validate correction against repo signals
        if input_type == "repository":
            detected = _detect_repository(inp.input_path)
            # ✅ Guard: repository override REQUIRES corrected language
            if (
                not correction.corrected_language
                or correction.corrected_language == "unknown"
            ):
                return {
                    "decision": "rejected",
                    "updated_detection": current,
                    "validation_source": "rule",
                    "evidence": [
                        "❌ Correction rejected: Programming Language is required to validate a repository."
                    ],
                }

            # Build a rule-based decision:
            # If user correction language provided and does not match detected, reject.
            if correction.corrected_language and detected["language"] != "unknown":
                if correction.corrected_language != detected["language"]:
                    evidence.insert(
                        0,
                        (
                            f"❌ Conflict detected: Repository analysis indicates '{detected['language']}' "
                            f"(originally detected from the uploaded repository), but you provided "
                            f"'{correction.corrected_language}' in the confirmation popup. "
                            "Unable to move forward. Please restart and provide correct details."
                        ),
                    )
                    return {
                        "decision": "rejected",
                        "updated_detection": current,
                        "validation_source": "rule",
                        "evidence": evidence,
                    }

            # If user correction framework provided and repo already detected a concrete framework, validate.
            if (
                correction.corrected_bdd_framework
                and detected["bdd_framework"] != "unknown"
            ):
                if (
                    correction.corrected_bdd_framework.lower().strip()
                    != detected["bdd_framework"]
                ):
                    evidence.insert(
                        0,
                        f"❌ Your clarification is not supported by repository structure. Repo indicates framework '{detected['bdd_framework']}', but you claimed '{correction.corrected_bdd_framework}'.",
                    )
                    return {
                        "decision": "rejected",
                        "updated_detection": current,
                        "validation_source": "rule",
                        "evidence": evidence,
                    }

            # ✅ Safety guard: NEVER re-run detection unless correction matches repo language
            if correction.corrected_language != detected["language"]:
                return {
                    "decision": "rejected",
                    "updated_detection": current,
                    "validation_source": "rule",
                    "evidence": [
                        f"❌ Repository language is '{detected['language']}', not '{correction.corrected_language}'."
                    ],
                }
            # If we reach here, accept correction as valid (or repo is unknown/ambiguous)
            # We rerun detection but keep user_project_style possibly updated if user clarified language.
            new_intent = user_style
            if correction.corrected_language:
                if correction.corrected_language == "java":
                    new_intent = "java-selenium-bdd"
                elif correction.corrected_language == "python":
                    new_intent = "python-selenium-bdd"
                elif correction.corrected_language == "csharp":
                    new_intent = "csharp-selenium-bdd"

            new_out = self.run(
                ProjectDetectionInput(
                    user_project_style=new_intent,
                    input_type="repository",
                    input_path=inp.input_path,
                )
            ).model_dump()

            # Add acceptance evidence
            new_ev = list(new_out.get("evidence", []))
            new_ev.insert(
                0,
                "✅ You are correct. Identification updated based on your confirmation/clarification.",
            )
            new_out["evidence"] = new_ev

            return {
                "decision": "accepted",
                "updated_detection": new_out,
                "validation_source": "rule",
                "evidence": new_out.get("evidence", []),
            }

        # HTML report arbitration: cannot validate language; accept user confirmation
        # Update evidence to reflect acceptance and proceed with user-selected style
        evidence.insert(
            0,
            "✅ You are correct. For HTML reports, language/tool cannot be reliably inferred; proceeding based on your confirmation.",
        )
        updated_detection["evidence"] = evidence
        updated_detection["user_project_style"] = user_style

        return {
            "decision": "accepted",
            "updated_detection": updated_detection,
            "validation_source": "rule",
            "evidence": evidence,
        }


# LangGraph node (orchestration-ready)
def project_detection_node(state: Dict[str, Any]) -> Dict[str, Any]:
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

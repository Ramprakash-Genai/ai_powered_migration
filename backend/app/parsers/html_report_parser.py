import re
from pathlib import Path
from typing import Dict, List


_GHERKIN_STEP_RE = re.compile(r"^\s*(Given|When|Then|And|But)\b", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# Common words seen in reports
_SCENARIO_HINTS = [
    "Scenario:",
    "Scenario Outline:",
    "Test:",
    "Spec:",
    "Suite:",
]


def parse_html_report(html_path: str, max_bytes: int = 2_000_000) -> Dict:
    """
    Parse an HTML report file and extract:
      - report_type (allure/gauge/unknown)
      - steps (gherkin-like or step-like)
      - screenshots (img src references)
      - scenarios (best effort)
      - evidence list
      - confidence (rule-based)
    """
    p = Path(html_path).resolve()
    if not p.exists() or not p.is_file():
        return {
            "report_type": "unknown",
            "name": p.name,
            "steps": [],
            "screenshots": [],
            "scenarios": [],
            "evidence": ["Invalid html_report path (not found or not a file)"],
            "confidence": 0.0,
        }

    raw = p.read_bytes()[:max_bytes]
    text = raw.decode("utf-8", errors="ignore")

    lower = text.lower()
    report_type = "unknown"
    evidence: List[str] = []

    # Detect report type (best effort)
    if "allure" in lower or "allure-report" in lower:
        report_type = "allure"
        evidence.append("HTML contains 'allure' markers → likely Allure report")
    elif "gauge" in lower or "thoughtworks.gauge" in lower:
        report_type = "gauge"
        evidence.append("HTML contains 'gauge' markers → likely Gauge report")
    else:
        evidence.append("No explicit Allure/Gauge markers found → report_type=unknown")

    # Extract title for name hint
    title_match = _TITLE_RE.search(text)
    title = ""
    if title_match:
        title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        if title:
            evidence.append(f"Found HTML <title>: {title}")

    # Extract screenshot references
    screenshots = _IMG_SRC_RE.findall(text)
    screenshots = list(dict.fromkeys([s.strip() for s in screenshots if s.strip()]))
    if screenshots:
        evidence.append(f"Found {len(screenshots)} <img src> screenshot references")

    # Extract steps: line-based heuristic
    # Many reports embed steps as plain text; we scan visible-ish lines
    candidate_lines = [
        re.sub(r"\s+", " ", ln).strip()
        for ln in re.split(r"[\r\n]+", re.sub(r"<[^>]+>", "\n", text))
    ]
    candidate_lines = [ln for ln in candidate_lines if len(ln) >= 4]

    steps: List[str] = []
    scenarios: List[str] = []

    for ln in candidate_lines:
        if _GHERKIN_STEP_RE.match(ln):
            steps.append(ln)
        # fallback: common step patterns in reports
        elif ln.lower().startswith("step ") or ln.lower().startswith("steps "):
            steps.append(ln)
        # scenario hints
        for h in _SCENARIO_HINTS:
            if ln.startswith(h):
                scenarios.append(ln)
                break

    # Deduplicate, cap to avoid giant payload
    steps = list(dict.fromkeys(steps))[:300]
    scenarios = list(dict.fromkeys(scenarios))[:100]

    if steps:
        evidence.append(f"Extracted {len(steps)} step-like lines from HTML")
    else:
        evidence.append(
            "No gherkin/step-like lines extracted (HTML may be highly scripted)"
        )

    if scenarios:
        evidence.append(f"Extracted {len(scenarios)} scenario/test name hints")

    # Confidence (rule-based)
    score = 0.0
    if report_type != "unknown":
        score += 0.25
    if len(steps) > 0:
        score += 0.45
    if len(screenshots) > 0:
        score += 0.20
    if len(scenarios) > 0:
        score += 0.10
    confidence = round(min(score, 1.0), 2)

    name = title if title else p.name

    return {
        "report_type": report_type,
        "name": name,
        "steps": steps,
        "screenshots": screenshots,
        "scenarios": scenarios,
        "evidence": evidence,
        "confidence": confidence,
    }

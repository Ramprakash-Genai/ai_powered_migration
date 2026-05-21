import ast
from pathlib import Path
from typing import Dict, List

from app.models.project_migration_execution_input import MigrationExecutionInput
from services.blueverse_client import call_blueverse_agent


class ProjectMigrationExecutionAgent:
    def execute(self, payload: MigrationExecutionInput):

        if payload.execution_mode == "INITIAL_MIGRATION":
            return self._initial_migration(payload)

        if payload.execution_mode == "REVIEW_REPAIR":
            return self._review_repair(payload)

        # ✅ HTML: migrate one selected step (does NOT affect repo flow)
        if payload.execution_mode == "HTML_STEP_MIGRATION":
            return self._html_step_migration(payload)

        if payload.execution_mode == "FINALIZE_FILE":
            return self._finalize_file(payload)

        return {"error": True, "message": "Invalid execution mode"}

    # ---------------- INITIAL MIGRATION ----------------
    def _initial_migration(self, payload):

        source_root = Path(payload.source_repo_path)
        target_root = Path(payload.target_path) / payload.repo_name
        target_root.mkdir(parents=True, exist_ok=True)

        files = self._extract_files(payload.migration_plan or {})

        result_files = []

        for rel_path, category in files:
            if not rel_path:
                continue
            src_file = source_root / rel_path

            if not src_file.exists():
                continue

            original_code = src_file.read_text(encoding="utf-8", errors="ignore")

            # ✅ Heuristic safeguard: step definitions sometimes land in wrong category
            # If file path clearly indicates step definitions, force category="step"
            p_low = (rel_path or "").lower().replace("\\", "/")
            if category != "step" and (
                "/steps/" in p_low or "step" in Path(p_low).stem.lower()
            ):
                category = "step"

            # ✅ PATH MAPPING (same-language keeps structure; cross-language uses target standard)
            new_rel_path = self._map_path(rel_path, payload, category)
            tgt_file = target_root / new_rel_path
            tgt_file.parent.mkdir(parents=True, exist_ok=True)

            # ✅ FIX 2 — FEATURE FILE (DO NOT CONVERT)
            if rel_path.endswith(".feature"):
                migrated_code = original_code
                justification = "Feature file retained in Gherkin format"
                decision = "APPROVED"

            # ✅ DEPENDENCY FILE HANDLING (same-language keep as-is; cross-language convert)
            elif (
                Path(rel_path).name
                in [
                    "pom.xml",
                    "requirements.txt",
                ]
                or Path(rel_path).suffix.lower() == ".csproj"
            ):
                is_cross = payload.source_language != payload.target_language

                # SAME language → keep original dependency file content as-is
                if not is_cross:
                    migrated_code = original_code
                    justification = "Dependency file retained (same-language migration)"
                    decision = "APPROVED"

                # CROSS language → generate target dependency file content (minimal baseline)
                else:
                    new_rel_path = self._map_path(rel_path, payload, "config")
                    tgt_file = target_root / new_rel_path
                    tgt_file.parent.mkdir(parents=True, exist_ok=True)

                    migrated_code = self._generate_dependency_content(
                        payload, original_code
                    )

                    justification = "Dependency generated based on migration rules (language + bdd + tool)"
                    decision = "APPROVED"

            # ✅ STEP FILE MIGRATION
            else:
                agent_input = {
                    "execution_mode": "INITIAL_MIGRATION",
                    "source_language": payload.source_language,
                    "target_language": payload.target_language,
                    "source_bdd": payload.source_bdd,
                    "target_bdd": payload.target_bdd,
                    "original_source_code": original_code,
                }

                raw = call_blueverse_agent(agent_input)
                parsed = self._parse(raw)

                # ✅ FIX 4 — BDD FORMAT CORRECTION + SAFE FALLBACK
                migrated_code = parsed.get("migrated_code")

                # Fallback if model output is empty
                if not migrated_code or not str(migrated_code).strip():
                    migrated_code = original_code
                    decision = "DENIED"
                    justification = "Model returned empty output. Fallback applied."
                else:
                    # only apply formatting fixes on real model output
                    migrated_code = (
                        str(migrated_code).replace('"&lt;', '"{').replace('&gt;"', '}"')
                    )
                    justification = parsed.get("justification", "")
                    decision = parsed.get("decision", "APPROVED")

            result_files.append(
                {
                    "path": rel_path,
                    "status": "PENDING",
                    "original": original_code,
                    "migrated": migrated_code,
                    "justification": justification,
                    "decision": decision,  # ✅ FIXED
                    "target_path": str(tgt_file),
                }
            )
        return {
            "executionResult": {"status": "READY_FOR_REVIEW", "files": result_files}
        }

    # ---------------- REVIEW / REPAIR ----------------
    def _review_repair(self, payload):

        # ✅ FEATURE FILE FIX
        if payload.file_path.endswith(".feature"):
            resp = {
                "decision": "APPROVED",
                "migrated_code": payload.original_source_code,
                "justification": "Feature file must remain Gherkin format",
            }
            return {
                "agent_response": {
                    "decision": resp["decision"],
                    "migrated_code": resp["migrated_code"],
                    "justification": resp["justification"],
                }
            }

        agent_input = {
            "execution_mode": "REVIEW_REPAIR",
            "source_language": payload.source_language,
            "target_language": payload.target_language,
            "source_bdd": payload.source_bdd,
            "target_bdd": payload.target_bdd,
            "original_source_code": payload.original_source_code,
            "migrated_code": payload.migrated_code,
            "user_feedback": payload.user_feedback,
        }

        raw = call_blueverse_agent(agent_input)

        parsed = self._parse(raw)

        # ✅ SAFETY: fallback if parsing fails
        if not parsed.get("decision") or not parsed.get("migrated_code"):
            parsed = {
                "decision": "DENIED",
                "migrated_code": payload.migrated_code,
                "justification": "Agent response invalid or parsing failed. No changes applied.",
            }

        return {
            "agent_response": {
                "decision": parsed.get("decision"),
                "migrated_code": parsed.get("migrated_code"),
                "justification": parsed.get("justification"),
            }
        }

    # ---------------- HTML STEP MIGRATION ----------------

    def _html_step_migration(self, payload):

        step_text = payload.original_source_code or ""

        if not step_text.strip():
            return {"executionResult": {"status": "READY_FOR_REVIEW", "steps": []}}

        agent_input = {
            "execution_mode": "INITIAL_MIGRATION",
            "source_language": payload.source_language,
            "target_language": payload.target_language,
            "source_bdd": payload.source_bdd,
            "target_bdd": payload.target_bdd,
            "original_source_code": step_text,
        }

        raw = call_blueverse_agent(agent_input)
        parsed = self._parse(raw)

        return {
            "executionResult": {
                "status": "READY_FOR_REVIEW",
                "steps": [
                    {
                        "step": step_text,
                        "migrated": parsed.get("migrated_code", ""),
                        "justification": parsed.get("justification", ""),
                        "status": "PENDING",
                    }
                ],
            }
        }

    # ---------------- FINAL SAVE ----------------
    def _finalize_file(self, payload):
        target_root = Path(payload.target_path) / payload.repo_name
        target_root.mkdir(parents=True, exist_ok=True)

        # ✅ If frontend sends absolute target file path, write directly to it.
        # ✅ If frontend sends relative path, write under target_root.
        p = Path(payload.file_path)

        if p.is_absolute():
            out_file = p
        else:
            out_file = target_root / payload.file_path

        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(payload.migrated_code, encoding="utf-8")

        return {"status": "SUCCESS"}

    # ---------------- HELPERS ----------------
    def _extract_files(self, plan):
        """
        Returns a list of tuples: (rel_path, category)
        category ∈ {"feature", "step", "helper", "config"}
        """
        out = []

        section_map = {
            "feature_files": "feature",
            "step_definition_files": "step",
            "support_files": "helper",
            "config_files": "config",
        }

        for section, cat in section_map.items():
            for p in plan.get(section, {}).get("files", []) or []:
                if p:
                    out.append((p, cat))

        # de-dup while preserving first-seen category
        seen = {}
        for p, cat in out:
            if p not in seen:
                seen[p] = cat
        return [(p, seen[p]) for p in seen]

    def _generate_dependency_content(self, payload, original_code):
        src_lang = payload.source_language
        tgt_lang = payload.target_language
        src_bdd = payload.source_bdd
        tgt_bdd = payload.target_bdd

        is_same_lang = src_lang == tgt_lang
        is_same_bdd = src_bdd == tgt_bdd

        # ✅ STEP 1 — Parse source dependencies (basic)
        lines = original_code.splitlines()

        # ✅ STEP 2 — Initialize target deps container
        deps = []

        # ✅ STEP 3 — Rule-based handling
        if is_same_lang and is_same_bdd:
            deps.extend(self._remove_existing_playwright(lines))
            deps.append(self._get_playwright_dep(tgt_lang))

        elif is_same_lang and not is_same_bdd:
            deps.extend(self._filter_language_deps(lines, tgt_lang))
            deps.append(self._get_bdd_dep(tgt_lang, tgt_bdd))
            deps.append(self._get_playwright_dep(tgt_lang))

        elif not is_same_lang and is_same_bdd:
            deps.append(self._get_language_base(tgt_lang))
            deps.append(self._get_bdd_dep(tgt_lang, tgt_bdd))
            deps.append(self._get_playwright_dep(tgt_lang))

        else:
            deps.append(self._get_language_base(tgt_lang))
            deps.append(self._get_bdd_dep(tgt_lang, tgt_bdd))
            deps.append(self._get_playwright_dep(tgt_lang))

        if tgt_lang == "python":
            return "\n".join(deps)

        if tgt_lang == "java":
            return "<dependencies>\n" + "\n".join(deps) + "\n</dependencies>"

        if tgt_lang == "csharp":
            return (
                '<Project Sdk="Microsoft.NET.Sdk">\n'
                "  <ItemGroup>\n" + "\n".join(deps) + "\n  </ItemGroup>\n"
                "</Project>"
            )

    def _remove_existing_playwright(self, lines):
        return [l for l in lines if "playwright" not in l.lower()]

    def _get_playwright_dep(self, lang):
        if lang == "python":
            return "playwright==1.40.0"
        if lang == "java":
            return "<dependency>Playwright latest</dependency>"
        if lang == "csharp":
            return (
                '<PackageReference Include="Microsoft.Playwright" Version="1.40.0" />'
            )

    def _get_bdd_dep(self, lang, bdd):
        if lang == "python":
            if bdd == "pytest-bdd":
                return "pytest-bdd==6.1.1"
            if bdd == "behave":
                return "behave==1.2.6"
        if lang == "java":
            if bdd == "cucumber":
                return "<dependency>Cucumber latest</dependency>"
        if lang == "csharp":
            if bdd == "specflow":
                return '<PackageReference Include="SpecFlow" Version="3.9.74" />'

    def _get_language_base(self, lang):
        if lang == "python":
            return "pytest==7.4.3"
        if lang == "java":
            return "<!-- Java base dependencies -->"
        if lang == "csharp":
            return '<Project Sdk="Microsoft.NET.Sdk">'

    def _filter_language_deps(self, lines, lang):
        skip_keywords = ["cucumber", "specflow", "gauge", "pytest-bdd", "behave"]

        return [l for l in lines if not any(k in l.lower() for k in skip_keywords)]

    def _map_path(self, path, payload, category="config"):
        p = (path or "").replace("\\", "/")

        src_lang = payload.source_language
        tgt_lang = payload.target_language
        tgt_bdd = payload.target_bdd

        file_path = Path(p)
        name = file_path.name
        suffix = file_path.suffix.lower()

        # ✅ SAME LANGUAGE + SAME BDD → KEEP STRUCTURE
        if src_lang == tgt_lang and payload.source_bdd == payload.target_bdd:
            return p

        # ✅ FEATURE FILES (BDD-driven)
        if suffix == ".feature":
            if tgt_bdd == "pytest-bdd":
                return f"features/{name}"
            elif tgt_bdd == "cucumber":
                return f"src/test/resources/features/{name}"
            elif tgt_bdd == "gauge":
                return f"specs/{name}"
            return name

        # ✅ EXTENSION MAP
        ext_map = {"java": ".java", "python": ".py", "csharp": ".cs"}
        new_ext = ext_map.get(tgt_lang, suffix)
        base_name = file_path.stem + new_ext

        # ✅ STEP FILES (CRITICAL LOGIC)
        if category == "step":
            if tgt_bdd == "pytest-bdd":
                return f"tests/steps/{base_name}"
            elif tgt_bdd == "cucumber":
                if tgt_lang == "java":
                    return f"src/test/java/stepdefs/{base_name}"
                elif tgt_lang == "python":
                    return f"features/steps/{base_name}"
                elif tgt_lang == "csharp":
                    return f"StepDefinitions/{base_name}"
            elif tgt_bdd == "gauge":
                return f"step_implementation/{base_name}"

        # ✅ HELPERS
        if category == "helper":
            if tgt_bdd == "pytest-bdd":
                return f"tests/helpers/{base_name}"
            elif tgt_bdd == "cucumber":
                return f"src/test/java/utils/{base_name}"
            elif tgt_bdd == "gauge":
                return f"env/{base_name}"

        # ✅ CONFIG FILES (FIXED – TARGET BASED MAPPING)
        if category == "config":
            if name == "pom.xml":
                if tgt_lang == "python":
                    return "requirements.txt"
                elif tgt_lang == "csharp":
                    return f"{payload.repo_name}.csproj"
                else:
                    return "pom.xml"

            if name == "requirements.txt":
                if tgt_lang == "java":
                    return "pom.xml"
                elif tgt_lang == "csharp":
                    return f"{payload.repo_name}.csproj"
                else:
                    return "requirements.txt"

            if suffix == ".csproj":
                if tgt_lang == "python":
                    return "requirements.txt"
                elif tgt_lang == "java":
                    return "pom.xml"
                else:
                    return f"{payload.repo_name}.csproj"

        # ✅ DEFAULT
        return f"src/{base_name}"

    def _parse(self, raw):
        try:
            parsed = ast.literal_eval(raw.get("response", ""))

            # ✅ CLEAN ONLY REQUIRED FIELDS
            return {
                "decision": parsed.get("decision"),
                "migrated_code": parsed.get("migrated_code"),
                "justification": parsed.get("justification"),
            }
        except Exception:
            return {}

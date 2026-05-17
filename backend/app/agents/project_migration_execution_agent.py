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

        for rel_path in files:
            if not rel_path:
                continue
            src_file = source_root / rel_path
            if not src_file.exists():
                continue

            original_code = src_file.read_text(encoding="utf-8", errors="ignore")

            # ✅ FIX 1 — PATH MAPPING
            new_rel_path = self._map_path(rel_path, payload)
            tgt_file = target_root / new_rel_path
            tgt_file.parent.mkdir(parents=True, exist_ok=True)

            # ✅ FIX 2 — FEATURE FILE (DO NOT CONVERT)
            if rel_path.endswith(".feature"):
                migrated_code = original_code
                justification = "Feature file retained in Gherkin format"
                decision = "APPROVED"

            # ✅ FIX 3 — pom.xml → requirements.txt
            elif rel_path.endswith("pom.xml") and payload.target_language == "python":
                new_rel_path = "requirements.txt"
                tgt_file = target_root / new_rel_path

                migrated_code = "\n".join(
                    ["pytest==7.4.3", "pytest-bdd==6.1.1", "playwright==1.40.0"]
                )
                justification = "Converted pom.xml to requirements.txt"
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

                # ✅ FIX 4 — BDD FORMAT CORRECTION
                migrated_code = parsed.get("migrated_code", "")
                migrated_code = migrated_code.replace('"<', '"{').replace('>"', '}"')

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
            return {"agent_response": {"response": str(resp)}}

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

    # ---------------- FINAL SAVE ----------------
    def _finalize_file(self, payload):

        target_root = Path(payload.target_path) / payload.repo_name
        target_root.mkdir(parents=True, exist_ok=True)

        new_rel = self._map_path(payload.file_path, payload)
        out_file = target_root / new_rel
        out_file.parent.mkdir(parents=True, exist_ok=True)

        out_file.write_text(payload.migrated_code, encoding="utf-8")

        return {"status": "SUCCESS"}

    # ---------------- HELPERS ----------------
    def _extract_files(self, plan):
        files = []
        for section in [
            "feature_files",
            "step_definition_files",
            "support_files",
            "config_files",
        ]:
            files.extend(plan.get(section, {}).get("files", []))
        return list(set(files))

    def _map_path(self, path, payload):

        p = (path or "").replace("\\", "/")

        if payload.target_language == "python":
            # ✅ STEP FILES
            if "src/test/java" in p and p.endswith(".java"):
                name = Path(p).stem
                return f"tests/steps/{name}.py"

            # ✅ FEATURE FILES
            if "src/test/resources/features" in p and p.endswith(".feature"):
                return f"features/{Path(p).name}"

            # ✅ pom.xml → requirements.txt
            if p.endswith("pom.xml"):
                return "requirements.txt"

            # ✅ fallback
            if p.endswith(".feature"):
                return f"features/{Path(p).name}"

        return path

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

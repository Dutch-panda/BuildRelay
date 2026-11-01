"""Automated multi-dimensional deliverable evaluation and scoring harness for BuildRelay."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from contracts import (
    DeliverableEvaluationReport,
    DimensionEvaluation,
    TechnicalSpec,
)


class DeliverableEvaluator:
    """Evaluates generated workspaces across 5 rigorous engineering dimensions."""

    def __init__(
        self,
        workspace_path: Path | str,
        spec: TechnicalSpec | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        vault_dir: Path | str = "vault",
    ) -> None:
        self.workspace_path = Path(workspace_path).resolve()
        self.spec = spec
        self.vault_dir = Path(vault_dir).resolve()
        self.task_id = task_id or self._infer_task_id()
        self.project_id = project_id or getattr(spec, "project_id", None) or self._infer_project_id()

    def _infer_task_id(self) -> str:
        name = self.workspace_path.name
        if name.startswith("task-"):
            return name
        return f"task-{name}"

    def _infer_project_id(self) -> str | None:
        name = self.workspace_path.name
        if not name.startswith("task-"):
            return name
        return None

    def _get_all_files(self) -> list[Path]:
        """Collect all relevant files in workspace, ignoring caches and venvs."""
        if not self.workspace_path.is_dir():
            return []
        ignored_patterns = {
            ".git", "__pycache__", ".pytest_cache", ".venv", "venv",
            "node_modules", ".obsidian", ".state", ".coverage", ".DS_Store"
        }
        all_files: list[Path] = []
        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in ignored_patterns and not d.startswith(".")]
            for f in files:
                if f.startswith(".") and f != ".env" and f != ".gitignore":
                    continue
                all_files.append(Path(root) / f)
        return all_files

    def evaluate(self) -> DeliverableEvaluationReport:
        """Execute full 5-dimensional evaluation and return structured report."""
        if not self.workspace_path.is_dir() or not any(self.workspace_path.iterdir()):
            empty_dims = {
                "test_integrity": DimensionEvaluation(
                    dimension="test_integrity",
                    label="Test Integrity & Coverage",
                    score=0,
                    status="fail",
                    findings=["Workspace directory does not exist or contains no generated files."],
                    recommendations=["Run implementation to generate project deliverables before evaluation."],
                ),
                "security_sanitization": DimensionEvaluation(
                    dimension="security_sanitization",
                    label="Security & Sanitization",
                    score=0,
                    status="fail",
                    findings=["No workspace files to evaluate for security posture."],
                ),
                "ui_surface": DimensionEvaluation(
                    dimension="ui_surface",
                    label="UI Surface & Usability",
                    score=0,
                    status="fail",
                    findings=["No user input surface detected."],
                    recommendations=["Implement user entry point (e.g. form.html or interactive CLI)."],
                ),
                "live_verification": DimensionEvaluation(
                    dimension="live_verification",
                    label="Tier 2 Live Verification Readiness",
                    score=0,
                    status="fail",
                    findings=["No Tier 2 live verification scripts or checklists found."],
                    recommendations=["Add scripts/verify_live.py and README live verification checklist."],
                ),
                "architectural_conformance": DimensionEvaluation(
                    dimension="architectural_conformance",
                    label="Architectural Conformance & Hygiene",
                    score=0,
                    status="fail",
                    findings=["Workspace is missing or empty."],
                ),
            }
            return DeliverableEvaluationReport(
                task_id=self.task_id,
                project_id=self.project_id,
                overall_score=0,
                verdict="fail",
                dimensions=empty_dims,
                summary="Evaluation failed: Workspace directory is missing or empty.",
            )

        files = self._get_all_files()

        dim1 = self._eval_test_integrity(files)
        dim2 = self._eval_security_sanitization(files)
        dim3 = self._eval_ui_surface(files)
        dim4 = self._eval_live_verification(files)
        dim5 = self._eval_architectural_conformance(files)

        dimensions = {
            "test_integrity": dim1,
            "security_sanitization": dim2,
            "ui_surface": dim3,
            "live_verification": dim4,
            "architectural_conformance": dim5,
        }

        overall_score = sum(d.score for d in dimensions.values())
        if overall_score >= 85:
            verdict = "exceptional"
        elif overall_score >= 70:
            verdict = "pass"
        elif overall_score >= 50:
            verdict = "marginal"
        else:
            verdict = "fail"

        summary = self._generate_summary(overall_score, verdict, dimensions)

        return DeliverableEvaluationReport(
            task_id=self.task_id,
            project_id=self.project_id,
            overall_score=overall_score,
            verdict=verdict,
            dimensions=dimensions,
            summary=summary,
        )

    def _eval_test_integrity(self, files: list[Path]) -> DimensionEvaluation:
        """Evaluate Dimension 1: Test Integrity & Coverage (Max 20 pts)."""
        score = 0
        findings: list[str] = []
        recommendations: list[str] = []

        test_files = [
            f for f in files
            if (
                f.name.startswith("test_")
                or f.name.endswith("_test.py")
                or f.name == "tests.py"
                or f.name.endswith(".test.js")
                or f.name.endswith(".spec.js")
                or f.name.endswith(".test.ts")
                or f.name.endswith(".spec.ts")
                or "tests" in f.parts
                or "test" in f.parts
            )
            and f.suffix in {".py", ".js", ".ts", ".gs"}
        ]

        if not test_files:
            return DimensionEvaluation(
                dimension="test_integrity",
                label="Test Integrity & Coverage",
                score=0,
                status="fail",
                findings=["No automated test files found in workspace (expected tests/ or test_*.py)."],
                recommendations=["Create automated unit tests verifying business logic and edge cases."],
            )

        score += 5
        findings.append(f"Detected {len(test_files)} test suite file(s).")

        total_assertions = 0
        trivial_assertions = 0
        has_edge_cases = False
        has_mocks = False

        for tf in test_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Non-trivial assertions
            py_assertions = len(re.findall(r"\bassert\b", content))
            js_assertions = len(re.findall(r"\bexpect\(|assert\.", content))
            total_assertions += (py_assertions + js_assertions)

            # Trivial assertion detection
            if re.search(r"\bassert\s+(?:True|1\s*==\s*1|not\s+False)\b", content):
                trivial_assertions += 1

            # Edge case & error checking
            if re.search(r"pytest\.raises|assertRaises|\.toThrow|\.rejects|ValueError|TypeError|None|null|\"\"|-1|boundary|invalid|empty", content, re.IGNORECASE):
                has_edge_cases = True

            # Mock fixtures & offline service isolation
            if re.search(r"unittest\.mock|MagicMock|Mock\(|monkeypatch|jest\.fn|mock_response|mock_sheet|fake|fixture", content, re.IGNORECASE):
                has_mocks = True

        if trivial_assertions > 0:
            score -= 3
            findings.append("Detected trivial assertions (e.g. assert True) with no real verification.")
            recommendations.append("Replace trivial assertion placeholders with concrete output verifications.")

        if total_assertions >= 5:
            score += 5
            findings.append(f"Strong assertion volume: {total_assertions} assertion check(s) across test suites.")
        elif total_assertions >= 1:
            score += 3
            findings.append(f"Moderate assertion volume: {total_assertions} assertion check(s).")
            recommendations.append("Expand test assertions to cover multiple function branches.")
        else:
            findings.append("Test files present but zero assertion statements detected.")
            recommendations.append("Add explicit assert or expect checks to test suites.")

        if has_edge_cases:
            score += 5
            findings.append("Edge case and exception handling verified (boundary inputs, error conditions).")
        else:
            recommendations.append("Add negative and edge-case unit tests (e.g. empty payloads, invalid types, boundary values).")

        if has_mocks:
            score += 5
            findings.append("Deterministic offline mock adapters & fixtures implemented.")
        else:
            findings.append("Tests do not use mock fixtures for external services.")
            recommendations.append("Use mock service adapters to isolate tests from network/cloud dependencies.")

        score = max(0, min(20, score))
        status = "excellent" if score >= 18 else "good" if score >= 14 else "marginal" if score >= 10 else "fail"
        return DimensionEvaluation(
            dimension="test_integrity",
            label="Test Integrity & Coverage",
            score=score,
            status=status,
            findings=findings,
            recommendations=recommendations,
        )

    def _eval_security_sanitization(self, files: list[Path]) -> DimensionEvaluation:
        """Evaluate Dimension 2: Security & Sanitization (Max 20 pts)."""
        score = 20
        findings: list[str] = []
        recommendations: list[str] = []

        code_files = [f for f in files if f.suffix in {".py", ".js", ".ts", ".gs", ".html", ".sh"}]

        # 1. Formula Injection Defenses
        has_tabular_writer = False
        has_formula_defense = False
        for cf in code_files:
            try:
                content = cf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if re.search(r"csv\.writer|to_csv|appendRow|getRange|setValue|write_records|write_csv|export_csv", content):
                has_tabular_writer = True
                if re.search(r"startswith\s*\(\s*['\"][\=\+\-\@\|\%]|\b(?:formula_guard|sanitize_cell|sanitize_formula|escape_formula)\b|['\"]\'+['\"]\s*\+\s*str", content):
                    has_formula_defense = True

        if has_tabular_writer:
            if has_formula_defense:
                findings.append("Formula injection defense verified: cell prefixes (=, +, -, @) are sanitized before export.")
            else:
                score -= 6
                findings.append("Formula injection vulnerability: tabular/spreadsheet data written without sanitizing prefix characters (=, +, -, @).")
                recommendations.append("Sanitize tabular exports by prefixing formula triggers (=, +, -, @, \\t, \\r) with a single quote or stripping them.")
        else:
            findings.append("No active tabular/spreadsheet writers detected; zero formula injection surface.")

        # 2. Secret & Token Leak Scans
        hardcoded_secrets: list[str] = []
        secret_patterns = [
            (r"\bsk-[a-zA-Z0-9]{20,}\b", "OpenAI API Key"),
            (r"\bghp_[a-zA-Z0-9]{36}\b", "GitHub Personal Token"),
            (r"\bAIza[0-9A-Za-z-_]{35}\b", "Google API Key"),
            (r"Bearer\s+[a-zA-Z0-9_\-\.]{25,}", "Bearer Token"),
            (r"(?:api_key|secret_key|auth_token)\s*=\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "Hardcoded API Secret"),
        ]

        for cf in code_files:
            if cf.name == ".env" or "mock" in cf.name.lower() or "fixture" in cf.name.lower():
                continue
            try:
                content = cf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat, sec_name in secret_patterns:
                if re.search(pat, content):
                    hardcoded_secrets.append(f"{sec_name} in {cf.name}")

        if hardcoded_secrets:
            score -= 8
            findings.append(f"CRITICAL SECURITY RISK: Hardcoded secret(s) detected: {', '.join(hardcoded_secrets)}.")
            recommendations.append("Immediately move all tokens, passwords, and API keys to environment variables.")
        else:
            findings.append("No leaked credentials or hardcoded secret keys detected.")

        # 3. Environment Variable & Gitignore Hygiene
        env_files = [f for f in files if f.name == ".env"]
        gitignore = self.workspace_path / ".gitignore"

        if env_files:
            if gitignore.is_file():
                git_text = gitignore.read_text(encoding="utf-8", errors="ignore")
                if ".env" in git_text:
                    findings.append("Environment secrets hygiene verified: .env is gitignored.")
                else:
                    score -= 4
                    findings.append(".env exists in workspace but is not excluded in .gitignore.")
                    recommendations.append("Add .env to .gitignore to prevent accidental credential commits.")
            else:
                score -= 2
                findings.append(".env exists in workspace without a .gitignore file.")
                recommendations.append("Create a .gitignore file excluding .env.")
        else:
            findings.append("Configured environment secrets follow safe isolation patterns.")

        score = max(0, min(20, score))
        status = "excellent" if score >= 18 else "good" if score >= 14 else "marginal" if score >= 10 else "fail"
        return DimensionEvaluation(
            dimension="security_sanitization",
            label="Security & Sanitization",
            score=score,
            status=status,
            findings=findings,
            recommendations=recommendations,
        )

    def _eval_ui_surface(self, files: list[Path]) -> DimensionEvaluation:
        """Evaluate Dimension 3: UI Surface & Usability (Max 20 pts)."""
        score = 0
        findings: list[str] = []
        recommendations: list[str] = []

        html_forms = [
            f for f in files
            if f.suffix == ".html" or f.name in {"form.html", "web-entry.html", "index.html"}
        ]
        cli_entry = [
            f for f in files
            if f.suffix == ".py" and re.search(r"input\(|argparse|click|inquirer", f.read_text(encoding="utf-8", errors="ignore") if f.is_file() else "")
        ]

        if not html_forms and not cli_entry:
            return DimensionEvaluation(
                dimension="ui_surface",
                label="UI Surface & Usability",
                score=4,
                status="fail",
                findings=["No user input surface detected: Missing web form (form.html) and interactive CLI input wizard."],
                recommendations=["Build a dedicated user entry point (e.g. form.html or interactive CLI) with validation."],
            )

        if html_forms:
            score += 8
            findings.append(f"Web input surface detected ({', '.join(f.name for f in html_forms)}).")

            has_inputs = False
            has_validation = False
            has_styling = False
            has_feedback = False

            for hf in html_forms:
                try:
                    text = hf.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                if re.search(r"<form|<input|<select|<textarea", text, re.IGNORECASE):
                    has_inputs = True
                if re.search(r"required|pattern=|type=[\"'](?:email|number|date)[\"']|min=|max=|validateForm", text, re.IGNORECASE):
                    has_validation = True
                if re.search(r"tailwindcss|class=[\"'][^\"']+[\"']|<style>|stylesheet", text, re.IGNORECASE):
                    has_styling = True
                if re.search(r"alert|toast|message|feedback|success|error-banner", text, re.IGNORECASE):
                    has_feedback = True

            if has_inputs:
                score += 3
                findings.append("Form elements and input fields properly configured.")
            if has_validation:
                score += 4
                findings.append("Client-side validation enforced (required fields, typed inputs).")
            else:
                recommendations.append("Add client-side form validation (required attributes, pattern constraints, input types).")

            if has_styling:
                score += 3
                findings.append("Responsive styling and clean visual design applied.")
            else:
                recommendations.append("Apply responsive styling (e.g. Tailwind CSS) for better usability.")

            if has_feedback:
                score += 2
                findings.append("Interactive user feedback elements (alerts, submission notifications) present.")
            else:
                recommendations.append("Add interactive submission confirmation and error notification banners.")

        elif cli_entry:
            score += 12
            findings.append("Interactive CLI user input surface detected.")
            # Check validation in CLI
            has_cli_val = any(
                re.search(r"try:|except\s+(?:ValueError|KeyError)|if\s+not\s+\w+:|sys\.exit", f.read_text(encoding="utf-8", errors="ignore"))
                for f in cli_entry
            )
            if has_cli_val:
                score += 5
                findings.append("CLI input validation and error feedback implemented.")
            else:
                recommendations.append("Add input validation guards and helpful error messages to CLI prompts.")

        score = max(0, min(20, score))
        status = "excellent" if score >= 18 else "good" if score >= 14 else "marginal" if score >= 10 else "fail"
        return DimensionEvaluation(
            dimension="ui_surface",
            label="UI Surface & Usability",
            score=score,
            status=status,
            findings=findings,
            recommendations=recommendations,
        )

    def _eval_live_verification(self, files: list[Path]) -> DimensionEvaluation:
        """Evaluate Dimension 4: Tier 2 Live Verification Readiness (Max 20 pts)."""
        score = 0
        findings: list[str] = []
        recommendations: list[str] = []

        smoke_scripts = [
            f for f in files
            if (
                f.name in {"verify_live.py", "verify.py", "verify.js", "verify_live.sh", "smoke_test.py"}
                or (f.parent.name == "scripts" and "verify" in f.name.lower())
            )
        ]
        has_apps_script_smoke = any(
            re.search(r"function\s+testDirectSync|function\s+smokeTest", f.read_text(encoding="utf-8", errors="ignore"))
            for f in files if f.name == "Code.gs"
        )

        if smoke_scripts or has_apps_script_smoke:
            score += 8
            script_names = [f.name for f in smoke_scripts] + (["Code.gs testDirectSync"] if has_apps_script_smoke else [])
            findings.append(f"Dedicated Tier 2 live verification smoke script available ({', '.join(script_names)}).")

            # Check for env decoupling
            loads_env = False
            for sf in smoke_scripts:
                try:
                    text = sf.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"os\.environ|process\.env|dotenv|get_project_env", text):
                        loads_env = True
                except Exception:
                    continue

            if loads_env or has_apps_script_smoke:
                score += 6
                findings.append("Live verification script decouples secrets (loads live credentials from environment/.env).")
            else:
                findings.append("Live verification script does not appear to load environment variables.")
                recommendations.append("Ensure verify_live.py reads live credentials from environment variables.")
        else:
            findings.append("No dedicated Tier 2 live verification smoke script detected (e.g. scripts/verify_live.py).")
            recommendations.append("Generate scripts/verify_live.py to smoke test against real external endpoints.")

        # Check README checklist
        readme_file = self.workspace_path / "README.md"
        if readme_file.is_file():
            readme_text = readme_file.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"live\s+verification|tier\s*2|verification\s+checklist|how\s+to\s+verify", readme_text, re.IGNORECASE):
                if re.search(r"(?:1\.|2\.|\[\s*\]|\-\s*\[\s*\])", readme_text):
                    score += 6
                    findings.append("README contains structured, actionable Tier 2 Live Verification checklist.")
                else:
                    score += 3
                    findings.append("README mentions live verification but lacks a numbered step-by-step checklist.")
                    recommendations.append("Add a numbered checklist with concrete commands and expected outputs to README.md.")
            else:
                recommendations.append("Add a 'Live Verification Checklist' section to README.md guiding human verification.")
        else:
            findings.append("Missing README.md in workspace.")
            recommendations.append("Create README.md with clear live verification steps and run instructions.")

        score = max(0, min(20, score))
        status = "excellent" if score >= 18 else "good" if score >= 14 else "marginal" if score >= 10 else "fail"
        return DimensionEvaluation(
            dimension="live_verification",
            label="Tier 2 Live Verification Readiness",
            score=score,
            status=status,
            findings=findings,
            recommendations=recommendations,
        )

    def _eval_architectural_conformance(self, files: list[Path]) -> DimensionEvaluation:
        """Evaluate Dimension 5: Architectural Conformance & Hygiene (Max 20 pts)."""
        score = 0
        findings: list[str] = []
        recommendations: list[str] = []

        # 1. Separation of Concerns
        has_src = any("src" in f.parts for f in files)
        has_tests = any("tests" in f.parts or "test" in f.parts or f.name.startswith("test_") for f in files)
        has_readme = (self.workspace_path / "README.md").is_file()

        if has_tests and (has_src or len(files) <= 5):
            score += 6
            findings.append("Clean separation of concerns between source modules and automated tests.")
        else:
            score += 3
            findings.append("Partial project structure organization.")
            recommendations.append("Organize workspace into src/, tests/, and scripts/ directories.")

        # 2. Living Project Profile Memory
        profile_file = self.workspace_path / "PROJECT_PROFILE.md"
        if profile_file.is_file():
            score += 5
            findings.append("Living memory document (PROJECT_PROFILE.md) maintained in project workspace.")
        elif self.project_id:
            findings.append("Project workspace missing living PROJECT_PROFILE.md memory.")
            recommendations.append("Maintain PROJECT_PROFILE.md documenting active schemas and entry surfaces.")
        else:
            score += 5  # Standalone tasks are not penalized for omitting profile

        # 3. README Documentation Quality
        if has_readme:
            readme_text = (self.workspace_path / "README.md").read_text(encoding="utf-8", errors="ignore")
            if re.search(r"run|test|docker|usage|installation", readme_text, re.IGNORECASE):
                score += 5
                findings.append("README provides setup, run, and test instructions.")
            else:
                score += 2
                recommendations.append("Expand README.md with detailed run commands and Docker instructions.")
        else:
            recommendations.append("Create workspace README.md documenting architecture and execution.")

        # 4. Spec Conformance (if spec provided)
        if self.spec and self.spec.phases:
            all_found = True
            for phase in self.spec.phases:
                # Check if command or keywords have related files
                words = re.findall(r"\b[a-zA-Z0-9_\-]+\.(?:py|js|ts|html|sh|gs)\b", phase.validation_command + " " + phase.instructions)
                for w in words:
                    if not any(f.name == w for f in files):
                        all_found = False
                        break
            if all_found:
                score += 4
                findings.append("Delivered code conforms to architectural phases in TechnicalSpec.")
            else:
                score += 2
                findings.append("Minor divergence between TechnicalSpec execution phases and delivered files.")
        else:
            score += 4

        score = max(0, min(20, score))
        status = "excellent" if score >= 18 else "good" if score >= 14 else "marginal" if score >= 10 else "fail"
        return DimensionEvaluation(
            dimension="architectural_conformance",
            label="Architectural Conformance & Hygiene",
            score=score,
            status=status,
            findings=findings,
            recommendations=recommendations,
        )

    def _generate_summary(
        self,
        overall_score: int,
        verdict: str,
        dimensions: dict[str, DimensionEvaluation],
    ) -> str:
        strengths: list[str] = []
        gaps: list[str] = []
        for d in dimensions.values():
            if d.score >= 18:
                strengths.append(d.label)
            elif d.score < 14:
                gaps.append(d.label)

        summary_parts = [
            f"Deliverable scored {overall_score}/100 with verdict '{verdict.upper()}'."
        ]
        if strengths:
            summary_parts.append(f"Exemplary engineering in: {', '.join(strengths)}.")
        if gaps:
            summary_parts.append(f"Actionable improvements needed in: {', '.join(gaps)}.")
        return " ".join(summary_parts)

    def save_report(self, report: DeliverableEvaluationReport) -> Path:
        """Persist evaluation report to vault/evaluations/eval-<task_id>.md."""
        evals_dir = self.vault_dir / "evaluations"
        report_path = evals_dir / f"eval-{report.task_id}.md"

        content = [
            f"# Deliverable Evaluation Report: {report.task_id}\n",
            f"- **Task ID:** `{report.task_id}`",
            f"- **Project ID:** `{report.project_id or 'standalone'}`",
            f"- **Evaluated At:** `{report.timestamp}`",
            f"- **Overall Score:** **{report.overall_score} / 100**",
            f"- **Verdict:** **{report.verdict.upper()}**\n",
            "## Executive Summary\n",
            f"{report.summary}\n",
            "## Dimension Scorecard\n",
            "| Dimension | Score | Status | Key Findings |",
            "| :--- | :---: | :---: | :--- |",
        ]

        for d in report.dimensions.values():
            primary_finding = d.findings[0] if d.findings else "No issues detected"
            content.append(f"| {d.label} | {d.score}/20 | {d.status.upper()} | {primary_finding} |")

        content.append("\n## Detailed Diagnostic Findings\n")
        for d in report.dimensions.values():
            content.append(f"### {d.label} ({d.score}/20 - {d.status.upper()})\n")
            if d.findings:
                content.append("**Findings:**")
                for f in d.findings:
                    content.append(f"- {f}")
                content.append("")
            if d.recommendations:
                content.append("**Recommendations:**")
                for r in d.recommendations:
                    content.append(f"- {r}")
                content.append("")

        all_recommendations: list[str] = []
        for d in report.dimensions.values():
            all_recommendations.extend(d.recommendations)

        if all_recommendations:
            content.append("## Consolidated Actionable Recommendations\n")
            for idx, rec in enumerate(all_recommendations, 1):
                content.append(f"{idx}. {rec}")
            content.append("")

        report_text = "\n".join(content)
        try:
            evals_dir.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_text, encoding="utf-8")
        except OSError:
            try:
                fallback_path = Path("/tmp") / f"eval-{report.task_id}.md"
                fallback_path.write_text(report_text, encoding="utf-8")
                return fallback_path
            except OSError:
                pass

        return report_path

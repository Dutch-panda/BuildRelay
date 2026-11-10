from __future__ import annotations

import asyncio
import re
from typing import Any, Callable
from pathlib import Path
from datetime import datetime
from pydantic_ai import Agent
from pydantic_ai.models import Model
from contracts import ExecutionPhase, TechnicalSpec, UIDesignSpec, UIFieldSpec, UIPrototypeResult
from tools.graphify_tool import GraphifyVaultManager
from tools.project_notes import prepare_project
from tools.vault_infra import (
    register_graph_tools,
    register_note_writer_tool,
    update_vault_graph,
)
from tools.ui import print_agent

class TaghiArchitect:
    def __init__(
        self,
        vault_path: str | Path = "./vault",
        model_name: str | Model = "openai-chat:gpt-4o",
        graph_manager: GraphifyVaultManager | None = None,
        specs_dir: str | Path | None = None,
        research_dir: str | Path | None = None,
    ):
        self.vault_path = Path(vault_path)
        self.model_name = model_name
        self.specs_dir = Path(specs_dir) if specs_dir is not None else self.vault_path / "specs"
        self.research_dir = Path(research_dir) if research_dir is not None else self.vault_path / "research"
        self.graph_manager = graph_manager or GraphifyVaultManager(vault_path=str(self.vault_path))

        self.agent = Agent(
            model_name,
            output_type=TechnicalSpec,
            model_settings={"cache": True},
            system_prompt=(
                "You are Taghi, Technical Design Lead. Verify that the task is designated for design/architecture. "
                "Translate research reports into precise technical specifications and sequential execution phases for Meti. "
                "Select a suitable Docker base_image for the required runtime (e.g. 'python:3.11-slim' for Python tasks, "
                "'node:18-bullseye-slim' for Node/JS/TS, or an appropriate slim image).\n\n"
                "CRITICAL EXECUTION CONSTRAINTS FOR METI SANDBOX:\n"
                "- Meti executes and validates all phases autonomously inside an isolated Docker container without host credentials or live external API keys.\n"
                "- Every phase in 'phases' MUST be fully executable and verifiable inside the container environment using offline test suites, fixtures, or mock adapters.\n"
                "- You MUST ALWAYS emit at least 1 and up to 5 concrete, actionable execution phases in 'phases'. An empty 'phases' list is strictly prohibited and breaks execution.\n"
                "- If the task involves third-party services or private APIs where no credentials or endpoints are provided in the brief, specify modular mock implementations and offline test suites.\n"
                "- NEVER emit speculative, conditional, or blocked phases (e.g., 'Phase 5: authorized-source-integration-gate') that require unprovided credentials, live network access, or manual approvals. "
                "Document production prerequisites and future live integration gates exclusively in 'architecture_overview', NEVER as an ExecutionPhase.\n\n"
                "MANDATORY WORKING APPLICATION & EXECUTABLE CODE INVARIANT:\n"
                "- When the user requests to build, create, or refactor an application, you MUST architect concrete, executable backend code (e.g. backend server 'app.py', real database persistence like SQLite, API endpoints, working form handlers, and offline test suites).\n"
                "- Emitting phases that only write design documentation, fixture JSON, unapproved decision tables, or passive mock previews while omitting the actual working backend code and persistence is STRICTLY PROHIBITED.\n"
                "- The user at the keyboard IS the stakeholder. Gate approval constitutes complete authorization. NEVER create phases or documentation declaring decisions 'UNAPPROVED' or deferring implementation pending external sign-offs.\n\n"
                "USER-FIRST DELIVERY & DOCUMENTATION MANDATE:\n"
                "- The final documentation/delivery phase MUST instruct creation of a project README.md designed for end-users with zero cognitive friction.\n"
                "- The README.md MUST include: (1) an intuitive visual architecture or data flow diagram (ASCII or Mermaid), (2) a zero-jargon, step-by-step Quickstart guide explaining exactly how to run or deploy the result in simple numbered steps, and (3) concrete examples.\n"
                "- If a project requires user-provided configuration (e.g. spreadsheet URLs, API tokens, column mappings, or database paths), DO NOT leave passive markdown questionnaires or expect raw JSON editing: mandate an interactive CLI setup script (e.g. 'scripts/setup.js' or 'setup.py') that guides the user interactively in plain English.\n\n"
                "MANDATORY USER INPUT SURFACE & ENTRY POINT PHASE:\n"
                "- Scale execution phases flexibly based on the project scope and outcome-driven intent:\n"
                "  - Simple CLI / Local Utility: 1 phase with executable script and offline tests (e.g. '1-core-implementation').\n"
                "  - Interactive Form with Persistence: 2 to 3 phases (e.g. backend/storage, frontend UI, verification).\n"
                "  - Complex Multi-service: up to 5 phases.\n"
                "- When the task involves user-facing input surfaces, web forms, dashboards, or transaction workflows:\n"
                "  1. Backend Core First: Database models, schemas, formula injection sanitizers, and deterministic unit tests.\n"
                "  2. Frontend UI/UX Integration: Phase ordering coordinates with UI design specifications generated by Diba (or standard form surfaces) with deterministic backend validation.\n"
                "  3. Live Verification & Delivery Third: Tier 2 Live Verification Smoke Script ('scripts/verify_live.py') and README Live Checklist.\n"
                "- ARCHITECTURAL FOCUS (NO UI/UX RESPONSIBILITY):\n"
                "  Focus strictly on backend architecture: database schemas, API routes, data validation, error handling, storage lifecycles, and Docker verification phases.\n"
                "  Do NOT design visual layouts, Tailwind color palettes, component wireframes, or interactive UI states. All UI/UX design is handled exclusively by Diba.\n\n"
                "ARCHITECTURAL GRILL-ME & BACKEND CONTRACTS (PLAIN-ENGLISH USER DECISIONS):\n"
                "- Always populate 'input_interface_spec' with concrete field types and backend validation constraints.\n"
                "- Formulate up to 10 targeted 'clarification_questions' (strictly <= 10). "
                "  MANDATORY NON-TECHNICAL PLAIN-ENGLISH MANDATE:\n"
                "  Questions MUST be written in simple, zero-jargon plain English designed for a non-technical product owner or user.\n"
                "  DO NOT use engineering jargon like 'idempotency keys', 'ephemeral SQLite', 'REST error envelopes', 'ACID transactions', or '422 Unprocessable Entity'.\n"
                "  Instead, translate technical concepts into practical, everyday user choices and business consequences:\n"
                "  1. Data Storage: Ask whether saved records should stay permanently on the computer across restarts or if this is temporary during the active session.\n"
                "  2. Accidental / Duplicate Actions: Ask what should happen if a user accidentally double-clicks or re-submits (e.g. ignore duplicate, update existing, or alert user).\n"
                "  3. Errors & Feedback: Ask how errors should appear to the user (e.g. friendly popup warning vs. automatic background retry).\n"
                "  Every question MUST provide 2 to 4 numbered options in plain language with exactly one marked is_default=True.\n\n"
                "TWO-TIER VERIFICATION ARCHITECTURE & SPECIFICATION MANDATE:\n"
                "1. Tier 1 (Automated Docker Validation):\n"
                "   - All execution phases executed by Meti inside Docker MUST use deterministic unit tests, fixtures, and mock service adapters (e.g. mock SpreadsheetApp, mock REST API responses).\n"
                "   - Docker tests validate 100% offline with zero external network or secrets required.\n"
                "   - Standard Library Offline Fallback: When using slim or standard base images (e.g. python:3.11-slim) without pre-vendored packages, specify that the implementation should use standard library primitives (e.g. Python http.server/wsgiref/sqlite3) for web/data services so tests run 100% offline without requiring external wheelhouses.\n"
                "2. Tier 2 (Guided Live Environment Verification):\n"
                "   - Always populate 'live_verification_guide' with a clear, step-by-step checklist explaining how the user verifies against their real environment (e.g. Google Sheets, live webhooks, real database).\n"
                "   - Mandate in the final delivery phase that Meti builds a dedicated live smoke-test script (e.g. 'scripts/verify_live.py' or Apps Script 'testDirectSync()') and includes the Live Verification Checklist in the project README.md.\n\n"
                "CONTINUOUS FEATURE ITERATION & INCREMENTAL DEVELOPMENT:\n"
                "- When working within an existing project workspace with previous task history, architect phases that build on and integrate with existing files and tests.\n"
                "- Ensure new phases do not break existing validation commands or overwrite existing user configurations."
            ),
        )
        # --- BINDING TOOLS TO Taghi ---
        register_graph_tools(self.agent, self.graph_manager, "Taghi")
        register_note_writer_tool(
            self.agent,
            self.specs_dir,
            tool_name="write_specs_note",
            category="Specs",
            directory_name="Specs",
            agent_name="Taghi",
        )

    def ingest_prototype_contracts(self, prototype: UIPrototypeResult | None, workspace_dir: str | Path | None = None) -> list[str]:
        """
        Parses an approved UI prototype HTML to extract input field names, IDs, types, and form submission targets.
        Ensures Taghi's backend models match the verified UI frontend interface.
        """
        fields_found: list[str] = []
        html_text = ""
        if prototype and prototype.html_content:
            html_text = prototype.html_content
        elif workspace_dir:
            ws_proto = Path(workspace_dir) / "prototype.html"
            if ws_proto.is_file():
                html_text = ws_proto.read_text(encoding="utf-8")

        if not html_text:
            return fields_found

        # Extract input/textarea/select tags
        input_patterns = [
            r'<(?:input|textarea|select)[^>]+(?:name|id)=["\']([^"\']+)["\']',
            r'formData\.get\(["\']([^"\']+)["\']\)',
        ]
        for pat in input_patterns:
            matches = re.findall(pat, html_text, re.IGNORECASE)
            for m in matches:
                clean_name = m.strip()
                if clean_name and clean_name not in fields_found and not clean_name.startswith("prototype-"):
                    fields_found.append(clean_name)
        return fields_found

    async def create_specification(
        self,
        task_id: str,
        research_summary: str,
        project_id: str | None = None,
        prototype: UIPrototypeResult | None = None,
    ) -> TechnicalSpec:
        print_agent("taghi", f"Designing technical architecture and roadmap for task: {task_id}")

        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", task_id):
            raise ValueError("Task ID must contain only letters, digits, underscores, or hyphens")
        project = prepare_project(self.vault_path, project_id)
        workspace_dir = project_id or task_id
        incremental_header = ""
        if project.profile_text and ("## Task History" in project.profile_text or "## Active Data Schema" in project.profile_text):
            incremental_header = (
                "[INCREMENTAL ARCHITECTURE SPECIFICATION]\n"
                f"This specification extends existing project '{workspace_dir}'. "
                "Do not regenerate existing baseline boilerplate if already present in the workspace. "
                "Focus new phases on implementing and validating the requested features or refactorings.\n\n"
            )
        directory_instruction = f"Create your project directory at workspace/{workspace_dir}/ and place all modules there."
        
        # Ingest prototype contracts if prototype is provided or present in workspace
        proto_fields = self.ingest_prototype_contracts(prototype, workspace_dir=Path("./workspace") / workspace_dir)
        prototype_contract_section = ""
        if proto_fields:
            prototype_contract_section = (
                "\n[APPROVED UI PROTOTYPE CONTRACT]\n"
                f"An upfront Zero-to-One interactive prototype has been approved with fields: {proto_fields}.\n"
                "MANDATE: Backend API models, route handlers, and schemas MUST directly match these field names and types.\n"
                "Meti will wire the backend into this verified prototype without rewriting the UI.\n\n"
            )
        
        prior_art_section = ""
        if self.graph_manager and hasattr(self.graph_manager, "query_by_keywords"):
            try:
                from tools.taxonomy import extract_keywords
                keywords = extract_keywords(f"{task_id} {research_summary}")
                if keywords:
                    matches = self.graph_manager.query_by_keywords(keywords, top_k=3, min_score=0.20)
                    prior_matches = [
                        (n, s) for n, s in matches
                        if n.get("id") != task_id
                        and not str(n.get("id", "")).startswith(f"task-{task_id}")
                        and not str(n.get("id", "")).startswith(f"spec-{task_id}")
                    ]
                    if prior_matches:
                        prior_lines = [
                            f"- `{n.get('id')}` (Relevance: {s:.2f}, Domain: {n.get('domain', 'core')}): {n.get('label', '')}"
                            for n, s in prior_matches
                        ]
                        prior_art_section = "### Prior Art Discovered in Knowledge Graph\n" + "\n".join(prior_lines) + "\n\n"
            except Exception:
                pass

        prompt = (
            f"Task ID: {task_id}\n{incremental_header}{prototype_contract_section}{project.prompt}{prior_art_section}Research Summary/Findings: {research_summary}\n\n"
            f"Include this instruction in the specification: {directory_instruction}\n"
            f"All sandbox commands start in /app/workspace/{workspace_dir}/. "
            "Keep source files, tests, documentation, validation scripts, and dependencies in this project directory. "
            "Write validation commands relative to this directory or using its absolute container path.\n"
            "Execution Rule: All phases in 'phases' must be actionable and fully verifiable offline within the container. "
            "You MUST emit at least 1 and up to 5 ordered execution phases in 'phases'. An empty 'phases' list is strictly prohibited. "
            "Do NOT include conditional or blocked phases that depend on unprovided credentials or external authorization; "
            "place any unverified external prerequisites or live deployment notes in architecture_overview."
        )
        result = await self.agent.run(prompt)
        spec = result.output
        spec.task_id = task_id
        spec.project_id = project_id
        from tools.token_analytics import extract_usage

        spec.token_usage = extract_usage(result, model_name=str(self.model_name))
        spec.sanitize_executable_phases()

        if spec.base_image is None and any(kw in f"{research_summary} {project.prompt}".lower() for kw in ("python", "flask", "fastapi", "django", "pytest")):
            spec.base_image = "python:3.11-slim"

        fallback_image = spec.base_image or "python:3.11-slim"
        fallback_cmd = "pytest tests" if "python" in fallback_image.lower() else "npm test"

        if not spec.phases:
            spec.phases = [
                ExecutionPhase(
                    phase_name="1-core-implementation",
                    instructions=f"Implement and verify core components for {task_id} in workspace/{workspace_dir}/ with automated offline tests.",
                    validation_command=fallback_cmd,
                )
            ]
        elif (
            any(w in f"{task_id} {project.prompt}".lower() for w in ("build", "create", "implement", "app", "tool", "cli", "server", "gateway", "desk"))
            and all(re.search(r"\.md\b", p.validation_command) and not re.search(r"\b(pytest|python|node|npm|cargo|go|sh|bash)\b", p.validation_command) for p in spec.phases)
        ):
            spec.phases = [
                ExecutionPhase(
                    phase_name="1-core-implementation",
                    instructions=f"Implement working executable code for {task_id} in workspace/{workspace_dir}/ with automated offline unit tests.",
                    validation_command=fallback_cmd,
                )
            ]

        spec.architecture_overview = f"{directory_instruction}\n\n{spec.architecture_overview}"

        timestamp = datetime.now().strftime("%Y-%m-%d")
        note_filename = self.specs_dir / f"spec-{task_id}.md"
        note_filename.parent.mkdir(parents=True, exist_ok=True)

        from tools.taxonomy import get_taxonomic_classification
        classification = get_taxonomic_classification(f"{task_id} {spec.architecture_overview[:200]}")
        tags = [t for t in [classification.domain, classification.action, classification.target, *classification.keywords] if t]
        tags = list(dict.fromkeys(tags))
        tags_block = "tags:\n" + "\n".join(f"  - {t}" for t in tags) + "\n" if tags else "tags: []\n"

        markdown_content = f"""---
id: "spec-{task_id}"
type: "technical-spec"
agent: "taghi"
task_id: "{task_id}"
domain: "{classification.domain or 'core'}"
action: "{classification.action or 'implement'}"
target: "{classification.target}"
{tags_block}{project.frontmatter}created_at: "{timestamp}"
links: ["[[research-{task_id}]]", "[[{task_id}-brief]]"]
---
# Technical Specification: {task_id}

{project.body}## Architecture Overview
{spec.architecture_overview}
"""
        if getattr(spec, "input_interface_spec", None):
            markdown_content += f"\n## User Input Surface & Form Specification\n{spec.input_interface_spec}\n"

        if getattr(spec, "live_verification_guide", None):
            markdown_content += f"\n## Tier 2: Live Verification Guide\n{spec.live_verification_guide}\n"

        markdown_content += "\n## Required Dependencies\n"
        for dep in spec.required_dependencies:
            markdown_content += f"- {dep}\n"

        markdown_content += "\n## Phased Execution Roadmap\n"
        for phase in spec.phases:
            markdown_content += f"### Phase: {phase.phase_name}\n"
            markdown_content += f"- **Instructions:** {phase.instructions}\n"
            markdown_content += f"- **Validation Command:** `{phase.validation_command}`\n\n"

        note_filename.write_text(markdown_content, encoding="utf-8")
        print_agent("taghi", f"Saved technical specification to: {note_filename}")

        await update_vault_graph(self.graph_manager, note_filename)

        return spec

    async def conduct_architectural_review(
        self,
        spec: TechnicalSpec,
        task_id: str,
        design_context: str,
        auto: bool = False,
        input_func: Any = None,
        project_id: str | None = None,
        skip_ui_grill: bool = False,
    ) -> tuple[TechnicalSpec, bool]:
        """
        Run Taghi's architectural grill interview and review approval gate before Meti implements.
        Returns: (approved_or_revised_spec, quit_requested)
        """
        from tools.grill import has_non_default_answers, run_grill_session, format_grill_answers_for_prompt
        from tools.ui import prompt_spec_approval_gate

        current_spec = spec
        grill_completed = False

        while True:
            # Step 1: Run architectural grill questions once
            if not grill_completed and getattr(current_spec, "clarification_questions", None):
                answers, quit_requested = run_grill_session(
                    current_spec.clarification_questions,
                    agent_name="taghi",
                    title="🏛 Taghi Architecture & Schema Grill",
                    auto=auto,
                    input_func=input_func,
                    max_questions=15,
                )
                if quit_requested:
                    return current_spec, True
                grill_completed = True

                if not auto and has_non_default_answers(current_spec.clarification_questions, answers):
                    from tools.ui import print_agent
                    print_agent("taghi", "Re-synthesizing architecture specification with user decisions (AI analyzing)...")
                    formatted_decisions = format_grill_answers_for_prompt(answers, current_spec.clarification_questions)
                    updated_context = f"{design_context}\n\n{formatted_decisions}"
                    current_spec = await self.create_specification(task_id, updated_context, project_id=project_id)

            # Step 2: Present architectural review card and prompt for user approval
            action, feedback = prompt_spec_approval_gate(current_spec, auto=auto, input_func=input_func)
            if action == "quit":
                return current_spec, True
            elif action == "revise" and feedback:
                updated_context = f"{design_context}\n\nUser Architectural Revisions / Feedback:\n{feedback}"
                current_spec = await self.create_specification(task_id, updated_context, project_id=project_id)
            else:
                return current_spec, False

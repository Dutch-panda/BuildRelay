"""Dana — Quality & Architecture Supervisor Agent for BuildRelay.

Dana acts as an independent quality assurance lead and autonomous supervisor.
She evaluates intermediate deliverables from Natasha, Odin, Taghi, and Meti,
providing step-by-step suggestions, risk analyses, and actionable recommendations
either interactively to the developer (advisory mode) or autonomously steering the leads (autonomous mode).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic_ai import Agent
from pydantic_ai.models import Model

from contracts import DanaCritique
from tools.graphify_tool import GraphifyVaultManager
from tools.token_analytics import extract_usage
from tools.ui import print_agent
from tools.vault_infra import register_graph_tools, safe_write_markdown


class DanaQualitySupervisor:
    """
    Quality Supervisor inspecting deliverables across each pipeline stage.
    """

    def __init__(
        self,
        vault_path: str | Path = "./vault",
        model_name: str | Model = "openai:gpt-4o",
        graph_manager: GraphifyVaultManager | None = None,
        supervision_dir: str | Path | None = None,
    ):
        self.vault_path = Path(vault_path)
        self.model_name = model_name
        self.supervision_dir = Path(supervision_dir) if supervision_dir is not None else self.vault_path / "supervision"
        self.graph_manager = graph_manager or GraphifyVaultManager(vault_path=str(self.vault_path))

        self.agent = Agent(
            model_name,
            output_type=DanaCritique,
            model_settings={"cache": True},
            system_prompt=(
                "You are Dana, the Principal Technical Quality & Working Prototype Supervisor of the BuildRelay multi-agent engineering team. "
                "Your mission is to ensure every deliverable produces working, executable software with real backend logic and local persistence.\n\n"
                "CRITICAL SUPERVISOR INVARIANTS (ANTI-PARALYSIS RULES):\n"
                "- The developer at the keyboard IS the stakeholder. Gate approvals constitute full authorization.\n"
                "- NEVER steer leads to delay implementation, demand external corporate/legal sign-offs, or mark working local features as 'unapproved'.\n"
                "- MANDATORY WORKING CODE RULE: Dana MUST issue a 'block' or 'warn' verdict if Taghi or Meti delivers documentation-only proposals, fixture mocks, or unpersisted previews when an application was requested.\n"
                "- CONSTRUCTIVE TECHNICAL STEERING: When formulating 'actionable_recommendations' or steering leads, emit CONCRETE TECHNICAL ACTIONS (e.g. 'Implement SQLite persistence with unique email constraint and pytest tests'), NEVER defensive procedural stalling (e.g. 'obtain approval before implementing').\n\n"
                "EVALUATION CRITERIA (5 TECHNICAL PILLARS):\n"
                "1. Executable Backend & Intent Fulfillment: Evaluate code against the prompt intent. If data storage was requested, verify real persistence (SQLite, JSON, file writes). If a CLI utility or script was requested, verify executable logic and unit tests without penalizing the absence of web servers. Issue 'block' if working code was requested but only a paper spec or static mock preview was delivered.\n"
                "2. Test Rigor & Offline Determinism: Do unit tests execute and pass offline in Docker with non-trivial assertions? Can all phases be tested offline without external live network dependencies? When un-vendored external dependencies are absent, approve and encourage standard-library implementations (e.g. Python http.server/wsgiref/sqlite3) that achieve working software with zero external dependencies.\n"
                "3. Security & Sanitization: Formula injection protection (=, +, -, @), input bounds, and secret hygiene in .env rather than hardcoded credentials.\n"
                "4. UI/UX Ergonomics, State Completeness & Usability: Does the UI surface implement responsive mobile/desktop layout, clean Tailwind tokens, clear validation feedback, and presence of all 5 discrete interactive states (empty, validating, submitting, success, error)? Actively flag crude unstyled tables, raw default browser buttons, missing input focus states, or unhandled blank empty states as actionable design gaps to polish.\n"
                "5. Idiomatic Architecture & Modularity: Are design patterns modular, clean, and extensible without bloat?\n\n"
                "VERDICT RULES:\n"
                "- 'approve': Deliverable is thorough, actionable, implements real working code, and adheres to standards (score >= 85).\n"
                "- 'suggest': Deliverable is solid, but quality could be improved with minor refinements (score 70-84).\n"
                "- 'warn': Deliverable has notable gaps, omitted validation fixtures, or unhandled edge cases (score 50-69).\n"
                "- 'block': Critical flaw, security risk, impossible validation commands, ghost pipeline without input mechanism, OR paper specification / mock preview that fails to implement requested working code (score < 50).\n\n"
                "OUTPUT FORMAT (CONCISE & TELEGRAPHIC):\n"
                "Populate 'summary' with a concise 1-2 sentence executive assessment. "
                "Mandate concise, telegraphic bullet phrasing (zero fluff). Formulate 'strengths', 'risks_or_gaps', and "
                "'actionable_recommendations' as direct, imperative action items (e.g. 'Add email regex validator', 'Risk: Duplicate records overwrite data') "
                "with zero conversational padding. Provide an overall quality 'score' (0-100)."
            ),
        )

        # Bind graph lookup tools for checking historical vault conventions
        register_graph_tools(self.agent, self.graph_manager, "Dana")

    async def supervise_stage(
        self,
        stage_name: Literal["natasha", "odin", "taghi", "meti"],
        deliverable: Any,
        prompt_context: str,
        task_id: str,
        project_id: str | None = None,
    ) -> DanaCritique:
        """
        Evaluate a stage deliverable and return structured quality critique.
        """
        print_agent("dana", f"Supervising stage deliverable from [{stage_name.upper()}] for task: {task_id}")

        deliverable_repr = self._serialize_deliverable(deliverable)

        prompt = (
            f"Supervised Stage: {stage_name.upper()}\n"
            f"Task ID: {task_id}\n"
            f"Project ID: {project_id or 'none'}\n"
            f"Original Request / Prompt Context:\n{prompt_context}\n\n"
            f"Stage Deliverable Content:\n{deliverable_repr}\n\n"
            "Produce your thorough supervision critique and quality verdict."
        )

        result = await self.agent.run(prompt)
        critique = result.output
        critique.lead = stage_name

        critique.token_usage = extract_usage(result, model_name=str(self.model_name))

        # Record supervision note in vault if available
        try:
            self._write_supervision_note(critique, task_id, stage_name, project_id)
        except Exception:
            pass

        return critique

    def _serialize_deliverable(self, deliverable: Any) -> str:
        """Serialize deliverable object into a structured string for Dana's review."""
        if hasattr(deliverable, "model_dump_json"):
            try:
                data = json.loads(deliverable.model_dump_json())
                return json.dumps(data, indent=2)
            except Exception:
                return str(deliverable)
        elif hasattr(deliverable, "to_dict"):
            try:
                return json.dumps(deliverable.to_dict(), indent=2)
            except Exception:
                return str(deliverable)
        elif isinstance(deliverable, (dict, list)):
            try:
                return json.dumps(deliverable, indent=2)
            except Exception:
                return str(deliverable)
        return str(deliverable)

    def _write_supervision_note(
        self,
        critique: DanaCritique,
        task_id: str,
        stage_name: str,
        project_id: str | None,
    ) -> None:
        """Save supervision critique as a Markdown note under vault/supervision/."""
        filename = f"{task_id}-{stage_name}.md"
        rec_list = "\n".join(f"- {r}" for r in critique.actionable_recommendations)
        strengths_list = "\n".join(f"- {s}" for s in critique.strengths)
        risks_list = "\n".join(f"- {r}" for r in critique.risks_or_gaps)

        content = (
            f"---\n"
            f'id: "{task_id}-{stage_name}"\n'
            f'task: "[[tasks/{task_id}]]"\n'
            f'project: "{project_id or ""}"\n'
            f'type: "supervision-critique"\n'
            f'stage: "{stage_name}"\n'
            f'verdict: "{critique.verdict}"\n'
            f'score: {critique.score}\n'
            f"---\n\n"
            f"# Dana Quality Supervision: {stage_name.capitalize()} ({task_id})\n\n"
            f"**Verdict:** {critique.verdict.upper()} (Score: {critique.score}/100)\n\n"
            f"## Summary\n{critique.summary}\n\n"
            f"## Strengths\n{strengths_list}\n\n"
            f"## Risks & Gaps\n{risks_list}\n\n"
            f"## Actionable Recommendations\n{rec_list}\n"
        )
        safe_write_markdown(
            self.supervision_dir,
            filename,
            content,
            category="Supervision",
            directory_name="supervision",
        )

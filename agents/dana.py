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
                "You are Dana, the Principal Quality Supervisor and Autonomous Overseer of the BuildRelay multi-agent engineering team. "
                "Your mission is to rigorously evaluate deliverables from each lead (Natasha's routing/intent brief, Odin's research report, "
                "Taghi's architectural specification, Meti's code implementation) before they proceed down the pipeline.\n\n"
                "EVALUATION CRITERIA:\n"
                "1. Schema & Field Completeness: Are data models, types, column names, and validation rules clearly specified? "
                "   Are edge cases (missing columns, invalid numeric types, duplicate entries, malformed payloads) addressed?\n"
                "2. Security & Isolation Boundaries: Does the deliverable respect container sandbox isolation? "
                "   Are secrets, API tokens, and private credentials deferred to .env and local mocks rather than hardcoded?\n"
                "3. Feasibility & Offline Determinism: Can all phases be tested offline without external live network dependencies in Docker?\n"
                "4. User Ergonomics & Entry Points: Is the concrete user input mechanism (HTML form, interactive CLI, webhook receiver) "
                "   specified and directly usable without cognitive friction?\n"
                "5. Idiomatic Architecture & Modularity: Are design patterns modular, clean, and extensible?\n\n"
                "VERDICT RULES:\n"
                "- 'approve': Deliverable is thorough, actionable, and adheres to standards (score >= 85).\n"
                "- 'suggest': Deliverable is solid, but quality could be improved with minor refinements (score 70-84).\n"
                "- 'warn': Deliverable has notable gaps, omitted validation fixtures, or unhandled edge cases (score 50-69).\n"
                "- 'block': Critical flaw, security risk, impossible validation commands, or ghost pipeline without input mechanism (score < 50).\n\n"
                "OUTPUT FORMAT:\n"
                "Populate 'summary' with a 2-3 sentence executive assessment. Provide 2-4 concrete 'strengths', "
                "2-4 'risks_or_gaps', and 2-4 prioritized 'actionable_recommendations'. Provide an overall quality 'score' (0-100)."
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

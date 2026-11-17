from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PreExecutionMetrics:
    """Tracks LLM calls, human gates, grill questions, and prompt tokens before Meti starts."""

    llm_calls_before_meti: int = 0
    human_gates_before_meti: int = 0
    grill_questions_asked: int = 0
    prompt_tokens_before_meti: int = 0

    def record_llm_call(
        self,
        token_usage: dict[str, Any] | None = None,
        questions_count: int = 0,
    ) -> None:
        self.llm_calls_before_meti += 1
        self.grill_questions_asked += max(0, int(questions_count))
        if isinstance(token_usage, dict):
            self.prompt_tokens_before_meti += int(
                token_usage.get("input_tokens")
                or token_usage.get("prompt_tokens")
                or token_usage.get("total_tokens")
                or 0
            )

    def record_gate(self) -> None:
        self.human_gates_before_meti += 1

    def log_to_state(self, task_id: str, state_dir: Path | str = ".state") -> None:
        try:
            target_dir = Path(state_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            log_path = target_dir / "task.log"
            with log_path.open("a", encoding="utf-8") as f:
                f.write(
                    f"\n--- [{datetime.now().isoformat()}] [Pipeline Metrics] "
                    f"task={task_id} llm_calls_before_meti={self.llm_calls_before_meti} "
                    f"gates_before_meti={self.human_gates_before_meti} "
                    f"grill_questions={self.grill_questions_asked} "
                    f"pre_meti_tokens={self.prompt_tokens_before_meti} ---\n"
                )
        except Exception:
            pass


class StageRunner:
    """Unified stage lifecycle helper managing Cockpit telemetry, token recording, and post-delivery reporting."""

    def __init__(self, cockpit: Any | None = None, tui_active: bool = False):
        if cockpit is None:
            from tools.cockpit import get_cockpit, is_tui_enabled

            cockpit = get_cockpit()
            tui_active = is_tui_enabled()
        self.cockpit = cockpit
        self.tui_active = tui_active

    def reset_for_task(
        self,
        project_id: str,
        task_id: str,
        prompt: str,
        model_name: str = "default",
    ) -> None:
        self.cockpit.telemetry.project_id = project_id
        self.cockpit.telemetry.task_id = task_id
        self.cockpit.telemetry.prompt = prompt
        self.cockpit.telemetry.model_name = str(model_name)
        self.cockpit.telemetry.pipeline_stages = {
            "natasha": "running",
            "odin": "pending",
            "diba": "pending",
            "taghi": "pending",
            "dana": "pending",
            "meti": "pending",
        }
        self.cockpit.telemetry.phases = []

    def start_stage(self, stage: str, action: str) -> None:
        if self.tui_active:
            self.cockpit.telemetry.update_stage(stage, "running")
            self.cockpit.telemetry.set_action(action)
            if hasattr(self.cockpit.telemetry, "refresh"):
                self.cockpit.telemetry.refresh()
            else:
                self.cockpit.refresh()

    def complete_stage(self, stage: str, detail: str = "") -> None:
        if self.tui_active:
            self.cockpit.telemetry.update_stage(stage, "passed", detail)
            self.cockpit.refresh()

    @staticmethod
    def render_post_delivery_summary(
        task_id: str,
        project_id: str | None,
        result: Any,
        token_usage: dict[str, Any] | None = None,
        default_model: str | None = None,
        auto: bool = False,
        show_tokens: bool = True,
    ) -> None:
        from tools.ui import (
            print_completion,
            print_evaluation_scorecard,
            print_how_to_run,
            print_token_summary_table,
            print_workspace_tree,
        )

        print_completion(task_id, result.status == "success", result.summary)
        workspace_dir = project_id or task_id
        workspace_path = Path("workspace") / workspace_dir
        if result.status == "success" and workspace_path.is_dir():
            from tools.eval_harness import DeliverableEvaluator

            evaluator = DeliverableEvaluator(workspace_path, project_id=project_id, task_id=task_id)
            report = evaluator.evaluate()
            evaluator.save_report(report)
            if not auto:
                print_evaluation_scorecard(report)
        if show_tokens and token_usage:
            print_token_summary_table(token_usage, default_model=default_model)
        if result.status == "success":
            print_workspace_tree(workspace_path)
            print_how_to_run(workspace_path)

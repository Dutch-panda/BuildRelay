"""Tests for pipeline simplification: StageRunner, PreExecutionMetrics, and single-pass grill alignment."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agents.diba import DibaDesigner
from agents.natasha import NatashaRouter
from agents.taghi import TaghiArchitect
from contracts import (
    ClarificationOption,
    ClarificationQuestion,
    ExecutionPhase,
    TaskBrief,
    TechnicalSpec,
    UIDesignSpec,
)
from orchestrator import PreExecutionMetrics, StageRunner
from tools.cockpit import BuildRelayCockpit


def test_pre_execution_metrics_logging(tmp_path: Path) -> None:
    metrics = PreExecutionMetrics()
    metrics.record_llm_call({"input_tokens": 1200, "output_tokens": 300}, questions_count=4)
    metrics.record_gate()
    metrics.record_llm_call({"prompt_tokens": 800}, questions_count=3)
    metrics.record_gate()

    assert metrics.llm_calls_before_meti == 2
    assert metrics.human_gates_before_meti == 2
    assert metrics.grill_questions_asked == 7
    assert metrics.prompt_tokens_before_meti == 2000

    state_dir = tmp_path / ".state"
    metrics.log_to_state("task-metrics-1", state_dir=state_dir)
    log_text = (state_dir / "task.log").read_text(encoding="utf-8")
    assert "[Pipeline Metrics]" in log_text
    assert "task=task-metrics-1" in log_text
    assert "llm_calls_before_meti=2" in log_text
    assert "gates_before_meti=2" in log_text
    assert "grill_questions=7" in log_text
    assert "pre_meti_tokens=2000" in log_text


def test_stage_runner_reset_and_transitions() -> None:
    cockpit = BuildRelayCockpit()
    runner = StageRunner(cockpit=cockpit, tui_active=True)

    runner.reset_for_task(
        project_id="proj-alpha",
        task_id="task-alpha",
        prompt="Build dashboard",
        model_name="openai:gpt-4o",
    )
    assert cockpit.telemetry.project_id == "proj-alpha"
    assert cockpit.telemetry.task_id == "task-alpha"
    assert list(cockpit.telemetry.pipeline_stages.keys()) == [
        "natasha",
        "odin",
        "diba",
        "taghi",
        "dana",
        "meti",
    ]
    assert cockpit.telemetry.pipeline_stages["natasha"] == "running"
    assert cockpit.telemetry.phases == []

    runner.complete_stage("natasha", "[Aligned]")
    assert cockpit.telemetry.pipeline_stages["natasha"] == "passed"

    for stage in ("odin", "diba", "taghi", "dana", "meti"):
        runner.start_stage(stage, f"Running {stage}")
        assert cockpit.telemetry.pipeline_stages[stage] == "running"
        runner.complete_stage(stage, f"[{stage} done]")
        assert cockpit.telemetry.pipeline_stages[stage] == "passed"


@pytest.mark.anyio
async def test_natasha_grill_in_place_without_second_llm_call(tmp_path: Path) -> None:
    vault_dir = tmp_path / "vault"
    natasha = NatashaRouter(vault_path=vault_dir, model_name="test")
    brief = TaskBrief(
        task_id="task-in-place-natasha",
        title="Personality Form",
        objective="Initial objective",
        slug="personality-form",
        target_lead="diba",
        research_questions=[],
        clarification_questions=[
            ClarificationQuestion(
                id="entry",
                question="Data entry surface",
                options=[
                    ClarificationOption(key="1", label="Web Form", is_default=True),
                    ClarificationOption(key="2", label="Interactive CLI", is_default=False),
                ],
            )
        ],
    )

    with patch.object(natasha, "realign_intent", new_callable=AsyncMock) as mock_realign:
        inputs = iter(["2"])
        updated, quit_req = await natasha.conduct_grill_session(
            brief,
            auto=False,
            input_func=lambda _: next(inputs),
            realign_on_change=False,
        )

    assert quit_req is False
    mock_realign.assert_not_awaited()
    assert "Interactive CLI" in updated.objective
    assert (vault_dir / "tasks" / "task-in-place-natasha-brief.md").is_file()


@pytest.mark.anyio
async def test_diba_review_in_place_without_second_llm_call(tmp_path: Path) -> None:
    vault_dir = tmp_path / "vault"
    specs_dir = vault_dir / "specs"
    diba = DibaDesigner(vault_path=vault_dir, model_name="test", specs_dir=specs_dir)
    ui_spec = UIDesignSpec(
        surface_type="web_form",
        theme="linear_dark",
        archetype="linear_dark",
        component_layout="Single column card",
        clarification_questions=[
            ClarificationQuestion(
                id="density",
                question="Layout density",
                options=[
                    ClarificationOption(key="1", label="Comfortable", is_default=True),
                    ClarificationOption(key="2", label="Compact", is_default=False),
                ],
            )
        ],
    )

    with patch.object(diba, "design_ui", new_callable=AsyncMock) as mock_design_ui, \
         patch("tools.ui.prompt_spec_approval_gate") as mock_gate:
        inputs = iter(["2"])
        updated_ui, quit_req = await diba.conduct_ui_review(
            ui_spec,
            task_id="task-in-place-diba",
            prompt_context="Build UI",
            auto=False,
            input_func=lambda _: next(inputs),
            skip_approval_gate=True,
            resynthesize_on_change=False,
        )

    assert quit_req is False
    mock_design_ui.assert_not_awaited()
    mock_gate.assert_not_called()
    assert "Compact" in updated_ui.component_layout
    assert (specs_dir / "spec-task-in-place-diba-ui.md").is_file()


@pytest.mark.anyio
async def test_taghi_skips_redundant_grill_when_prototype_approved(tmp_path: Path) -> None:
    vault_dir = tmp_path / "vault"
    taghi = TaghiArchitect(vault_path=vault_dir, model_name="test")
    spec = TechnicalSpec(
        task_id="task-taghi-skip-grill",
        architecture_overview="Lean schema",
        required_dependencies=[],
        base_image="python:3.11-slim",
        phases=[ExecutionPhase(phase_name="1-core", instructions="Build", validation_command="pytest")],
        clarification_questions=[
            ClarificationQuestion(
                id="storage",
                question="Persistence choice",
                options=[
                    ClarificationOption(key="1", label="SQLite", is_default=True),
                    ClarificationOption(key="2", label="In-memory", is_default=False),
                ],
            )
        ],
    )

    with patch("tools.grill.run_grill_session") as mock_grill:
        inputs = iter(["y"])
        final_spec, quit_req = await taghi.conduct_architectural_review(
            spec,
            task_id="task-taghi-skip-grill",
            design_context="Approved prototype context",
            auto=False,
            input_func=lambda _: next(inputs),
            skip_grill_when_prototype=True,
        )

    assert quit_req is False
    mock_grill.assert_not_called()
    assert final_spec.task_id == "task-taghi-skip-grill"

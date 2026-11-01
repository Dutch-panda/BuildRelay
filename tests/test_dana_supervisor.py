"""Tests for Dana Quality Supervisor Agent and Autonomous Steering Pipeline (Issue #28)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.dana import DanaQualitySupervisor
from contracts import (
    DanaCritique,
    ExecutionPhase,
    ImplementationCheckpoint,
    ImplementationResult,
    ResearchReport,
    TaskBrief,
    TechnicalSpec,
)
from main import run_task
from tools.task_ledger import TaskLedger, TaskRecord
from tools.ui import print_dana_critique_card, prompt_dana_gate


def test_dana_critique_contract() -> None:
    """Validate DanaCritique contract properties, defaults, and dictionary access."""
    critique = DanaCritique(
        lead="taghi",
        verdict="suggest",
        summary="Architecture is sound but needs input fixture validation.",
        strengths=["Modular phases", "Deterministic offline testing"],
        risks_or_gaps=["No malformed CSV fixture specified"],
        actionable_recommendations=["Add corrupt row CSV fixture in Phase 1"],
        score=78,
    )
    assert critique.lead == "taghi"
    assert critique.verdict == "suggest"
    assert critique.score == 78
    assert critique["verdict"] == "suggest"
    assert "strengths" in critique
    assert critique.get("score") == 78


def test_dana_supervisor_supervises_stage(tmp_path: Path) -> None:
    """DanaQualitySupervisor evaluates stage deliverable and records supervision note."""
    vault_dir = tmp_path / "vault"
    supervisor = DanaQualitySupervisor(vault_path=vault_dir, model_name="test")

    mock_critique = DanaCritique(
        lead="natasha",
        verdict="approve",
        summary="Task brief clearly scopes user input surface and schemas.",
        strengths=["Clear goal", "Explicit CLI input surface"],
        risks_or_gaps=[],
        actionable_recommendations=["Proceed to architecture"],
        score=95,
    )

    brief = TaskBrief(
        task_id="task-101",
        slug="csv-validator",
        title="CSV Validator",
        objective="Build CLI CSV validator",
        target_lead="taghi",
        research_questions=[],
    )

    with patch.object(supervisor.agent, "run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MagicMock(output=mock_critique)
        critique = asyncio.run(
            supervisor.supervise_stage(
                stage_name="natasha",
                deliverable=brief,
                prompt_context="Build CSV validator",
                task_id="task-101",
                project_id="csv-proj",
            )
        )

        assert critique.verdict == "approve"
        assert critique.score == 95
        assert critique.lead == "natasha"

        # Check supervision note on disk
        note_file = vault_dir / "supervision" / "task-101-natasha.md"
        assert note_file.is_file()
        content = note_file.read_text(encoding="utf-8")
        assert "Dana Quality Supervision: Natasha" in content
        assert "APPROVE" in content.upper()


def test_prompt_dana_gate_proceed() -> None:
    """User pressing enter accepts supervisor review and proceeds."""
    critique = DanaCritique(
        lead="natasha",
        verdict="approve",
        summary="Looks great.",
        score=90,
    )
    action, feedback = prompt_dana_gate(critique, auto=False, input_func=lambda _: "")
    assert action == "proceed"
    assert feedback is None


def test_prompt_dana_gate_apply_recommendations() -> None:
    """User selecting 'a' returns actionable recommendations for steering."""
    critique = DanaCritique(
        lead="taghi",
        verdict="warn",
        summary="Missing error fixtures.",
        actionable_recommendations=["Add negative test fixtures", "Validate schema on startup"],
        score=65,
    )
    action, feedback = prompt_dana_gate(critique, auto=False, input_func=lambda _: "a")
    assert action == "apply"
    assert "Add negative test fixtures" in feedback


def test_prompt_dana_gate_skip_and_quit() -> None:
    """User selecting 's' skips and 'q' aborts."""
    critique = DanaCritique(
        lead="taghi",
        verdict="suggest",
        summary="Good.",
        score=80,
    )
    action, _ = prompt_dana_gate(critique, auto=False, input_func=lambda _: "s")
    assert action == "skip"

    action, _ = prompt_dana_gate(critique, auto=False, input_func=lambda _: "q")
    assert action == "quit"


def test_run_task_with_dana_advisory_mode(tmp_path: Path) -> None:
    """Advisory supervision displays Dana critique and applies recommendations on user confirmation."""
    db_path = tmp_path / "tasks.db"
    ledger = TaskLedger(path=db_path)

    record = TaskRecord(
        task_id="task-dana-adv",
        prompt="Build a transaction parser",
        project_id="tx-project",
    )
    ledger.create(record)

    mock_brief = TaskBrief(
        task_id="task-dana-adv",
        slug="tx-parser",
        title="Transaction Parser",
        objective="Parse transactions",
        target_lead="taghi",
        research_questions=[],
    )
    mock_spec = TechnicalSpec(
        task_id="task-dana-adv",
        architecture_overview="Parser module",
        phases=[ExecutionPhase(phase_name="1-test", instructions="Run", validation_command="pytest")],
        required_dependencies=[],
    )
    mock_impl = ImplementationResult(
        task_id="task-dana-adv",
        status="success",
        summary="Parser built successfully",
        executed_phases=["1-test"],
    )

    dana_critique = DanaCritique(
        lead="natasha",
        verdict="suggest",
        summary="Intent is solid; recommend explicit decimal handling.",
        actionable_recommendations=["Specify decimal precision for transaction amounts"],
        score=82,
    )

    with patch("agents.natasha.NatashaRouter.coordinate_request", new_callable=AsyncMock) as mock_coord, \
         patch("agents.natasha.NatashaRouter.realign_intent", new_callable=AsyncMock) as mock_realign, \
         patch("agents.taghi.TaghiArchitect.create_specification", new_callable=AsyncMock) as mock_spec_call, \
         patch("agents.meti.MetiImplementer.execute_specification", new_callable=AsyncMock) as mock_exec, \
         patch("agents.dana.DanaQualitySupervisor.supervise_stage", new_callable=AsyncMock) as mock_supervise:

        mock_coord.return_value = mock_brief
        mock_realign.return_value = mock_brief
        mock_spec_call.return_value = mock_spec
        mock_exec.return_value = mock_impl
        mock_supervise.return_value = dana_critique

        # User chooses 'a' (apply recommendation) at the Dana gate, then proceeds
        with patch("tools.ui.prompt_dana_gate", return_value=("apply", "Enforce decimal precision")):
            res = asyncio.run(
                run_task(
                    record=record,
                    ledger=ledger,
                    model_override="test",
                    auto=False,
                    supervise="advisory",
                )
            )

            assert res.status == "success"
            assert mock_supervise.called
            # Natasha should have been re-aligned with Dana's recommendation
            assert mock_realign.called


def test_run_task_with_dana_autonomous_mode(tmp_path: Path) -> None:
    """Autonomous supervision automatically steers leads when critique indicates a warning or block."""
    db_path = tmp_path / "tasks.db"
    ledger = TaskLedger(path=db_path)

    record = TaskRecord(
        task_id="task-dana-auto",
        prompt="Build a rate limiter utility",
        project_id="limiter-project",
    )
    ledger.create(record)

    mock_brief = TaskBrief(
        task_id="task-dana-auto",
        slug="rate-limiter",
        title="Rate Limiter",
        objective="Build token bucket rate limiter",
        target_lead="taghi",
        research_questions=[],
    )
    mock_spec = TechnicalSpec(
        task_id="task-dana-auto",
        architecture_overview="Limiter overview",
        phases=[ExecutionPhase(phase_name="1-test", instructions="Run", validation_command="pytest")],
        required_dependencies=[],
    )
    mock_impl = ImplementationResult(
        task_id="task-dana-auto",
        status="success",
        summary="Rate limiter built",
        executed_phases=["1-test"],
    )

    warning_critique = DanaCritique(
        lead="natasha",
        verdict="warn",
        summary="Brief lacks concurrency and thread-safety requirements.",
        actionable_recommendations=["Mandate thread-safe lock mechanisms"],
        score=62,
    )

    with patch("agents.natasha.NatashaRouter.coordinate_request", new_callable=AsyncMock) as mock_coord, \
         patch("agents.natasha.NatashaRouter.realign_intent", new_callable=AsyncMock) as mock_realign, \
         patch("agents.taghi.TaghiArchitect.create_specification", new_callable=AsyncMock) as mock_spec_call, \
         patch("agents.meti.MetiImplementer.execute_specification", new_callable=AsyncMock) as mock_exec, \
         patch("agents.dana.DanaQualitySupervisor.supervise_stage", new_callable=AsyncMock) as mock_supervise:

        mock_coord.return_value = mock_brief
        mock_realign.return_value = mock_brief
        mock_spec_call.return_value = mock_spec
        mock_exec.return_value = mock_impl
        mock_supervise.return_value = warning_critique

        res = asyncio.run(
            run_task(
                record=record,
                ledger=ledger,
                model_override="test",
                auto=True,
                supervise="autonomous",
            )
        )

        assert res.status == "success"
        # Autonomous mode detected 'warn' and automatically steered Natasha to realign!
        assert mock_realign.called
        assert "thread-safe" in mock_realign.call_args[0][1]


def test_run_task_with_dana_off(tmp_path: Path) -> None:
    """When supervision is 'off', Dana is not invoked and pipeline runs directly."""
    db_path = tmp_path / "tasks.db"
    ledger = TaskLedger(path=db_path)

    record = TaskRecord(
        task_id="task-no-dana",
        prompt="Build a simple hash helper",
    )
    ledger.create(record)

    mock_brief = TaskBrief(
        task_id="task-no-dana",
        slug="hash-helper",
        title="Hash Helper",
        objective="Build helper",
        target_lead="taghi",
        research_questions=[],
    )
    mock_spec = TechnicalSpec(
        task_id="task-no-dana",
        architecture_overview="Helper overview",
        phases=[ExecutionPhase(phase_name="1-test", instructions="Run", validation_command="pytest")],
        required_dependencies=[],
    )
    mock_impl = ImplementationResult(
        task_id="task-no-dana",
        status="success",
        summary="Helper built",
        executed_phases=["1-test"],
    )

    with patch("agents.natasha.NatashaRouter.coordinate_request", new_callable=AsyncMock) as mock_coord, \
         patch("agents.taghi.TaghiArchitect.create_specification", new_callable=AsyncMock) as mock_spec_call, \
         patch("agents.meti.MetiImplementer.execute_specification", new_callable=AsyncMock) as mock_exec, \
         patch("agents.dana.DanaQualitySupervisor.supervise_stage", new_callable=AsyncMock) as mock_supervise:

        mock_coord.return_value = mock_brief
        mock_spec_call.return_value = mock_spec
        mock_exec.return_value = mock_impl

        res = asyncio.run(
            run_task(
                record=record,
                ledger=ledger,
                model_override="test",
                auto=True,
                supervise="off",
            )
        )

        assert res.status == "success"
        assert not mock_supervise.called

"""Tests for continuous feature iteration loops and post-delivery enhancement pipeline (Issue #27)."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from contracts import ImplementationResult, TaskBrief, TechnicalSpec
from main import run_iteration_loop
from tools.task_ledger import TaskLedger, TaskRecord
from tools.ui import prompt_iteration_gate


def test_prompt_iteration_gate_auto_exits() -> None:
    """Headless auto mode returns ('exit', None) without prompting."""
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=True,
    )
    assert action == "exit"
    assert payload is None


def test_prompt_iteration_gate_exit_inputs() -> None:
    """User pressing enter, 5, q, or quit exits cleanly."""
    for choice in ["", "5", "q", "quit", "exit"]:
        action, payload = prompt_iteration_gate(
            project_id="test-proj",
            task_id="test-task",
            auto=False,
            input_func=lambda _: choice,
        )
        assert action == "exit"
        assert payload is None


def test_prompt_iteration_gate_add_feature() -> None:
    """User choosing [1] or 'feature' is prompted for description."""
    inputs = iter(["1", "Add export to PDF functionality"])
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: next(inputs),
    )
    assert action == "feature"
    assert payload == "Add export to PDF functionality"


def test_prompt_iteration_gate_refactor() -> None:
    """User choosing [2] or 'refactor' is prompted for refactoring instructions."""
    inputs = iter(["2", "Optimize SQL queries and add index"])
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: next(inputs),
    )
    assert action == "refactor"
    assert payload == "Optimize SQL queries and add index"


def test_prompt_iteration_gate_session() -> None:
    """User choosing [3] requests interactive REPL session."""
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: "3",
    )
    assert action == "session"
    assert payload is None


def test_prompt_iteration_gate_verify() -> None:
    """User choosing [4] then [v] triggers live verification."""
    inputs = iter(["4", "v"])
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: next(inputs),
    )
    assert action == "verify"
    assert payload is None


def test_prompt_iteration_gate_preview() -> None:
    """User choosing [4] then [p] triggers UI preview server."""
    inputs = iter(["4", "p"])
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: next(inputs),
    )
    assert action == "preview"
    assert payload is None


def test_prompt_iteration_gate_cancel_subchoice() -> None:
    """User choosing [4] then pressing Enter returns 'none'."""
    inputs = iter(["4", ""])
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: next(inputs),
    )
    assert action == "none"
    assert payload is None


def test_prompt_iteration_gate_freeform_prompt() -> None:
    """User entering direct task prompt is treated as a new feature."""
    action, payload = prompt_iteration_gate(
        project_id="test-proj",
        task_id="test-task",
        auto=False,
        input_func=lambda _: "Build Stripe webhook listener",
    )
    assert action == "feature"
    assert payload == "Build Stripe webhook listener"


def test_run_iteration_loop_executes_second_feature_task(tmp_path: Path) -> None:
    """Multi-turn iteration executes a subsequent feature while retaining project identity."""
    db_path = tmp_path / "tasks.db"
    ledger = TaskLedger(path=db_path)

    initial_record = TaskRecord(
        task_id="invoice-pipeline-init",
        prompt="Build initial invoice pipeline",
        project_id="invoice-pipeline",
        status="COMPLETED",
    )
    ledger.create(initial_record)

    args = argparse.Namespace(
        auto=False,
        model=None,
        tier=None,
        image=None,
        step=False,
        research_only=False,
        port=8080,
    )
    lead_overrides = {"natasha": None, "odin": None, "taghi": None, "meti": None}

    # First turn: User selects [1] (feature) and provides prompt;
    # Second turn: User selects [5] (exit).
    prompts = iter(["1", "Add CSV batch export", "5"])

    mock_result = ImplementationResult(
        task_id="subsequent-task",
        project_id="invoice-pipeline",
        status="success",
        summary="Batch export implemented cleanly",
        executed_phases=["phase-1"],
    )

    with patch("main.run_task", new_callable=AsyncMock) as mock_run_task:
        mock_run_task.return_value = mock_result
        asyncio.run(
            run_iteration_loop(
                record=initial_record,
                ledger=ledger,
                args=args,
                lead_overrides=lead_overrides,
                input_func=lambda _: next(prompts),
            )
        )

        assert mock_run_task.call_count == 1
        called_record = mock_run_task.call_args[0][0]
        assert called_record.project_id == "invoice-pipeline"
        assert "CSV batch export" in called_record.prompt


def test_run_iteration_loop_opens_session(tmp_path: Path) -> None:
    """Selecting [3] delegates to run_project_session with the active project ID."""
    db_path = tmp_path / "tasks.db"
    ledger = TaskLedger(path=db_path)

    initial_record = TaskRecord(
        task_id="crm-init",
        prompt="Build initial CRM",
        project_id="crm-project",
        status="COMPLETED",
    )
    ledger.create(initial_record)

    args = argparse.Namespace(
        auto=False,
        model=None,
        tier=None,
        image=None,
        step=False,
        research_only=False,
        port=8080,
    )
    lead_overrides = {"natasha": None, "odin": None, "taghi": None, "meti": None}

    with patch("tools.session.run_project_session", new_callable=AsyncMock) as mock_session:
        asyncio.run(
            run_iteration_loop(
                record=initial_record,
                ledger=ledger,
                args=args,
                lead_overrides=lead_overrides,
                input_func=lambda _: "3",
            )
        )
        mock_session.assert_called_once_with(
            project_id="crm-project",
            model=None,
            tier=None,
            auto=False,
            step=False,
            input_func=mock_session.call_args.kwargs["input_func"],
        )


def test_run_iteration_loop_runs_verify_then_exits(tmp_path: Path) -> None:
    """Selecting [4] -> [v] runs live verification, then continues loop until exit."""
    db_path = tmp_path / "tasks.db"
    ledger = TaskLedger(path=db_path)

    initial_record = TaskRecord(
        task_id="crm-init",
        prompt="Build initial CRM",
        project_id="crm-project",
        status="COMPLETED",
    )
    ledger.create(initial_record)

    args = argparse.Namespace(
        auto=False,
        model=None,
        tier=None,
        image=None,
        step=False,
        research_only=False,
        port=8080,
    )
    lead_overrides = {"natasha": None, "odin": None, "taghi": None, "meti": None}

    inputs = iter(["4", "v", "5"])

    with patch("tools.live_verifier.run_live_verification") as mock_verify:
        asyncio.run(
            run_iteration_loop(
                record=initial_record,
                ledger=ledger,
                args=args,
                lead_overrides=lead_overrides,
                input_func=lambda _: next(inputs),
            )
        )
        mock_verify.assert_called_once_with("crm-project")


def test_natasha_and_taghi_incremental_evolution_headers(tmp_path: Path) -> None:
    """Verify that Natasha and Taghi inject incremental headers when project has memory."""
    from agents.natasha import NatashaRouter
    from agents.taghi import TaghiArchitect
    from tools.project_notes import init_project_workspace, update_project_profile

    ws_root = tmp_path / "workspace"
    vault_root = tmp_path / "vault"
    project_id = "test-incremental"

    # Pre-populate project memory
    init_project_workspace(project_id, workspace_root=ws_root)
    update_project_profile(
        project_id=project_id,
        task_id="task-1",
        brief=TaskBrief(
            task_id="task-1",
            slug="initial-module",
            title="Initial module",
            objective="Initial baseline",
            target_lead="meti",
            research_questions=[],
        ),
        result=ImplementationResult(task_id="task-1", status="success", summary="Base done", executed_phases=[]),
        workspace_root=ws_root,
    )

    # Test Natasha agent run prompt
    router = NatashaRouter(vault_path=vault_root, model_name="test")
    with patch.object(router.agent, "run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = MagicMock(
            output=TaskBrief(
                task_id="task-2",
                slug="new-feature",
                title="New feature",
                objective="Add feature",
                target_lead="meti",
                research_questions=[],
            )
        )
        # Patch prepare_project to point to our test workspace_root
        with patch("agents.natasha.prepare_project") as mock_prep:
            from tools.project_notes import prepare_project
            mock_prep.side_effect = lambda v, p: prepare_project(vault_root, p, workspace_root=ws_root)
            asyncio.run(router.coordinate_request("Add secondary endpoint", "task-2", project_id=project_id))
            called_prompt = mock_run.call_args[0][0]
            assert "[INCREMENTAL FEATURE EVOLUTION]" in called_prompt
            assert f"project '{project_id}'" in called_prompt

    # Test Taghi agent run prompt
    architect = TaghiArchitect(vault_path=vault_root, model_name="test")
    with patch.object(architect.agent, "run", new_callable=AsyncMock) as mock_taghi_run:
        mock_taghi_run.return_value = MagicMock(
            output=TechnicalSpec(
                task_id="task-2",
                architecture_overview="Overview",
                phases=[],
                required_dependencies=[],
            )
        )
        with patch("agents.taghi.prepare_project") as mock_prep_taghi:
            from tools.project_notes import prepare_project
            mock_prep_taghi.side_effect = lambda v, p: prepare_project(vault_root, p, workspace_root=ws_root)
            asyncio.run(architect.create_specification("task-2", "Add secondary endpoint", project_id=project_id))
            called_taghi_prompt = mock_taghi_run.call_args[0][0]
            assert "[INCREMENTAL ARCHITECTURE SPECIFICATION]" in called_taghi_prompt
            assert f"project '{project_id}'" in called_taghi_prompt

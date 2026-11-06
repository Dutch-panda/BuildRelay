"""Unit tests for Split-Pane Textual/Rich Live TUI Cockpit & Live Telemetry Dashboard."""

import os
import sys
from unittest.mock import Mock, patch
import pytest

from tools.cockpit import (
    BuildRelayCockpit,
    CockpitTelemetry,
    get_cockpit,
    is_tui_enabled,
    reset_cockpit,
)


def test_cockpit_telemetry_initialization_and_formatting():
    telem = CockpitTelemetry(
        project_id="crm-app",
        task_id="task-auth-01",
        prompt="Add login auth",
        model_name="gpt-4o",
    )
    assert telem.project_id == "crm-app"
    assert telem.task_id == "task-auth-01"
    assert telem.format_elapsed_time() in ("00:00", "00:01")

    # Log buffer handling
    telem.add_log("Line 1\nLine 2")
    assert telem.log_lines == ["Line 1", "Line 2"]
    telem.clear_logs()
    assert len(telem.log_lines) == 0


def test_cockpit_telemetry_scrollback():
    telem = CockpitTelemetry()
    for i in range(50):
        telem.add_log(f"Log {i}")

    assert telem.scroll_offset == 0
    telem.scroll_up(10)
    assert telem.scroll_offset == 10
    telem.scroll_down(5)
    assert telem.scroll_offset == 5
    telem.scroll_to_bottom()
    assert telem.scroll_offset == 0


def test_cockpit_telemetry_stages_and_phases():
    telem = CockpitTelemetry()

    # Pipeline stepper
    telem.update_stage("natasha", "passed", "[Aligned]")
    assert telem.pipeline_stages["natasha"] == "passed"
    assert telem.stage_details["natasha"] == "[Aligned]"

    telem.update_stage("taghi", "running")
    assert telem.pipeline_stages["taghi"] == "running"
    assert telem.active_lead == "taghi"

    # Execution phases
    phases = [
        {"phase_name": "1-core", "validation_command": "pytest tests/core"},
        {"phase_name": "2-api", "validation_command": "pytest tests/api"},
    ]
    telem.set_phases(phases)
    assert len(telem.phases) == 2
    assert telem.phases[0]["name"] == "1-core"
    assert telem.phases[0]["status"] == "running"

    telem.update_phase("1-core", "passed", attempt=1)
    assert telem.phases[0]["status"] == "passed"

    telem.update_phase("2-api", "running", attempt=2)
    assert telem.phases[1]["status"] == "running"
    assert telem.phases[1]["attempt"] == 2


def test_cockpit_telemetry_token_usage_and_cost():
    telem = CockpitTelemetry(model_name="gpt-4o")
    telem.record_token_usage({"total_tokens": 1000, "prompt_tokens": 800, "completion_tokens": 200})
    assert telem.total_tokens == 1000
    assert telem.estimated_cost > 0.0
    summary = telem.format_tokens_summary()
    assert "1.0k" in summary
    assert "$" in summary


def test_cockpit_layout_construction():
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table

    cockpit = BuildRelayCockpit()
    cockpit.telemetry.project_id = "test-proj"
    cockpit.telemetry.task_id = "task-ui-01"
    cockpit.telemetry.add_log("Docker starting container...")
    cockpit.telemetry.add_log("pytest tests PASSED")

    renderable = cockpit.make_layout()
    assert isinstance(renderable, Group)
    assert len(renderable.renderables) == 3

    header, grid, dock = renderable.renderables
    assert isinstance(header, Panel)
    assert isinstance(grid, Table)
    assert isinstance(dock, Panel)

    # Rendered lines should be compact (~16-22 lines) with zero blank trailing padding
    rendered_lines = cockpit.console.render_lines(renderable)
    assert 14 <= len(rendered_lines) <= 24


def test_cockpit_nested_pause_reference_counting():
    cockpit = BuildRelayCockpit()
    cockpit._is_active = True

    with patch.object(cockpit, "suspend", return_value=True) as mock_suspend, \
         patch.object(cockpit, "resume") as mock_resume:
        with cockpit.pause():
            assert cockpit._pause_depth == 1
            assert mock_suspend.call_count == 1
            with cockpit.pause():
                assert cockpit._pause_depth == 2
                assert mock_suspend.call_count == 1  # Not suspended again
            assert cockpit._pause_depth == 1
            assert mock_resume.call_count == 0  # Not resumed yet
        assert cockpit._pause_depth == 0
        assert mock_resume.call_count == 1  # Resumed once at root exit


def test_cockpit_awaiting_input_visual_states():
    cockpit = BuildRelayCockpit()
    cockpit.telemetry.awaiting_input = True
    header = cockpit.render_header()
    assert "INPUT REQUIRED" in str(header.renderable)
    assert header.border_style == "#f59e0b"

    dock = cockpit.render_dock()
    assert "ATTENTION REQUIRED" in str(dock.renderable)
    assert dock.border_style == "#f59e0b"

    cockpit.telemetry.awaiting_input = False
    header_running = cockpit.render_header()
    assert "RUNNING" in str(header_running.renderable)
    assert header_running.border_style == "#38bdf8"


def test_cockpit_tui_enabled_logic(monkeypatch):
    # Non-TTY (e.g. CI or pipe): disabled by default
    monkeypatch.delenv("BUILDRELAY_TUI", raising=False)
    monkeypatch.delenv("BUILDRELAY_COCKPIT", raising=False)
    monkeypatch.delenv("BUILDRELAY_PLAIN", raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert is_tui_enabled() is False

    # Non-TTY with explicit opt-in: enabled
    monkeypatch.setenv("BUILDRELAY_TUI", "1")
    assert is_tui_enabled() is True

    # Interactive TTY: enabled by default
    monkeypatch.delenv("BUILDRELAY_TUI", raising=False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert is_tui_enabled() is True

    # Interactive TTY with BUILDRELAY_PLAIN=1: disabled
    monkeypatch.setenv("BUILDRELAY_PLAIN", "1")
    assert is_tui_enabled() is False

    # Interactive TTY with BUILDRELAY_TUI=0: disabled
    monkeypatch.delenv("BUILDRELAY_PLAIN", raising=False)
    monkeypatch.setenv("BUILDRELAY_TUI", "0")
    assert is_tui_enabled() is False


def test_cockpit_suspend_and_resume():
    reset_cockpit()
    cockpit = get_cockpit()

    assert cockpit.suspend() is False
    cockpit.resume()

    # With pause context manager
    with cockpit.pause():
        pass


def test_cockpit_ui_helpers_telemetry_integration():
    from tools.ui import print_agent, print_brief_summary, print_spec_summary, print_phase_table
    reset_cockpit()
    cockpit = get_cockpit()
    cockpit._is_active = True

    print_agent("natasha", "Analyzing request")
    assert cockpit.telemetry.active_lead == "natasha"
    assert "[NATASHA] Analyzing request" in cockpit.telemetry.log_lines[-1]

    print_brief_summary("taghi", ["Which db to use?"], token_usage={"total_tokens": 100, "prompt_tokens": 80, "completion_tokens": 20})
    assert cockpit.telemetry.pipeline_stages["natasha"] == "passed"
    assert cockpit.telemetry.pipeline_stages["taghi"] == "running"

    phases = [
        {"phase_name": "1-core", "validation_command": "pytest tests/core"},
        {"phase_name": "2-api", "validation_command": "pytest tests/api"},
    ]
    print_spec_summary("python:3.11-slim", phases)
    assert len(cockpit.telemetry.phases) == 2
    assert cockpit.telemetry.pipeline_stages["taghi"] == "passed"

    print_phase_table(phases, completed_phases=["1-core"], current_phase="2-api")
    assert cockpit.telemetry.phases[0]["status"] == "passed"
    assert cockpit.telemetry.phases[1]["status"] == "running"

    cockpit._is_active = False


def test_non_tty_graceful_degradation(monkeypatch):
    reset_cockpit()
    cockpit = get_cockpit()

    # In non-TTY, start() should not activate Live
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    monkeypatch.setenv("BUILDRELAY_TUI", "1")

    cockpit.start(screen=False)
    assert cockpit.is_active is False
    cockpit.stop()


def test_cockpit_live_context_and_pause():
    reset_cockpit()
    cockpit = get_cockpit()

    # With pause context manager
    with cockpit.pause():
        pass  # Clean execution without exception

    with cockpit.live_context(screen=False):
        pass  # Clean entry and exit


def test_cockpit_standalone_mode(tmp_path):
    ws_dir = tmp_path / "workspace"
    proj_dir = ws_dir / "cockpit-proj"
    proj_dir.mkdir(parents=True)
    (proj_dir / "PROJECT_PROFILE.md").write_text(
        "# Project Profile\n\n## Active Data Schemas\n- User (id, email)\n\n## User Input Surfaces\n- web form\n",
        encoding="utf-8",
    )

    cockpit = BuildRelayCockpit()
    inputs = ["p", "v", "c", "q"]

    cockpit.run_standalone(
        project_id="cockpit-proj",
        workspace_root=ws_dir,
        input_func=lambda _: inputs.pop(0),
    )

    assert cockpit.telemetry.project_id == "cockpit-proj"
    assert cockpit.telemetry.preview_url == "http://localhost:8080"


@pytest.mark.anyio
async def test_session_repl_cockpit_command(tmp_path, capsys):
    vault = tmp_path / "vault"
    ws = tmp_path / "workspace"
    from tools.session import run_project_session

    inputs = ["/cockpit", "q", "/exit"]
    await run_project_session(
        project_id="tui-session-proj",
        vault_path=vault,
        workspace_root=ws,
        input_func=lambda _: inputs.pop(0),
    )

    out = capsys.readouterr().out
    assert "tui-session-proj" in out
    assert "Session ended. Project memory preserved." in out


@pytest.mark.anyio
async def test_cli_cockpit_command_dispatch(monkeypatch):
    from main import main
    called_projects = []

    def mock_run_standalone(self, project_id, **kwargs):
        called_projects.append(project_id)

    monkeypatch.setattr(BuildRelayCockpit, "run_standalone", mock_run_standalone)

    # 1. Positional syntax: python main.py cockpit my-project
    monkeypatch.setattr(sys, "argv", ["buildrelay", "cockpit", "my-project"])
    await main()
    assert called_projects == ["my-project"]

    # 2. Flag syntax: python main.py --cockpit my-project
    called_projects.clear()
    monkeypatch.setattr(sys, "argv", ["buildrelay", "--cockpit", "my-project"])
    await main()
    assert called_projects == ["my-project"]


def test_cockpit_spinner_in_header_and_dock():
    cockpit = BuildRelayCockpit()
    cockpit.telemetry.awaiting_input = False
    cockpit.telemetry.current_action = "Synthesizing architecture..."

    # Check header contains running spinner
    header = cockpit.render_header()
    # Panel renderable text
    text_content = header.renderable
    assert "● RUNNING" in text_content

    # Check dock contains action line
    dock = cockpit.render_dock()
    assert "Synthesizing architecture..." in str(dock.renderable)

    # When awaiting input
    cockpit.telemetry.awaiting_input = True
    header_input = cockpit.render_header()
    assert "INPUT REQUIRED" in header_input.renderable


def test_cockpit_heartbeat_ticker_lifecycle(monkeypatch):
    import time
    cockpit = BuildRelayCockpit()
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setenv("BUILDRELAY_TUI", "1")

    # Start cockpit with mock Live
    cockpit.start(screen=False)
    assert cockpit.is_active is True
    assert cockpit._ticker_thread is not None
    assert cockpit._ticker_thread.is_alive()

    # Pause increments pause depth
    with cockpit.pause():
        assert cockpit._pause_depth == 1

    # Resume restores
    assert cockpit._pause_depth == 0

    # Stop stops ticker thread cleanly
    cockpit.stop()
    assert cockpit.is_active is False
    assert cockpit._ticker_thread is None


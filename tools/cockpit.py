"""Split-Pane Terminal User Interface Cockpit & Live Telemetry Dashboard for BuildRelay.

Provides a persistent multi-pane developer cockpit featuring:
1. Header HUD: Project ID, Task ID, active lead, elapsed time, token usage, cost, and health.
2. Workflow Sidebar: Pipeline progression stepper, phased execution roadmap, and living memory.
3. Container Telemetry Buffer: Real-time scrolling stdout/stderr logs from Docker sandboxes.
4. Interactive Command Dock: Action status, quick hotkeys, and embedded gate prompts.
Includes automatic graceful fallback to linear logs in non-TTY and CI environments.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def is_tui_enabled() -> bool:
    """Return True if TUI cockpit mode is enabled and supported by the current environment."""
    if os.environ.get("BUILDRELAY_PLAIN") == "1":
        return False
    if os.environ.get("BUILDRELAY_TUI") == "0":
        return False
    if os.environ.get("BUILDRELAY_TUI") == "1" or os.environ.get("BUILDRELAY_COCKPIT") == "1":
        return True
    if not sys.stdout.isatty():
        return False
    return True


@dataclass
class CockpitTelemetry:
    project_id: str = "default-project"
    task_id: str = "pending"
    prompt: str = ""
    active_lead: str = "natasha"
    model_name: str = "gpt-4o"
    start_time: float = field(default_factory=time.time)

    # Token & Cost Metrics
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost: float = 0.0
    cost_display: str = "$0.00"

    # Pipeline Stepper: name -> ('pending', 'running', 'passed', 'failed', 'skipped')
    pipeline_stages: dict[str, str] = field(
        default_factory=lambda: {
            "natasha": "running",
            "odin": "pending",
            "taghi": "pending",
            "diba": "pending",
            "dana": "pending",
            "meti": "pending",
        }
    )
    stage_details: dict[str, str] = field(default_factory=dict)

    # Execution Phases from TechnicalSpec
    phases: list[dict[str, Any]] = field(default_factory=list)
    active_phase_index: int = 0

    # Living Memory Snippets
    storage_schema: str = "SQLite"
    ui_surface: str = "Web Form (form.html)"

    # Service & Sandbox Health
    sandbox_status: str = "Docker (Ready)"
    preview_url: str = "Off"

    # Output Logs Buffer
    log_lines: list[str] = field(default_factory=list)
    max_log_lines: int = 1000
    scroll_offset: int = 0

    # Command Dock Action
    current_action: str = "Initializing BuildRelay task..."
    awaiting_input: bool = False

    def format_elapsed_time(self) -> str:
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        return f"{mins:02d}:{secs:02d}"

    def format_tokens_summary(self) -> str:
        if self.total_tokens >= 1_000_000:
            tok_str = f"{self.total_tokens / 1_000_000:.1f}M"
        elif self.total_tokens >= 1_000:
            tok_str = f"{self.total_tokens / 1_000:.1f}k"
        else:
            tok_str = str(self.total_tokens)
        return f"{tok_str} ({self.cost_display})"

    def add_log(self, text: str) -> None:
        """Append log text, splitting multi-line strings and respecting maximum buffer size."""
        if not text:
            return
        lines = str(text).splitlines()
        for line in lines:
            self.log_lines.append(line)
        if len(self.log_lines) > self.max_log_lines:
            self.log_lines = self.log_lines[-self.max_log_lines:]

    def clear_logs(self) -> None:
        self.log_lines.clear()
        self.scroll_offset = 0

    def scroll_up(self, count: int = 5) -> None:
        max_offset = max(0, len(self.log_lines) - 5)
        self.scroll_offset = min(self.scroll_offset + count, max_offset)

    def scroll_down(self, count: int = 5) -> None:
        self.scroll_offset = max(0, self.scroll_offset - count)

    def scroll_to_bottom(self) -> None:
        self.scroll_offset = 0

    def update_stage(self, stage: str, status: str, detail: str | None = None) -> None:
        stage = stage.lower().strip()
        if stage in self.pipeline_stages:
            self.pipeline_stages[stage] = status
            if detail:
                self.stage_details[stage] = detail
            self.active_lead = stage

    def set_phases(self, phases: list[Any]) -> None:
        self.phases = []
        for i, p in enumerate(phases):
            name = (
                getattr(p, "phase_name", None)
                or (p.get("phase_name") if isinstance(p, dict) else f"Phase {i+1}")
            )
            cmd = (
                getattr(p, "validation_command", None)
                or (p.get("validation_command") if isinstance(p, dict) else "")
            )
            self.phases.append({
                "name": name,
                "status": "pending",
                "attempt": 1,
                "max_attempts": 3,
                "command": cmd,
            })
        if self.phases:
            self.phases[0]["status"] = "running"
            self.active_phase_index = 0

    def update_phase(self, phase_name: str, status: str, attempt: int = 1) -> None:
        for idx, p in enumerate(self.phases):
            if p["name"] == phase_name or phase_name in p["name"]:
                p["status"] = status
                p["attempt"] = attempt
                self.active_phase_index = idx
                break

    def record_token_usage(
        self, usage: dict[str, Any] | None, model_name: str | None = None
    ) -> None:
        if not usage:
            return
        total = usage.get("total_tokens", 0)
        prompt = usage.get("prompt_tokens", 0)
        completion = usage.get("completion_tokens", 0)
        cached = usage.get("cache_read_tokens", 0)

        self.total_tokens += total
        self.prompt_tokens += prompt
        self.completion_tokens += completion

        try:
            from tools.token_analytics import calculate_token_cost
            cost, display = calculate_token_cost(
                self.prompt_tokens,
                self.completion_tokens,
                model=model_name or self.model_name,
                cache_read_tokens=cached,
            )
            if cost is not None:
                self.estimated_cost = cost
                self.cost_display = display
        except Exception:
            pass

    def set_action(self, action: str) -> None:
        self.current_action = action


SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class BuildRelayCockpit:
    """Manages the full split-pane terminal dashboard layout and Rich Live lifecycle."""

    def __init__(
        self,
        console: Console | None = None,
        telemetry: CockpitTelemetry | None = None,
    ):
        self.console = console or Console(highlight=False)
        self.telemetry = telemetry or CockpitTelemetry()
        self._live: Live | None = None
        self._is_active = False
        self._screen = False
        self._pause_depth = 0
        self._ticker_thread: threading.Thread | None = None
        self._ticker_stop_event = threading.Event()
        self._spinner_idx = 0

    @property
    def is_active(self) -> bool:
        return self._is_active

    def _ticker_loop(self) -> None:
        """Background heartbeat ticker to keep timer ticking and spinner turning during async model calls."""
        while not self._ticker_stop_event.is_set():
            if (
                self._is_active
                and self._pause_depth == 0
                and self._live is not None
                and self._live.is_started
            ):
                self._spinner_idx = (self._spinner_idx + 1) % len(SPINNER_FRAMES)
                try:
                    self._live.update(self.make_layout(), refresh=True)
                except Exception:
                    pass
            time.sleep(0.5)

    def make_layout(self) -> Group:
        """Construct the split terminal dashboard hierarchy with 0 trailing padding lines."""
        header = self.render_header()
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1, min_width=32)
        grid.add_column(ratio=2)
        # 1.5x expanded body (sidebar + logs)
        grid.add_row(self.render_sidebar(), self.render_logs(max_display_lines=9))
        dock = self.render_dock()
        return Group(header, grid, dock)

    def render_header(self) -> Panel:
        """Render Persistent Header Bar HUD."""
        t = self.telemetry
        title = "⚡ [bold #38bdf8]BUILDRELAY[/bold #38bdf8]"
        spinner = SPINNER_FRAMES[self._spinner_idx % len(SPINNER_FRAMES)]
        status_badge = (
            "[bold black on #f59e0b] 🔔 INPUT REQUIRED [/bold black on #f59e0b]"
            if t.awaiting_input
            else f"[bold #22c55e]● RUNNING {spinner}[/bold #22c55e]"
        )
        project = f"[bold white]Proj:[/bold white] [green]{escape(t.project_id)}[/green]"
        task = f"[bold white]Task:[/bold white] [cyan]{escape(t.task_id)}[/cyan]"
        model = f"[bold white]Model:[/bold white] [magenta]{escape(t.model_name)}[/magenta]"
        elapsed = f"[bold white]Time:[/bold white] [yellow]{t.format_elapsed_time()}[/yellow]"
        tokens = f"[bold white]Tokens:[/bold white] [bold]{t.format_tokens_summary()}[/bold]"
        preview = f"[bold white]Preview:[/bold white] [cyan]{escape(t.preview_url)}[/cyan]"

        content = f"{title} · {status_badge} · {project} · {task} · {model} · {elapsed} · {tokens} · {preview}"
        border_col = "#f59e0b" if t.awaiting_input else "#38bdf8"
        return Panel(
            content.strip(),
            border_style=border_col,
            padding=(0, 1),
        )

    def render_sidebar(self) -> Panel:
        """Render Left Workflow Sidebar: Compact Pipeline Progression & Phases."""
        t = self.telemetry
        content: list[str] = []

        # 1. Pipeline progression badges (compact 2 lines)
        stage_names = [
            ("natasha", "Natasha"),
            ("odin", "Odin"),
            ("taghi", "Taghi"),
            ("diba", "Diba"),
            ("dana", "Dana"),
            ("meti", "Meti"),
        ]
        badges = []
        for key, name in stage_names:
            status = t.pipeline_stages.get(key, "pending")
            if status == "passed":
                badges.append(f"[green]✔ {name}[/green]")
            elif status == "running":
                badges.append(f"[bold cyan]▶ {name}[/bold cyan]")
            elif status == "failed":
                badges.append(f"[bold red]✖ {name}[/bold red]")
            else:
                badges.append(f"[dim]◻ {name}[/dim]")

        line1 = " ".join(badges[:3])
        line2 = " ".join(badges[3:])
        content.append(f"[bold #38bdf8]PIPELINE:[/bold #38bdf8] {line1}")
        content.append(f"          {line2}")

        # 2. Phased Execution Roadmap (compact list, up to 5 phases)
        content.append("[bold #38bdf8]PHASES:[/bold #38bdf8]")
        if not t.phases:
            content.append(" [dim](Awaiting specification...)[/dim]")
        else:
            for p in t.phases[:5]:
                pname = p["name"]
                pstat = p["status"]
                patt = p.get("attempt", 1)
                if pstat == "passed":
                    icon = "[green]✔[/green]"
                elif pstat == "running":
                    icon = f"[bold cyan]▶[/bold cyan] [yellow]({patt}/3)[/yellow]"
                elif pstat == "failed":
                    icon = "[bold red]✖[/bold red]"
                else:
                    icon = "[dim]◻[/dim]"
                content.append(f" {icon} [white]{escape(pname[:24])}[/white]")
            if len(t.phases) > 5:
                content.append(f" [dim]+ {len(t.phases) - 5} more phases[/dim]")

        # 3. Living memory / schemas
        if t.storage_schema or t.ui_surface:
            mem_summary = t.storage_schema or t.ui_surface
            content.append(f"[bold #38bdf8]MEMORY:[/bold #38bdf8] [dim]{escape(mem_summary[:26])}[/dim]")

        return Panel(
            "\n".join(content).strip(),
            title="[bold white]Workflow[/bold white]",
            border_style="#06b6d4",
            padding=(0, 1),
        )

    def render_logs(self, max_display_lines: int = 9) -> Panel:
        """Render Right Main Pane: Streaming Container Logs & Execution Telemetry."""
        t = self.telemetry
        lines = t.log_lines

        if not lines:
            display_text = "[dim]Waiting for container or agent execution logs...[/dim]"
        else:
            if t.scroll_offset > 0:
                end_idx = len(lines) - t.scroll_offset
                start_idx = max(0, end_idx - max_display_lines)
                visible_lines = lines[start_idx:end_idx]
            else:
                visible_lines = lines[-max_display_lines:]

            formatted_lines: list[str] = []
            for line in visible_lines:
                # Syntax highlight command invocations, test passes, and errors
                if line.startswith("$") or "Command:" in line:
                    formatted_lines.append(f"[bold cyan]{escape(line)}[/bold cyan]")
                elif "PASSED" in line or "Exit: 0" in line or "Exit Code: 0" in line:
                    formatted_lines.append(f"[bold green]{escape(line)}[/bold green]")
                elif "FAILED" in line or "ERROR" in line or "Error:" in line or "exit_code: 1" in line:
                    formatted_lines.append(f"[bold red]{escape(line)}[/bold red]")
                elif "warning" in line.lower():
                    formatted_lines.append(f"[yellow]{escape(line)}[/yellow]")
                elif line.startswith("↳"):
                    formatted_lines.append(f"[dim]{escape(line)}[/dim]")
                else:
                    formatted_lines.append(escape(line))

            display_text = "\n".join(formatted_lines)

        footer = f"[dim]Lines: {len(lines)}[/dim]"
        return Panel(
            display_text,
            title="[bold white]🐳 Container & Execution Telemetry[/bold white]",
            subtitle=footer,
            border_style="#ffa76c",
            padding=(0, 1),
        )

    def render_dock(self) -> Panel:
        """Render Bottom Interactive Dock & Command Shortcuts."""
        t = self.telemetry
        spinner = SPINNER_FRAMES[self._spinner_idx % len(SPINNER_FRAMES)]
        if t.awaiting_input:
            action_line = "[bold black on #f59e0b] 🔔 ATTENTION REQUIRED [/bold black on #f59e0b] [bold yellow]Provide input or press [Enter] to accept default[/bold yellow]"
            border_style = "#f59e0b"
            title = "[bold #f59e0b]⚡ Awaiting User Input[/bold #f59e0b]"
        else:
            action_line = f"[bold cyan]▶ {spinner}[/bold cyan] [white]{escape(t.current_action)}[/white]"
            border_style = "#ec4899"
            title = "[bold white]Interactive Dock[/bold white]"

        shortcuts = "[dim][P] Preview  [V] Verify  [D] Dana  [L] Logs  [Q] Exit[/dim]"
        content = f"{action_line}   {shortcuts}"
        return Panel(
            content,
            title=title,
            border_style=border_style,
            padding=(0, 1),
        )

    def start(self, screen: bool = False) -> None:
        """Activate the Live TUI dashboard if enabled and in an interactive TTY."""
        if not is_tui_enabled():
            return
        if not sys.stdout.isatty():
            return
        if self._live is not None and self._live.is_started:
            return

        self._screen = screen
        self._is_active = True
        self._live = Live(
            self.make_layout(),
            console=self.console,
            screen=screen,
            refresh_per_second=4,
            auto_refresh=True,
        )
        self._live.start()
        self._ticker_stop_event.clear()
        if self._ticker_thread is None or not self._ticker_thread.is_alive():
            self._ticker_thread = threading.Thread(target=self._ticker_loop, daemon=True)
            self._ticker_thread.start()

    def stop(self) -> None:
        """Stop the live TUI dashboard and cleanly restore the terminal screen."""
        self._is_active = False
        self._ticker_stop_event.set()
        if self._ticker_thread is not None and self._ticker_thread.is_alive():
            try:
                self._ticker_thread.join(timeout=0.2)
            except Exception:
                pass
            self._ticker_thread = None
        if self._live is not None:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None

    def refresh(self) -> None:
        """Trigger an immediate layout update on the live dashboard."""
        if self._pause_depth > 0:
            return
        if self._live is not None and self._live.is_started:
            try:
                self._live.update(self.make_layout(), refresh=True)
            except Exception:
                pass

    def suspend(self) -> bool:
        """Suspend live rendering and return True if it was active."""
        if self._is_active and self._live is not None and self._live.is_started:
            try:
                self._live.stop()
            except Exception:
                pass
            return True
        return False

    def resume(self) -> None:
        """Resume live rendering if cockpit is active and not in a nested pause."""
        if self._is_active and self._pause_depth == 0:
            try:
                self._live = Live(
                    self.make_layout(),
                    console=self.console,
                    screen=getattr(self, "_screen", False),
                    refresh_per_second=4,
                    auto_refresh=True,
                )
                self._live.start()
            except Exception:
                pass
            if self._ticker_thread is None or not self._ticker_thread.is_alive():
                self._ticker_stop_event.clear()
                self._ticker_thread = threading.Thread(target=self._ticker_loop, daemon=True)
                self._ticker_thread.start()

    @contextmanager
    def live_context(self, screen: bool = False):
        """Context manager to start and cleanly stop the live TUI dashboard."""
        self.start(screen=screen)
        try:
            yield self
        finally:
            self.stop()

    @contextmanager
    def pause(self):
        """Temporarily suspend live rendering for clean stdin/interactive gate prompts.

        Re-entrant and reference-counted so nested pauses do not prematurely resume
        or spawn duplicate Live instances.
        """
        was_active_at_root = False
        if self._pause_depth == 0:
            was_active_at_root = self.suspend()
        self._pause_depth += 1
        try:
            yield
        finally:
            self._pause_depth -= 1
            if self._pause_depth == 0 and was_active_at_root:
                self.resume()

    def run_standalone(
        self,
        project_id: str,
        workspace_root: str | Path = "workspace",
        input_func: Callable[[str], str] | None = None,
    ) -> None:
        """Launch a standalone interactive Cockpit session for a project."""
        self.telemetry.project_id = project_id
        self.telemetry.task_id = f"cockpit-{project_id}"
        self.telemetry.current_action = f"Interactive Cockpit active for project: {project_id}"

        # Load living memory profile if available
        ws_path = Path(workspace_root) / project_id
        profile_path = ws_path / "PROJECT_PROFILE.md"
        if profile_path.is_file():
            content = profile_path.read_text(encoding="utf-8")
            if "## Active Data Schemas" in content:
                self.telemetry.storage_schema = "Active Schemas Defined"
            if "## User Input Surfaces" in content:
                self.telemetry.ui_surface = "Configured Entry Surface"

        # Load recent logs from .state/task.log if present
        log_path = Path(".state") / "task.log"
        if log_path.is_file():
            try:
                recent_lines = log_path.read_text(encoding="utf-8").splitlines()[-50:]
                for line in recent_lines:
                    self.telemetry.add_log(line)
            except Exception:
                pass

        ask = input_func or input

        if not sys.stdout.isatty() and input_func is None:
            # Non-TTY fallback: print static layout once
            self.console.print(self.make_layout())
            return

        self.start(screen=True)
        try:
            while True:
                with self.pause():
                    try:
                        cmd = ask(f"[{project_id}] cockpit > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        break

                if not cmd:
                    continue
                lowered = cmd.lower()
                if lowered in ("q", "quit", "exit", "/exit"):
                    break
                elif lowered in ("p", "preview", "/preview"):
                    self.telemetry.current_action = "Launching UI Preview server..."
                    self.telemetry.preview_url = "http://localhost:8080"
                    self.telemetry.add_log("[System] Preview server active at http://localhost:8080")
                elif lowered in ("v", "verify", "/verify"):
                    self.telemetry.current_action = "Running Tier 2 Live Verification..."
                    self.telemetry.add_log(f"[System] Executing Tier 2 smoke verification for {project_id}...")
                elif lowered in ("c", "clear"):
                    self.telemetry.clear_logs()
                elif lowered in ("u", "up"):
                    self.telemetry.scroll_up(10)
                elif lowered in ("d", "down"):
                    self.telemetry.scroll_down(10)
                else:
                    self.telemetry.current_action = f"Command: {cmd}"
                    self.telemetry.add_log(f"[{project_id}] > {cmd}")
                self.refresh()
        finally:
            self.stop()
            self.console.print(f"[bold green]✔ Cockpit closed for project: {project_id}[/bold green]")


# Global singleton instance
_global_cockpit: BuildRelayCockpit | None = None


def get_cockpit() -> BuildRelayCockpit:
    """Access the global BuildRelay cockpit instance."""
    global _global_cockpit
    if _global_cockpit is None:
        _global_cockpit = BuildRelayCockpit()
    return _global_cockpit


def reset_cockpit() -> BuildRelayCockpit:
    """Reset the global cockpit instance (useful in test teardown)."""
    global _global_cockpit
    if _global_cockpit is not None:
        _global_cockpit.stop()
    _global_cockpit = BuildRelayCockpit()
    return _global_cockpit

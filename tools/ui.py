"""Terminal UI and Rich styling helpers for BuildRelay."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterable

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from tools.cockpit import BuildRelayCockpit, CockpitTelemetry, get_cockpit, is_tui_enabled

console = Console(highlight=False)

AGENT_THEMES: dict[str, dict[str, str]] = {
    "natasha": {"name": "Natasha", "color": "bold #d946ef", "icon": "🟣", "role": "Coordinator"},
    "odin": {"name": "Odin", "color": "bold #06b6d4", "icon": "🔵", "role": "Researcher"},
    "taghi": {"name": "Taghi", "color": "bold #22c55e", "icon": "🟢", "role": "Architect"},
    "diba": {"name": "Diba", "color": "bold #ec4899", "icon": "🎨", "role": "UI/UX Designer"},
    "meti": {"name": "Meti", "color": "bold #ffa76c", "icon": "🟠", "role": "Implementer"},
    "dana": {"name": "Dana", "color": "bold #a855f7", "icon": "🧭", "role": "Quality Supervisor"},
    "docker": {"name": "Docker", "color": "bold #38bdf8", "icon": "🐳", "role": "Sandbox"},
    "orchestrator": {"name": "BuildRelay", "color": "bold #818cf8", "icon": "⚡", "role": "System"},
    "resume": {"name": "Resume", "color": "bold #eab308", "icon": "🔄", "role": "Recovery"},
}


def _get_theme(agent_key: str) -> dict[str, str]:
    normalized = agent_key.lower().strip()
    return AGENT_THEMES.get(
        normalized,
        {"name": agent_key, "color": "bold white", "icon": "•", "role": "Agent"},
    )


def _ask_with_cockpit(raw_func: Callable[[str], str] | None = None) -> Callable[[str], str]:
    """Wrap an input function so that active cockpit dashboard alerts and pauses during user interaction."""
    import sys
    fn = raw_func or input

    def ask(prompt: str) -> str:
        from tools.cockpit import get_cockpit
        cockpit = get_cockpit()
        cockpit.telemetry.awaiting_input = True
        cockpit.telemetry.current_action = f"Awaiting input: {prompt.strip() or 'Press Enter or choose option'}"
        if getattr(cockpit, "_pause_depth", 0) == 0:
            cockpit.refresh()
        try:
            with cockpit.pause():
                try:
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                except Exception:
                    pass

                # Flush any pending/buffered keystrokes pressed while LLM or Docker was processing
                if sys.stdin.isatty():
                    try:
                        import termios
                        termios.tcflush(sys.stdin, termios.TCIFLUSH)
                    except Exception:
                        pass

                clean_prompt = prompt.strip()
                prompt_display = f" [bold]{clean_prompt}[/bold]" if clean_prompt else ""

                # Explicitly close style and emit ANSI reset before input() to prevent BCE orange bar
                console.print(
                    f"\n[bold black on #f59e0b] 🔔 ACTION REQUIRED [/bold black on #f59e0b]{prompt_display}\033[0m",
                    end=" ",
                )
                sys.stdout.flush()
                try:
                    sys.stdout.write("\033[0m")
                    sys.stdout.flush()
                except Exception:
                    pass

                return fn("")
        finally:
            if getattr(cockpit, "_pause_depth", 0) == 0:
                cockpit.telemetry.awaiting_input = False
                cockpit.refresh()

    return ask


def print_agent(agent: str, message: str, detail: str | None = None) -> None:
    """Print a role-badged message with agent icon and color."""
    from tools.cockpit import get_cockpit
    cockpit = get_cockpit()
    if cockpit.is_active:
        cockpit.telemetry.update_stage(agent, "running")
        cockpit.telemetry.set_action(f"[{agent.upper()}] {message}")
        cockpit.telemetry.add_log(f"[{agent.upper()}] {message}")
        if detail:
            cockpit.telemetry.add_log(f"   {detail}")
        cockpit.refresh()
        return

    theme = _get_theme(agent)
    console.print(f"[{theme['color']}]{theme['icon']} \\[{escape(theme['name'])}\\][/] {escape(message)}")
    if detail:
        console.print(f"   [dim]{escape(detail)}[/dim]")


def print_tool_call(agent: str, action: str, detail: str) -> None:
    """Print a subtle, dimmed tool invocation line to prevent clutter."""
    from tools.cockpit import get_cockpit
    cockpit = get_cockpit()
    if cockpit.is_active:
        cockpit.telemetry.add_log(f"↳ [{agent}] {action}: {detail}")
        cockpit.refresh()
        return

    theme = _get_theme(agent)
    detail_str = str(detail).strip()
    lines = detail_str.splitlines()

    if len(lines) > 1:
        # Check if the command is writing files (e.g. cat > file <<EOF or tee file)
        import re
        from pathlib import Path
        written_files = re.findall(
            r"(?:cat\s*>\s*|cat\s*<<['\"]?\w+['\"]?\s*>\s*|tee\s+)([^\s<>&|;'\"]+)",
            detail_str,
        )
        if written_files:
            file_names = [Path(f).name for f in written_files if Path(f).name]
            files_str = ", ".join(file_names[:3])
            if len(file_names) > 3:
                files_str += f" (+{len(file_names) - 3} more)"
            first_cmd = lines[0].strip()
            if first_cmd.startswith("mkdir"):
                summary = f"Scaffolding & writing {files_str} ({len(lines)} lines)"
            else:
                summary = f"Writing {files_str} ({len(lines)} lines)"
        else:
            first_line = lines[0].strip()
            summary = f"{first_line[:70]}... (+{len(lines) - 1} lines)"
    else:
        summary = detail_str[:100] + ("..." if len(detail_str) > 100 else "")

    console.print(f"   [dim]↳ \\[{escape(theme['name'])}\\] {escape(action)}: {escape(summary)}[/dim]")


@contextmanager
def agent_status(agent: str, message: str):
    """Display an animated spinner with the agent's role icon and theme."""
    from tools.cockpit import get_cockpit
    cockpit = get_cockpit()
    if cockpit.is_active:
        cockpit.telemetry.set_action(f"[{agent.upper()}] {message}")
        cockpit.refresh()
        yield None
        return

    theme = _get_theme(agent)
    status_text = f"[{theme['color']}]{theme['icon']} [{escape(theme['name'])}][/] {escape(message)}"
    status = console.status(status_text, spinner="dots")
    status.start()
    try:
        yield status
    finally:
        status.stop()


def print_task_header(
    task_id: str, prompt: str, project_id: str | None = None, is_resume: bool = False
) -> None:
    """Render a clean launch or resume header panel."""
    title = "🔄 BuildRelay — Task Resume" if is_resume else "⚡ BuildRelay — Task Launch"
    border_style = "#eab308" if is_resume else "#ffa76c"

    lines = [f"[bold]Task ID:[/bold]  [cyan]{task_id}[/cyan]"]
    if project_id:
        lines.append(f"[bold]Project:[/bold]  [green]{project_id}[/green]")
    lines.append(f"[bold]Prompt:[/bold]   {prompt}")

    panel = Panel(
        "\n".join(lines),
        title=f"[bold]{title}[/bold]",
        title_align="left",
        border_style=border_style,
        padding=(1, 2),
    )
    console.print()
    console.print(panel)


def print_brief_summary(
    target_lead: str,
    questions: list[str],
    token_usage: dict[str, Any] | None = None,
    model: str | None = None,
) -> None:
    """Display Natasha's routing decision in a compact box."""
    from tools.cockpit import get_cockpit
    cockpit = get_cockpit()
    if cockpit.is_active:
        cockpit.telemetry.update_stage("natasha", "passed", detail=target_lead)
        cockpit.telemetry.update_stage(target_lead, "running")
        cockpit.telemetry.add_log(f"[NATASHA] Routed task to {target_lead.upper()}")
        if token_usage:
            cockpit.telemetry.record_token_usage(token_usage, model)
        cockpit.refresh()
        return

    lead_theme = _get_theme(target_lead)
    content = f"[bold]Assigned Lead:[/bold] [{lead_theme['color']}]{lead_theme['icon']} {lead_theme['name']} ({lead_theme['role']})[/]\n"
    if token_usage:
        from tools.token_analytics import format_token_badge

        content += f"[bold]Tokens Used:[/bold]   [yellow]{format_token_badge(token_usage, model)}[/yellow]\n"
    if questions:
        content += "[bold]Key Questions:[/bold]\n" + "\n".join(f"  • [dim]{q}[/dim]" for q in questions)
    console.print(
        Panel(
            content.strip(),
            title="[bold magenta]🟣 Task Brief & Routing[/bold magenta]",
            title_align="left",
            border_style="#d946ef",
            padding=(0, 2),
        )
    )


def print_spec_summary(
    base_image: str | None,
    phases: list[Any],
    token_usage: dict[str, Any] | None = None,
    model: str | None = None,
) -> None:
    """Display Taghi's execution roadmap in a styled summary."""
    from tools.cockpit import get_cockpit
    cockpit = get_cockpit()
    if cockpit.is_active:
        cockpit.telemetry.update_stage("taghi", "passed")
        cockpit.telemetry.set_phases(phases)
        cockpit.telemetry.add_log(f"[TAGHI] Generated specification with {len(phases)} execution phases")
        if token_usage:
            cockpit.telemetry.record_token_usage(token_usage, model)
        cockpit.refresh()
        return

    image = base_image or "node:18-bullseye-slim (default)"
    header = f"[bold]Runtime Image:[/bold] [cyan]{image}[/cyan]\n"
    if token_usage:
        from tools.token_analytics import format_token_badge

        header += f"[bold]Tokens Used:[/bold]   [yellow]{format_token_badge(token_usage, model)}[/yellow]\n"
    header += f"[bold]Execution Roadmap ({len(phases)} phases):[/bold]\n"
    phase_lines = []
    for idx, phase in enumerate(phases, start=1):
        name = getattr(phase, "phase_name", str(phase))
        cmd = getattr(phase, "validation_command", "")
        phase_lines.append(f"  [green]{idx}.[/green] [bold]{name}[/bold] [dim]→ `{cmd}`[/dim]")
    content = header + "\n".join(phase_lines)
    console.print(
        Panel(
            content.strip(),
            title="[bold green]🟢 Technical Architecture & Roadmap[/bold green]",
            title_align="left",
            border_style="#22c55e",
            padding=(0, 2),
        )
    )


def print_phase_table(
    phases: list[Any],
    completed_phases: Iterable[str] = (),
    current_phase: str | None = None,
    failed_phase: str | None = None,
) -> None:
    """Render a structured status table for all execution phases."""
    from tools.cockpit import get_cockpit
    cockpit = get_cockpit()
    if cockpit.is_active:
        cockpit.telemetry.set_phases(phases)
        completed_set = set(completed_phases or ())
        for p in phases:
            name = (
                getattr(p, "phase_name", None)
                or (p.get("phase_name") if isinstance(p, dict) else str(p))
            )
            if name in completed_set:
                cockpit.telemetry.update_phase(name, "passed")
            elif name == failed_phase:
                cockpit.telemetry.update_phase(name, "failed")
            elif name == current_phase:
                cockpit.telemetry.update_phase(name, "running")
        cockpit.refresh()
        return
    table = Table(
        title="[bold #ffa76c]Execution & Validation Phases[/bold #ffa76c]",
        title_justify="left",
        border_style="dim",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Phase", style="bold", min_width=20)
    table.add_column("Validation Command", style="cyan", min_width=30)
    table.add_column("Status", justify="center", width=14)

    completed_set = set(completed_phases)
    for idx, phase in enumerate(phases, start=1):
        name = getattr(phase, "phase_name", str(phase))
        cmd = getattr(phase, "validation_command", "")

        if name in completed_set:
            status = "[bold green]✓ PASSED[/bold green]"
        elif name == failed_phase:
            status = "[bold red]✗ FAILED[/bold red]"
        elif name == current_phase:
            status = "[bold yellow]RUNNING[/bold yellow]"
        else:
            status = "[dim]PENDING[/dim]"

        table.add_row(str(idx), name, cmd, status)

    console.print()
    console.print(table)
    console.print()


def print_completion(task_id: str, success: bool, summary: str) -> None:
    """Render the final outcome panel with resume hints if failed."""
    if success:
        panel = Panel(
            f"[bold green]✓ All phases validated successfully![/bold green]\n\n{summary}",
            title=f"[bold green]⚡ Workflow Completed — {task_id}[/bold green]",
            title_align="left",
            border_style="green",
            padding=(1, 2),
        )
    else:
        panel = Panel(
            f"[bold red]✗ Workflow did not complete successfully.[/bold red]\n\n"
            f"{summary}\n\n"
            f"[bold yellow]To resume from saved checkpoints:[/bold yellow]\n"
            f"  [cyan]python main.py --resume {task_id}[/cyan]",
            title=f"[bold red]⚡ Workflow Incomplete — {task_id}[/bold red]",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )
    console.print()
    console.print(panel)
    console.print()


def print_token_summary_table(
    token_usage_dict: dict[str, dict[str, Any]],
    default_model: str | None = None,
) -> None:
    """Render a structured token usage and cost table broken down per lead."""
    from tools.token_analytics import calculate_token_cost

    table = Table(
        title="[bold #818cf8]Token Usage & Cost Summary[/bold #818cf8]",
        title_justify="left",
        border_style="dim",
        padding=(0, 1),
    )
    table.add_column("Lead", style="bold", min_width=18)
    table.add_column("Prompt Tokens", justify="right", min_width=16)
    table.add_column("Completion Tokens", justify="right", min_width=18)
    table.add_column("Total Tokens", justify="right", min_width=14)
    table.add_column("Est. Cost", justify="right", min_width=14)

    total_prompt = 0
    total_completion = 0
    total_tokens = 0
    total_cost: float = 0.0
    all_numeric_cost = True

    lead_order = ["natasha", "odin", "taghi", "meti"]
    for k in token_usage_dict:
        if k not in lead_order:
            lead_order.append(k)

    for lead_key in lead_order:
        usage = token_usage_dict.get(lead_key)
        if not usage:
            continue
        theme = _get_theme(lead_key)
        lead_label = f"[{theme['color']}]{theme['icon']} {theme['name']}[/]"

        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        tot = usage.get("total_tokens", inp + out)
        model = usage.get("model") or default_model

        cost_val, cost_display = calculate_token_cost(inp, out, model)
        if cost_val is not None:
            total_cost += cost_val
        else:
            all_numeric_cost = False

        total_prompt += inp
        total_completion += out
        total_tokens += tot

        table.add_row(
            lead_label,
            f"{inp:,}",
            f"{out:,}",
            f"{tot:,}",
            f"[green]{cost_display}[/green]" if "$" in cost_display else f"[dim]{cost_display}[/dim]",
        )

    if total_tokens > 0:
        table.add_section()
        if all_numeric_cost:
            total_cost_str = f"${total_cost:.4f}" if total_cost < 0.001 else f"${total_cost:.3f}"
        else:
            total_cost_str = "--"
        table.add_row(
            "[bold white]Total[/bold white]",
            f"[bold]{total_prompt:,}[/bold]",
            f"[bold]{total_completion:,}[/bold]",
            f"[bold yellow]{total_tokens:,}[/bold yellow]",
            f"[bold green]{total_cost_str}[/bold green]"
            if "$" in total_cost_str
            else f"[bold dim]{total_cost_str}[/bold dim]",
        )

    console.print()
    console.print(table)
    console.print()


def print_workspace_tree(workspace_path: str | Path, max_depth: int = 3) -> None:
    """Print a formatted rich.tree.Tree of all generated project files."""
    path = Path(workspace_path)
    if not path.exists():
        return

    tree = Tree(f"[bold blue]📁 {path.name}/[/bold blue]")
    ignore_dirs = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".DS_Store",
    }

    def _build_tree(current_dir: Path, current_node: Tree, depth: int) -> None:
        if depth > max_depth:
            current_node.add("[dim]... (truncated)[/dim]")
            return

        try:
            entries = sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return

        for entry in entries:
            if entry.name in ignore_dirs or entry.name.startswith("."):
                continue
            if entry.is_dir():
                sub_node = current_node.add(f"[bold #38bdf8]📁 {entry.name}/[/bold #38bdf8]")
                _build_tree(entry, sub_node, depth + 1)
            else:
                current_node.add(f"[white]📄 {entry.name}[/white]")

    _build_tree(path, tree, depth=1)
    console.print(tree)
    console.print()


def print_how_to_run(
    workspace_path: str | Path,
    run_cmd: str | None = None,
    test_cmd: str | None = None,
    entry_point: str | None = None,
) -> None:
    """Render a prominent Rich banner showing how to run and test the project."""
    path = Path(workspace_path)

    # Auto-detect test command if not provided
    if test_cmd is None:
        if (path / "package.json").exists():
            test_cmd = "npm test"
        elif (path / "Cargo.toml").exists():
            test_cmd = "cargo test"
        elif (path / "go.mod").exists():
            test_cmd = "go test ./..."
        else:
            test_cmd = "pytest"

    # Auto-detect run command and entry point if not provided
    if run_cmd is None:
        if (path / "package.json").exists():
            run_cmd = "npm start"
            entry_point = entry_point or "index.js"
        elif (path / "Cargo.toml").exists():
            run_cmd = "cargo run"
            entry_point = entry_point or "src/main.rs"
        elif (path / "go.mod").exists():
            run_cmd = "go run ."
            entry_point = entry_point or "main.go"
        elif (path / "src" / "main.py").exists():
            run_cmd = "python -m src.main"
            entry_point = entry_point or "src/main.py"
        elif (path / "main.py").exists():
            run_cmd = "python main.py"
            entry_point = entry_point or "main.py"
        elif (path / "app.py").exists():
            run_cmd = "python app.py"
            entry_point = entry_point or "app.py"
        else:
            run_cmd = f"python main.py"
            entry_point = entry_point or "main.py"

    content_lines = [
        f"[bold]Workspace:[/bold]  [cyan]{path}[/cyan]",
        f"[bold]Run:[/bold]        [green]{run_cmd}[/green]",
        f"[bold]Test:[/bold]       [yellow]{test_cmd}[/yellow]",
    ]
    if entry_point:
        content_lines.append(f"[bold]Entry:[/bold]      [magenta]{entry_point}[/magenta]")

    live_smoke_cmd = None
    if (path / "scripts" / "verify_live.py").exists():
        live_smoke_cmd = "python scripts/verify_live.py"
    elif (path / "scripts" / "verify.py").exists():
        live_smoke_cmd = "python scripts/verify.py"
    elif (path / "scripts" / "verify.js").exists():
        live_smoke_cmd = "node scripts/verify.js"
    elif (path / "dist" / "Code.gs").exists():
        live_smoke_cmd = "Run testDirectSync() in Apps Script"

    if live_smoke_cmd:
        content_lines.append(f"[bold]Tier 2 Smoke:[/bold] [cyan]{live_smoke_cmd}[/cyan]")

    panel = Panel(
        "\n".join(content_lines),
        title="[bold green]🚀 How to Run & Test[/bold green]",
        title_align="left",
        border_style="#22c55e",
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


def print_alignment_brief(brief: Any) -> None:
    """Render the 5-sentence structured Task Alignment Brief panel."""
    ab = getattr(brief, "alignment_brief", None)
    if not ab:
        return

    lines = ab.to_lines() if hasattr(ab, "to_lines") else []
    if not lines and isinstance(ab, dict):
        lines = [
            ("1. Goal:", ab.get("goal", "")),
            ("2. Features:", ab.get("core_features", "")),
            ("3. Stack:", ab.get("tech_stack", "")),
            ("4. Exclusions:", ab.get("exclusions", "")),
            ("5. Next Steps:", ab.get("next_actions", "")),
        ]

    content_lines = []
    for label, val in lines:
        content_lines.append(f"[bold #38bdf8]{label:<15}[/bold #38bdf8] {escape(val)}")

    panel = Panel(
        "\n".join(content_lines),
        title="[bold #d946ef]🎯 Task Alignment Brief[/bold #d946ef]",
        title_align="left",
        border_style="#d946ef",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)


def prompt_alignment_gate(
    brief: Any,
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, str | None, dict[str, str]]:
    """
    Present the 5-sentence brief and any clarification questions.
    Returns: (action, feedback_text, selected_answers)
      action: 'confirm' | 'edit' | 'quit'
    """
    import sys

    # Always render the alignment brief panel
    print_alignment_brief(brief)

    # Collect default answers
    questions = getattr(brief, "clarification_questions", []) or []
    answers: dict[str, str] = {}
    for q in questions:
        for opt in getattr(q, "options", []):
            if getattr(opt, "is_default", False):
                answers[getattr(q, "id", str(q))] = getattr(opt, "label", getattr(opt, "key", ""))
                break

    # If headless / automated / non-interactive: automatically proceed with defaults
    ask = _ask_with_cockpit(input_func)
    if auto or (input_func is None and not sys.stdin.isatty()):
        return "confirm", None, answers

    # Render clarification questions if present
    if questions:
        console.print(
            "[bold yellow]⚡ Clarification Questions[/bold yellow] [dim](Press Enter to accept defaults):[/dim]"
        )
        for idx, q in enumerate(questions, start=1):
            q_text = getattr(q, "question", str(q))
            console.print(f"  [bold cyan]{idx}. {escape(q_text)}[/bold cyan]")
            for opt in getattr(q, "options", []):
                key = getattr(opt, "key", "")
                lbl = getattr(opt, "label", "")
                is_def = getattr(opt, "is_default", False)
                def_tag = " [bold green](Default)[/bold green]" if is_def else ""
                console.print(f"     [bold cyan]\\[{escape(str(key))}][/bold cyan] {escape(lbl)}{def_tag}")
        console.print()

    console.print(
        "[bold]👉 Action:[/bold] "
        "[green]\\[Y/enter][/green] Confirm Defaults  |  "
        "[cyan]\\[1, 2...][/cyan] Pick Option  |  "
        "[yellow]\\[e][/yellow] Edit / Custom  |  "
        "[red]\\[q][/red] Quit"
    )
    try:
        user_choice = ask("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quit", None, {}

    low = user_choice.lower()
    if low in ("", "y", "yes"):
        return "confirm", None, answers
    if low in ("q", "quit", "exit"):
        return "quit", None, {}
    if low in ("e", "edit"):
        try:
            feedback = ask("📝 Describe intent changes / clarifications: ").strip()
            return "edit", feedback or "User requested intent review.", answers
        except (EOFError, KeyboardInterrupt):
            return "quit", None, {}

    # Check if user typed a specific option number / key (e.g. "2" or "b")
    matched_opt = None
    matched_q = None
    for q in questions:
        for opt in getattr(q, "options", []):
            if str(getattr(opt, "key", "")).strip().lower() == low:
                matched_opt = opt
                matched_q = q
                break
        if matched_opt:
            break

    if matched_opt and matched_q:
        opt_key = getattr(matched_opt, "key", user_choice)
        opt_label = getattr(matched_opt, "label", "")
        q_id = getattr(matched_q, "id", str(matched_q))
        q_text = getattr(matched_q, "question", "requirement")
        answers[q_id] = opt_label
        console.print(f"   [bold green]✔ Selected option \\[{opt_key}]: {escape(opt_label)}[/bold green]")
        feedback = f"Selected option [{opt_key}] {opt_label} for '{q_text}'."
        return "edit", feedback, answers

    # Freeform user input treated as modification/clarification
    console.print(f"   [dim]↳ Applying modification: {escape(user_choice)}[/dim]")
    return "edit", user_choice, answers


def prompt_step_gate(
    stage_name: str,
    summary_text: str,
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, str | None]:
    """
    Step gate confirmation for --step mode before executing a lead.
    Returns: ('confirm' | 'pivot' | 'quit', feedback_text)
    """
    import sys

    theme = _get_theme(stage_name)
    panel = Panel(
        summary_text.strip(),
        title=f"[{theme['color']}]{theme['icon']} Step Gate: {theme['name']} ({theme['role']})[/{theme['color']}]",
        title_align="left",
        border_style=theme["color"].split()[-1] if " " in theme["color"] else theme["color"],
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    ask = _ask_with_cockpit(input_func)
    if auto or (input_func is None and not sys.stdin.isatty()):
        return "confirm", None

    console.print(
        f"[bold]Proceed to {theme['name']}?[/bold] [green]\\[Y/enter][/green] Proceed  |  "
        f"[yellow]\\[e][/yellow] Pivot / Re-route  |  [red]\\[q][/red] Abort"
    )
    try:
        choice = ask("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quit", None

    low = choice.lower()
    if low in ("", "y", "yes"):
        return "confirm", None
    if low in ("q", "quit", "exit"):
        return "quit", None
    if low in ("e", "edit", "pivot"):
        try:
            feedback = ask("📝 Describe intent pivot: ").strip()
            return "pivot", feedback
        except (EOFError, KeyboardInterrupt):
            return "quit", None

    return "pivot", choice


def print_ui_spec_proposal_card(ui_spec: Any) -> None:
    """Render Taghi's dedicated UI/UX visual design specification card."""
    if not ui_spec:
        return

    surface_type = getattr(ui_spec, "surface_type", "web_form")
    theme_name = getattr(ui_spec, "theme", "modern_dark")
    palette = getattr(ui_spec, "color_palette", {}) or {}
    layout = getattr(ui_spec, "component_layout", "")
    fields = getattr(ui_spec, "form_fields", []) or []
    states = getattr(ui_spec, "states", {}) or {}
    responsive = getattr(ui_spec, "responsive_breakpoints", "")

    lines = [
        f"[bold white]🎨 UI Surface & Theme:[/bold white]   [cyan]{escape(str(surface_type))}[/cyan]  |  [yellow]{escape(str(theme_name))}[/yellow]",
        f"[bold white]📱 Responsive Layout:[/bold white]    {escape(str(responsive))}\n",
    ]

    if palette:
        palette_tokens = "  ".join(f"[bold]{k}:[/bold] `{v}`" for k, v in list(palette.items())[:5])
        lines.append(f"[bold white]🎨 Design Palette Tokens:[/bold white]\n  {palette_tokens}\n")

    if layout:
        lines.append(f"[bold white]📐 Component Hierarchy & Wireframe:[/bold white]\n{escape(str(layout)[:400]) + ('...' if len(str(layout)) > 400 else '')}\n")

    if fields:
        lines.append(f"[bold white]📝 Form Fields & Input Constraints ({len(fields)} fields):[/bold white]")
        for f in fields[:6]:
            req = "[red]*[/red]" if getattr(f, "required", True) else "[dim](opt)[/dim]"
            f_id = getattr(f, "id", "field")
            f_label = getattr(f, "label", f_id)
            f_type = getattr(f, "input_type", "text")
            f_rules = getattr(f, "validation_rules", None)
            rule_str = f" [dim]({f_rules})[/dim]" if f_rules else ""
            lines.append(f"  • {req} [bold]{escape(str(f_label))}[/bold] [cyan]({f_type})[/cyan]{escape(rule_str)}")
        if len(fields) > 6:
            lines.append(f"  [dim]... and {len(fields) - 6} more fields[/dim]")
        lines.append("")

    if states:
        lines.append("[bold white]⚡ Dynamic UI States:[/bold white]")
        for st_name, st_desc in states.items():
            lines.append(f"  • [cyan]{escape(st_name.capitalize())}:[/cyan] {escape(str(st_desc))}")

    panel = Panel(
        "\n".join(lines).strip(),
        title="[bold #ec4899]🎨 Taghi — UI/UX Design & Ergonomics Specification[/bold #ec4899]",
        title_align="left",
        border_style="#ec4899",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)


def print_spec_proposal_card(spec: Any) -> None:
    """Render Taghi's full architectural proposal, input surface, and phase roadmap."""
    theme = _get_theme("taghi")
    overview = getattr(spec, "architecture_overview", "")
    clean_overview = "\n".join(
        line for line in overview.splitlines()
        if not line.startswith("Create your project directory at workspace/")
        and not line.startswith("All sandbox commands start in /app/workspace/")
    ).strip()

    input_spec = getattr(spec, "input_interface_spec", None)
    base_image = getattr(spec, "base_image", None) or "python:3.11-slim"
    phases = getattr(spec, "phases", []) or []
    deps = getattr(spec, "required_dependencies", []) or []

    content_lines = [
        f"[bold white]🏗 Architecture Overview:[/bold white]\n{escape(clean_overview[:600]) + ('...' if len(clean_overview) > 600 else '')}\n",
    ]
    if input_spec:
        content_lines.append(f"[bold white]👉 User Input Surface & Form Specification:[/bold white]\n{escape(input_spec)}\n")
    if deps:
        content_lines.append(f"[bold white]📦 Dependencies:[/bold white] [cyan]{escape(', '.join(deps))}[/cyan]")
    content_lines.append(f"[bold white]🐳 Base Runtime Image:[/bold white] [cyan]{escape(base_image)}[/cyan]\n")

    content_lines.append(f"[bold white]🚀 Execution Roadmap ({len(phases)} phases):[/bold white]")
    for idx, p in enumerate(phases, start=1):
        p_name = getattr(p, "phase_name", str(p))
        p_cmd = getattr(p, "validation_command", "")
        content_lines.append(f"  [green]{idx}.[/green] [bold]{escape(p_name)}[/bold] [dim]→ `{escape(p_cmd)}`[/dim]")

    live_guide = getattr(spec, "live_verification_guide", None)
    if live_guide:
        content_lines.append(f"\n[bold white]🧪 Tier 2: Live Verification Guide:[/bold white]\n{escape(live_guide)}")

    panel = Panel(
        "\n".join(content_lines),
        title=f"[{theme['color']}]{theme['icon']} Taghi Architectural Design Proposal[/{theme['color']}]",
        title_align="left",
        border_style="blue",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    ui_spec = getattr(spec, "ui_spec", None)
    if ui_spec:
        print_ui_spec_proposal_card(ui_spec)


def prompt_spec_approval_gate(
    spec: Any,
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, str | None]:
    """
    Approval gate for Taghi's architectural specification before Meti starts coding.
    Returns: ('confirm' | 'revise' | 'quit', feedback_text)
    """
    import sys

    print_spec_proposal_card(spec)

    ask = _ask_with_cockpit(input_func)
    if auto or (input_func is None and not sys.stdin.isatty()):
        return "confirm", None

    console.print(
        "[bold]👉 Architecture Approval Action:[/bold] "
        "[green]\\[Y/enter][/green] Approve Architecture & Begin Coding  |  "
        "[yellow]\\[e/r][/yellow] Edit / Revise Architecture & Fields  |  "
        "[red]\\[q][/red] Abort"
    )
    try:
        choice = ask("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quit", None

    low = choice.lower()
    if low in ("", "y", "yes"):
        return "confirm", None
    if low in ("q", "quit", "exit"):
        return "quit", None
    if low in ("r", "revise", "edit", "e"):
        try:
            feedback = ask("📝 Describe architectural / field / UI revisions needed:\n> ").strip()
            return "revise", feedback or "User requested architecture revisions."
        except (EOFError, KeyboardInterrupt):
            return "quit", None

    # Freeform text typed directly at prompt
    console.print(f"   [dim]↳ Requesting architecture revision: {escape(choice)}[/dim]")
    return "revise", choice


def prompt_delivery_gate(
    task_id: str,
    workspace_path: Path,
    summary_text: str,
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, str | None]:
    """
    Delivery review gate after Meti validates all phases, before final completion.
    Returns: ('confirm' | 'refine' | 'quit', feedback_text)
    """
    import sys

    theme = _get_theme("meti")
    rel_ws = str(workspace_path)
    try:
        rel_ws = str(workspace_path.relative_to(Path.cwd()))
    except ValueError:
        pass

    entry_lines = []
    if (workspace_path / "scripts" / "setup.js").exists():
        entry_lines.append("[bold cyan]Setup Wizard:[/bold cyan] node scripts/setup.js")
    elif (workspace_path / "setup.py").exists():
        entry_lines.append("[bold cyan]Setup Wizard:[/bold cyan] python setup.py")
    if (workspace_path / "scripts" / "input.js").exists():
        entry_lines.append("[bold cyan]Interactive Entry CLI:[/bold cyan] node scripts/input.js")
    elif (workspace_path / "input.py").exists():
        entry_lines.append("[bold cyan]Interactive Entry CLI:[/bold cyan] python input.py")
    if (workspace_path / "dist" / "Code.gs").exists():
        entry_lines.append("[bold cyan]Google Apps Script Engine:[/bold cyan] dist/Code.gs")
    if (workspace_path / "form.html").exists():
        entry_lines.append("[bold cyan]Web Entry Form:[/bold cyan] form.html")
    elif (workspace_path / "index.html").exists():
        entry_lines.append("[bold cyan]Web Interface:[/bold cyan] index.html")
    elif (workspace_path / "main.py").exists():
        entry_lines.append("[bold cyan]Application Entry:[/bold cyan] python main.py")

    entry_section = ""
    if entry_lines:
        entry_section = "\n[bold white]👉 User Input Surface & Entry Points:[/bold white]\n" + "\n".join(f"  • {e}" for e in entry_lines) + "\n"

    smoke_lines = []
    if (workspace_path / "scripts" / "verify_live.py").exists():
        smoke_lines.append("[bold green]Live Smoke Test:[/bold green] python scripts/verify_live.py")
    elif (workspace_path / "scripts" / "verify.py").exists():
        smoke_lines.append("[bold green]Live Smoke Test:[/bold green] python scripts/verify.py")
    if (workspace_path / "scripts" / "verify_live.sh").exists():
        smoke_lines.append("[bold green]Live Smoke Test:[/bold green] bash scripts/verify_live.sh")
    if (workspace_path / "scripts" / "verify.js").exists():
        smoke_lines.append("[bold green]Live Smoke Test:[/bold green] node scripts/verify.js")
    if (workspace_path / "dist" / "Code.gs").exists():
        try:
            code_gs = (workspace_path / "dist" / "Code.gs").read_text(encoding="utf-8", errors="ignore")
            if "testDirectSync" in code_gs:
                smoke_lines.append("[bold green]Apps Script Direct Sync:[/bold green] Select 'testDirectSync' in Apps Script editor dropdown & click Run")
            if "createGoogleForm" in code_gs:
                smoke_lines.append("[bold green]Apps Script Form Creator:[/bold green] Select 'createGoogleForm' in Apps Script editor dropdown & click Run")
        except Exception:
            pass

    smoke_section = ""
    if smoke_lines:
        smoke_section = "\n[bold white]🧪 Tier 2: Guided Live Verification Commands:[/bold white]\n" + "\n".join(f"  • {s}" for s in smoke_lines) + "\n"

    content = (
        f"[bold white]📦 Deliverables Ready in:[/bold white] [cyan]{escape(rel_ws)}[/cyan]\n"
        f"[bold white]🎯 Implementation Summary:[/bold white] {escape(summary_text)}\n"
        f"{entry_section}"
        f"{smoke_section}\n"
        "[dim]Review the generated files and instructions. If you would like simpler guides, "
        "visual charts, or code refinements, request them now before final delivery.[/dim]"
    )

    panel = Panel(
        content.strip(),
        title=f"[{theme['color']}]{theme['icon']} Meti Delivery Review: {escape(task_id)}[/{theme['color']}]",
        title_align="left",
        border_style="green",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    ask = _ask_with_cockpit(input_func)
    if auto or (input_func is None and not sys.stdin.isatty()):
        return "confirm", None

    console.print(
        "[bold]👉 Delivery Action:[/bold] "
        "[green]\\[Y/enter][/green] Accept & Complete  |  "
        "[yellow]\\[e/r][/yellow] Request Refinement / Edit (Docs/Code)  |  "
        "[red]\\[q][/red] Quit"
    )
    try:
        choice = ask("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "quit", None

    low = choice.lower()
    if low in ("", "y", "yes"):
        return "confirm", None
    if low in ("q", "quit", "exit"):
        return "quit", None
    if low in ("r", "refine", "edit", "e"):
        try:
            feedback = ask("📝 Describe refinements needed (e.g. clearer README, beginner guide, specific fixes):\n> ").strip()
            return "refine", feedback or "User requested documentation and usability refinement."
        except (EOFError, KeyboardInterrupt):
            return "quit", None

    # Freeform text typed directly at prompt
    console.print(f"   [dim]↳ Requesting refinement: {escape(choice)}[/dim]")
    return "refine", choice


def print_model_lineup_card(
    models: dict[str, Any],
    tier: str = "balanced",
    prompt_caching: bool = True,
    budget_estimate: str | None = None,
) -> None:
    """Render a clean card displaying the pipeline model lineup across all leads."""
    from tools.model_tiers import get_tier_label

    content_lines = []
    pairs = [
        (("natasha", "Natasha"), ("odin", "Odin")),
        (("taghi", "Taghi"), ("diba", "Diba")),
    ]
    if "dana" in models and models.get("dana"):
        pairs.append((("meti", "Meti"), ("dana", "Dana")))
    else:
        pairs.append((("meti", "Meti"), None))

    for left_lead, right_lead in pairs:
        t_left = _get_theme(left_lead[0])
        mdl_left = models.get(left_lead[0], "gpt-4o")
        lbl_left = get_tier_label(mdl_left)
        str_left = f"[{t_left['color']}]{t_left['icon']} {t_left['name']}:[/{t_left['color']}] [white]{escape(str(mdl_left))}[/white] [dim]({lbl_left})[/dim]"

        if right_lead:
            t_right = _get_theme(right_lead[0])
            mdl_right = models.get(right_lead[0], "gpt-4o")
            lbl_right = get_tier_label(mdl_right)
            str_right = f"[{t_right['color']}]{t_right['icon']} {t_right['name']}:[/{t_right['color']}] [white]{escape(str(mdl_right))}[/white] [dim]({lbl_right})[/dim]"
            content_lines.append(f"{str_left:<42}  {str_right}")
        else:
            content_lines.append(str_left)

    footer = f"\n[bold cyan]Selection:[/bold cyan] {'Per lead' if tier == 'manual' else tier.title()}  |  [bold yellow]Prompt Caching:[/bold yellow] {'Requested; provider-dependent' if prompt_caching else 'Disabled'}"
    if budget_estimate:
        footer += f"  |  [bold green]Est. Budget:[/bold green] {budget_estimate}"
    content_lines.append(footer)

    panel = Panel(
        "\n".join(content_lines),
        title="[bold #818cf8]⚙ Pipeline Model Configuration[/bold #818cf8]",
        title_align="left",
        border_style="#818cf8",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)


def prompt_model_approval_gate(
    models: dict[str, Any],
    tier: str = "balanced",
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """
    Confirm or edit per-lead models; persist changes only after explicit confirmation.
    Returns: ('confirm' | 'change' | 'quit', resolved_models)
    """
    import os
    import sys
    from tools.model_tiers import estimate_pipeline_budget, get_available_models_for_active_provider
    from tools.model_catalog import pick_model

    ask = _ask_with_cockpit(input_func)
    selected = dict(models)
    changed = False
    while True:
        _, budget = estimate_pipeline_budget(selected)
        print_model_lineup_card(selected, tier="manual", prompt_caching=True, budget_estimate=budget)
        if auto or (input_func is None and not sys.stdin.isatty()):
            return "confirm", selected
        try:
            choice = ask("Enter: continue | c: change a lead | q: quit > ").strip().lower()
            if choice in ("q", "quit", "exit"):
                return "quit", None
            if choice in ("", "y", "yes"):
                if changed:
                    save = ask("Save these assignments as defaults? [y/N] > ").strip().lower()
                    if save in ("y", "yes"):
                        from tools.onboarding import save_env_configuration
                        model_key = {"anthropic": "ANTHROPIC_MODEL", "gemini": "GEMINI_MODEL"}.get(os.environ.get("BUILDRELAY_PROVIDER"), "OPENAI_MODEL")
                        save_env_configuration({
                            **{f"MODEL_{lead.upper()}": str(value) for lead, value in selected.items()},
                            "BUILDRELAY_MODEL_MODE": "selected",
                            "BUILDRELAY_MODEL": str(selected["natasha"]),
                            model_key: str(selected["natasha"]).split(":", 1)[-1],
                        })
                return ("change" if changed else "confirm"), selected
            if choice not in ("c", "change"):
                console.print("Choose Enter, c, or q.")
                continue
            leads = list(selected)
            for idx, lead in enumerate(leads, 1):
                console.print(f"  [{idx}] {lead.title()}: {selected[lead]}")
            target = ask("Choose lead number (Enter returns) > ").strip()
            if not target:
                continue
            if not target.isdigit() or not 1 <= int(target) <= len(leads):
                console.print("Choose a listed lead number.")
                continue
            lead = leads[int(target) - 1]
            provider, catalog = get_available_models_for_active_provider()
            console.print(f"Models for {provider}. Cached catalog or saved choices; availability is not guaranteed.")
            def picker_ask(prompt, default=""):
                return ask(prompt + " > ")
            chosen = pick_model(catalog, str(selected[lead]), lead.title(), picker_ask, console.print)
            connection = os.environ.get("BUILDRELAY_PROVIDER")
            if connection:
                from tools.model_catalog import qualify_model
                try:
                    chosen = qualify_model(chosen, connection)
                except ValueError:
                    console.print("Choose a model from the selected connection.")
                    continue
            selected[lead] = chosen
            changed = selected != models
        except (EOFError, KeyboardInterrupt):
            return "quit", None


def prompt_iteration_gate(
    project_id: str,
    task_id: str,
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, str | None]:
    """
    Continuous feature iteration & enhancement gate after task completion.

    Provides interactive choices:
      [1] Add new feature / milestone (loops back to Natasha -> Taghi -> Meti within project)
      [2] Refactor or optimize existing code
      [3] Open interactive REPL session (buildrelay session <project_id>)
      [4] Run Tier 2 live verification or UI preview
      [5] Exit cleanly ([Enter] or [q])

    Returns:
      (action, payload) where:
        action is one of: 'feature', 'refactor', 'session', 'verify', 'preview', 'none', 'exit'
        payload is optional instruction or prompt string.
    """
    import os
    import sys

    ask = _ask_with_cockpit(input_func)
    if auto or (
        input_func is None
        and (not sys.stdin.isatty() or "pytest" in sys.modules or os.environ.get("BUILDRELAY_TESTING") == "1")
    ):
        return "exit", None

    content = (
        f"[bold white]Project ID:[/bold white]          [green]{escape(project_id)}[/green]\n"
        f"[bold white]Completed Milestone:[/bold white] [cyan]{escape(task_id)}[/cyan]\n"
        f"[bold white]Project Workspace:[/bold white]   [yellow]workspace/{escape(project_id)}[/yellow]\n\n"
        "[bold white]Continuous Enhancement Options:[/bold white]\n"
        "  [bold green][1][/bold green] 🚀 [bold]Add a new feature / milestone[/bold] [dim](Natasha → Taghi → Meti)[/dim]\n"
        "  [bold cyan][2][/bold cyan] ⚡ [bold]Refactor or optimize existing codebase[/bold]\n"
        "  [bold magenta][3][/bold magenta] 💬 [bold]Launch interactive Project REPL session[/bold] [dim](buildrelay session)[/dim]\n"
        "  [bold blue][4][/bold blue] 🧪 [bold]Run Tier 2 live verification or UI preview[/bold]\n"
        "  [bold dim][5][/bold dim] 🏁 [bold]Exit & complete workflow[/bold] [dim]([Enter] or [q])[/dim]"
    )
    panel = Panel(
        content.strip(),
        title="[bold #38bdf8]🔄 BuildRelay — Continuous Feature Iteration Gate[/bold #38bdf8]",
        title_align="left",
        border_style="#38bdf8",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    console.print(
        "[bold]👉 Next Step:[/bold] "
        "[green]\\[1][/green] Add Feature  |  "
        "[cyan]\\[2][/cyan] Refactor  |  "
        "[magenta]\\[3][/magenta] REPL Session  |  "
        "[blue]\\[4][/blue] Verify/Preview  |  "
        "[dim]\\[5/enter/q][/dim] Exit"
    )

    try:
        user_choice = ask("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return "exit", None

    low = user_choice.lower()
    if low in ("", "5", "q", "quit", "exit"):
        return "exit", None

    if low in ("1", "feature", "new", "f"):
        try:
            prompt_text = ask("📝 Enter new feature request or milestone description: ").strip()
            if not prompt_text:
                return "exit", None
            return "feature", prompt_text
        except (EOFError, KeyboardInterrupt):
            return "exit", None

    if low in ("2", "refactor", "optimize", "r"):
        try:
            prompt_text = ask("📝 Enter refactoring or optimization instructions: ").strip()
            if not prompt_text:
                return "exit", None
            return "refactor", prompt_text
        except (EOFError, KeyboardInterrupt):
            return "exit", None

    if low in ("3", "session", "repl", "s"):
        return "session", None

    if low in ("4", "verify", "preview", "v", "p"):
        console.print(
            "[bold]Pick action:[/bold] "
            "[cyan]\\[v/1][/cyan] Run Tier 2 Live Verification  |  "
            "[green]\\[p/2][/green] Launch UI Preview  |  "
            "[dim]\\[enter][/dim] Cancel"
        )
        try:
            sub = ask("> ").strip().lower()
            if sub in ("v", "verify", "1"):
                return "verify", None
            elif sub in ("p", "preview", "2"):
                return "preview", None
            else:
                return "none", None
        except (EOFError, KeyboardInterrupt):
            return "exit", None

    # Freeform user input treated directly as a new feature prompt
    console.print(f"   [dim]↳ Proceeding with new feature prompt: {escape(user_choice)}[/dim]")
    return "feature", user_choice


def print_dana_critique_card(critique: Any) -> None:
    """Render Dana's quality evaluation card for the supervised stage."""
    lead = str(getattr(critique, "lead", "stage")).upper()
    verdict = str(getattr(critique, "verdict", "approve")).lower()
    score = getattr(critique, "score", 85)
    summary = str(getattr(critique, "summary", ""))
    strengths = getattr(critique, "strengths", []) or []
    risks = getattr(critique, "risks_or_gaps", []) or []
    recommendations = getattr(critique, "actionable_recommendations", []) or []

    if verdict == "approve":
        badge = f"[bold green]APPROVED (Score: {score}/100)[/bold green]"
        border_col = "green"
    elif verdict == "suggest":
        badge = f"[bold cyan]SUGGESTIONS (Score: {score}/100)[/bold cyan]"
        border_col = "cyan"
    elif verdict == "warn":
        badge = f"[bold yellow]WARNINGS (Score: {score}/100)[/bold yellow]"
        border_col = "yellow"
    else:
        badge = f"[bold red]BLOCKED (Score: {score}/100)[/bold red]"
        border_col = "red"

    lines = [
        f"[bold white]Lead:[/bold white] [cyan]{escape(lead)}[/cyan] [dim]|[/dim] [bold white]Verdict:[/bold white] {badge}",
    ]
    if summary:
        lines.append(f"[dim]{escape(summary)}[/dim]")

    if strengths:
        lines.append("[bold green]Strengths Identified:[/bold green]")
        for s in strengths:
            lines.append(f"  [bold green]+[/bold green] {escape(str(s))}")

    if risks:
        lines.append("[bold yellow]Risks / Gaps Detected:[/bold yellow]")
        for r in risks:
            lines.append(f"  [bold yellow]▲[/bold yellow] {escape(str(r))}")

    if recommendations:
        lines.append("[bold cyan]Actionable Recommendations:[/bold cyan]")
        for rec in recommendations:
            lines.append(f"  [bold cyan]➔[/bold cyan] {escape(str(rec))}")

    panel = Panel(
        "\n".join(lines).strip(),
        title="[bold #a855f7]🧭 Dana — Quality Supervisor Evaluation[/bold #a855f7]",
        title_align="left",
        border_style=border_col,
        padding=(0, 2),
    )
    console.print()
    console.print(panel)


def prompt_dana_gate(
    critique: Any,
    auto: bool = False,
    input_func: Callable[[str], str] | None = None,
) -> tuple[str, str | None]:
    """
    Interactive decision gate for Dana's critique in advisory mode.
    Returns: ('proceed' | 'apply' | 'skip' | 'quit', feedback_text)
    """
    import os
    import sys

    print_dana_critique_card(critique)

    ask = _ask_with_cockpit(input_func)
    if auto or (
        input_func is None
        and (not sys.stdin.isatty() or "pytest" in sys.modules or os.environ.get("BUILDRELAY_TESTING") == "1")
    ):
        return "proceed", None

    recs = getattr(critique, "actionable_recommendations", []) or []
    rec_text = " | ".join(str(r) for r in recs) if recs else "Apply supervisor recommendations"

    console.print(
        "[bold]👉 Supervisor Action:[/bold] "
        "[green]\\[Y/enter][/green] Accept & Proceed  |  "
        "[cyan]\\[a][/cyan] Apply Recommendations to Lead  |  "
        "[yellow]\\[s][/yellow] Skip Suggestions  |  "
        "[red]\\[q][/red] Quit"
    )

    try:
        choice = ask("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "quit", None

    if choice in ("", "y", "yes"):
        return "proceed", None
    if choice in ("s", "skip"):
        return "skip", None
    if choice in ("q", "quit", "exit"):
        return "quit", None
    if choice in ("a", "apply"):
        return "apply", rec_text

    # Freeform user response
    return "apply", choice


def print_evaluation_scorecard(report: Any) -> None:
    """Render the multi-dimensional deliverable evaluation scorecard in Rich."""
    from rich.table import Table

    overall_score = getattr(report, "overall_score", 0)
    verdict = str(getattr(report, "verdict", "fail")).lower()
    task_id = str(getattr(report, "task_id", "unknown"))
    project_id = getattr(report, "project_id", None)
    dimensions = getattr(report, "dimensions", {}) or {}
    summary = str(getattr(report, "summary", ""))

    if verdict == "exceptional":
        badge = f"[bold green]🌟 EXCEPTIONAL ({overall_score}/100)[/bold green]"
        border_col = "green"
    elif verdict == "pass":
        badge = f"[bold cyan]✓ PASS ({overall_score}/100)[/bold cyan]"
        border_col = "cyan"
    elif verdict == "marginal":
        badge = f"[bold yellow]⚠ MARGINAL ({overall_score}/100)[/bold yellow]"
        border_col = "yellow"
    else:
        badge = f"[bold red]⛔ FAIL ({overall_score}/100)[/bold red]"
        border_col = "red"

    table = Table(title=None, expand=True, show_header=True, header_style="bold #10b981", border_style="#334155")
    table.add_column("Dimension", style="bold white", width=34)
    table.add_column("Score", justify="center", width=12)
    table.add_column("Rating", justify="center", width=14)
    table.add_column("Key Diagnostic Finding", style="dim white")

    icons = {
        "test_integrity": "🧪",
        "security_sanitization": "🔒",
        "ui_surface": "🎨",
        "live_verification": "🚀",
        "architectural_conformance": "📐",
    }

    all_recommendations: list[str] = []

    for dim_key, dim_eval in dimensions.items():
        score = getattr(dim_eval, "score", 0)
        label = getattr(dim_eval, "label", dim_key)
        status = str(getattr(dim_eval, "status", "marginal")).lower()
        findings = getattr(dim_eval, "findings", []) or []
        recs = getattr(dim_eval, "recommendations", []) or []
        all_recommendations.extend(recs)

        icon = icons.get(dim_key, "•")
        score_str = f"{score} / 20"

        if status == "excellent":
            status_badge = "[bold green]Excellent[/bold green]"
        elif status == "good":
            status_badge = "[bold cyan]Good[/bold cyan]"
        elif status == "marginal":
            status_badge = "[bold yellow]Marginal[/bold yellow]"
        else:
            status_badge = "[bold red]Gap[/bold red]"

        key_finding = findings[0] if findings else "Verified"
        table.add_row(f"{icon} {label}", score_str, status_badge, escape(key_finding))

    lines = [
        f"[bold white]Task ID:[/bold white]      [cyan]{escape(task_id)}[/cyan]" + (f"  |  [bold white]Project:[/bold white] [green]{escape(project_id)}[/green]" if project_id else ""),
        f"[bold white]Result:[/bold white]       {badge}\n",
        f"[bold white]Executive Assessment:[/bold white]\n{escape(summary)}\n",
    ]

    header_text = "\n".join(lines)
    console.print()
    console.print(
        Panel(
            header_text.strip(),
            title="[bold #10b981]📊 BuildRelay — Deliverable Evaluation Harness[/bold #10b981]",
            title_align="left",
            border_style=border_col,
            padding=(1, 2),
        )
    )
    console.print(table)

    if all_recommendations:
        rec_lines = []
        for idx, rec in enumerate(all_recommendations[:5], 1):
            rec_lines.append(f"  [cyan]{idx}.[/cyan] {escape(str(rec))}")
        if len(all_recommendations) > 5:
            rec_lines.append(f"  [dim]... and {len(all_recommendations) - 5} more in report[/dim]")

        console.print(
            Panel(
                "\n".join(rec_lines).strip(),
                title="[bold #f59e0b]💡 Actionable Quality Recommendations[/bold #f59e0b]",
                title_align="left",
                border_style="#f59e0b",
                padding=(1, 2),
            )
        )
    console.print(f"[dim]Audit Report saved to: vault/evaluations/eval-{escape(task_id)}.md[/dim]\n")




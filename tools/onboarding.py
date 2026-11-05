"""First-time interactive onboarding wizard and model/provider configuration."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from tools.model_catalog import discover_models, pick_model, qualify_model
from tools.chatgpt_auth import is_chatgpt_oauth_available
from tools.claude_auth import is_claude_oauth_available


SUPPORTED_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "chatgpt_oauth",
        "name": "ChatGPT Web Auth (Codex / Browser Subscription)",
        "badge": "Codex / Subscription",
        "description": "Browser authentication; provider access and usage limits apply.",
        "models": ["gpt-4o", "o3-mini", "gpt-4o-mini", "o1"],
        "default_model": "gpt-4o",
    },
    {
        "id": "openai",
        "name": "OpenAI API",
        "badge": "Direct API",
        "description": "Direct pay-as-you-go API key (platform.openai.com).",
        "env_key": "OPENAI_API_KEY",
        "models": ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"],
        "default_model": "gpt-4o",
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "badge": "Direct API",
        "description": "Anthropic API key (console.anthropic.com).",
        "env_key": "ANTHROPIC_API_KEY",
        "models": ["claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"],
        "default_model": "claude-3-7-sonnet",
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "badge": "Direct API",
        "description": "Google AI Studio API key (aistudio.google.com).",
        "env_key": "GEMINI_API_KEY",
        "models": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-1.5-pro"],
        "default_model": "gemini-2.0-flash",
    },
    {
        "id": "ollama",
        "name": "Local LLM (Ollama / LocalAI)",
        "badge": "Local / Free",
        "description": "Local models via Ollama or OpenAI-compatible endpoint.",
        "default_base_url": "http://localhost:11434/v1",
        "models": ["llama3.3", "qwen2.5-coder", "mistral"],
        "default_model": "llama3.3",
    },
    {
        "id": "openrouter",
        "name": "Custom / OpenRouter Gateway",
        "badge": "Custom Endpoint",
        "description": "Universal routing gateway (openrouter.ai) or custom proxy.",
        "default_base_url": "https://openrouter.ai/api/v1",
        "models": ["anthropic/claude-3.7-sonnet", "openai/gpt-4o", "meta-llama/llama-3.3-70b-instruct"],
        "default_model": "anthropic/claude-3.7-sonnet",
    },
    {
        "id": "claude_oauth",
        "name": "Claude Web Auth (Browser / Pro / Max Subscription)",
        "badge": "Claude / Subscription",
        "description": "Browser authentication or claude setup-token; subscription limits apply.",
        "models": ["claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"],
        "default_model": "claude-3-7-sonnet",
    },
]


def check_credentials_configured() -> bool:
    """
    Check if any LLM credentials are configured.
    Returns True if direct API keys are present in environment,
    ChatGPT OAuth credentials exist, or a local LLM URL is configured.
    """
    selected = os.environ.get("BUILDRELAY_PROVIDER")
    if selected:
        if selected == "chatgpt_oauth":
            return is_chatgpt_oauth_available()
        if selected == "claude_oauth":
            return is_claude_oauth_available()
        key = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "ollama": "OPENAI_API_KEY", "openrouter": "OPENAI_API_KEY"}.get(selected)
        credentials = bool(key and os.environ.get(key, "").strip()) or (selected == "gemini" and bool(os.environ.get("GOOGLE_API_KEY", "").strip()))
        if selected in ("ollama", "openrouter"):
            return credentials and bool(os.environ.get("OPENAI_BASE_URL", "").strip())
        return credentials
    # 1. Direct API keys
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"]
    for key in api_keys:
        val = os.environ.get(key)
        if val and val.strip():
            return True

    # 2. Local LLM / Custom base URLs
    base_urls = ["OLLAMA_BASE_URL", "OPENAI_BASE_URL"]
    for key in base_urls:
        val = os.environ.get(key)
        if val and val.strip():
            return True

    # 3. OAuth session files (ChatGPT & Claude)
    if is_chatgpt_oauth_available() or is_claude_oauth_available():
        return True

    return False


def get_credential_status() -> dict[str, Any]:
    """Return detailed status of configured providers and active models."""
    chatgpt = is_chatgpt_oauth_available()
    claude_oauth = is_claude_oauth_available()
    openai_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    anthropic_key = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    gemini_key = bool(os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip())
    local_url = bool(os.environ.get("OLLAMA_BASE_URL", "").strip() or os.environ.get("OPENAI_BASE_URL", "").strip())

    configured: list[str] = []
    if chatgpt:
        configured.append("ChatGPT OAuth (Codex)")
    if claude_oauth:
        configured.append("Claude OAuth (Subscription)")
    if openai_key:
        configured.append("OpenAI API")
    if anthropic_key:
        configured.append("Anthropic Claude")
    if gemini_key:
        configured.append("Google Gemini")
    if local_url:
        configured.append("Local LLM / Custom")

    active_provider = "none"
    if chatgpt and not openai_key:
        active_provider = "chatgpt_oauth"
    elif claude_oauth and not anthropic_key:
        active_provider = "claude_oauth"
    elif openai_key:
        active_provider = "openai"
    elif anthropic_key:
        active_provider = "anthropic"
    elif gemini_key:
        active_provider = "gemini"
    elif local_url:
        active_provider = "local"
    elif chatgpt:
        active_provider = "chatgpt_oauth"
    elif claude_oauth:
        active_provider = "claude_oauth"

    active_provider = os.environ.get("BUILDRELAY_PROVIDER") or active_provider

    if active_provider in ("anthropic", "claude_oauth"):
        active_model = os.environ.get("ANTHROPIC_MODEL", "claude-3-7-sonnet")
    elif active_provider == "gemini":
        active_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    elif active_provider == "local":
        active_model = os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL", "llama3.3")
    else:
        active_model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    return {
        "has_credentials": check_credentials_configured(),
        "configured_providers": configured,
        "active_provider": active_provider,
        "chatgpt_oauth": chatgpt,
        "claude_oauth": claude_oauth,
        "openai": openai_key,
        "anthropic": anthropic_key,
        "gemini": gemini_key,
        "local": local_url,
        "active_model": os.environ.get("BUILDRELAY_MODEL") or active_model,
        "active_tier": os.environ.get("DEFAULT_TIER", "balanced"),
    }


def parse_env_file(path: Path) -> list[tuple[str | None, str]]:
    """Parse an existing .env file preserving comments and blank lines."""
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[tuple[str | None, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            entries.append((None, line))
        elif "=" in line:
            key = line.split("=", 1)[0].strip()
            entries.append((key, line))
        else:
            entries.append((None, line))
    return entries


def save_env_configuration(entries: dict[str, str], env_path: Path | str | None = None) -> Path:
    """
    Safely persist configuration entries to .env file preserving existing variables and comments.
    Enforces atomic write and 0o600 (owner read/write only) file permissions.
    """
    project_root = Path(__file__).resolve().parent.parent
    target_path = Path(env_path) if env_path else (project_root / ".env")
    if not target_path.is_absolute():
        target_path = project_root / target_path

    parsed = parse_env_file(target_path)
    updated_keys: set[str] = set()
    new_lines: list[str] = []

    for key, line in parsed:
        if key is not None and key in entries:
            new_lines.append(f"{key}={entries[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    unadded = [k for k in entries if k not in updated_keys]
    if unadded and new_lines and new_lines[-1].strip():
        new_lines.append("")

    for k in unadded:
        new_lines.append(f"{k}={entries[k]}")

    content = "\n".join(new_lines) + "\n"

    target_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp_file: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target_path.parent, delete=False) as tf:
            temp_file = Path(tf.name)
            os.fchmod(tf.fileno(), 0o600)
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())
        temp_file.replace(target_path)
        os.chmod(target_path, 0o600)
    finally:
        if temp_file is not None and temp_file.exists():
            temp_file.unlink(missing_ok=True)

    # Immediately update in-memory process environment
    for k, v in entries.items():
        os.environ[k] = str(v)

    return target_path


def validate_credential_format(provider: str, value: str) -> tuple[bool, str]:
    """Validate format sanity for provider keys or connection endpoints."""
    val = value.strip()
    if not val:
        return False, "Credential value cannot be empty."

    p = provider.lower()
    if p == "openai":
        if val.startswith("sk-") or len(val) >= 20:
            return True, "Valid OpenAI key format"
        return False, "OpenAI API keys typically start with 'sk-'"

    if p == "anthropic":
        if val.startswith("sk-ant-") or val.startswith("sk-") or len(val) >= 20:
            return True, "Valid Anthropic key format"
        return False, "Anthropic API keys typically start with 'sk-ant-'"

    if p == "gemini":
        if len(val) >= 15:
            return True, "Valid Gemini key format"
        return False, "Gemini API key appears too short"

    if p in ("ollama", "local", "openrouter", "custom"):
        if val.startswith("http://") or val.startswith("https://"):
            return True, "Valid URL format"
        return False, "Endpoint URL must begin with http:// or https://"

    return True, "Format accepted"


def ping_provider_connectivity(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 2.0,
) -> tuple[bool, str]:
    """
    Lightweight, non-blocking check to verify endpoint or key reachability.
    Gracefully handles sandboxed/offline environments without blocking setup.
    """
    p = provider.lower()
    try:
        import urllib.request
        import urllib.error

        if p == "openai" and api_key:
            req = urllib.request.Request(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        return True, "Connected successfully to OpenAI API"
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    return False, "Authentication failed (401 Unauthorized): Check your OpenAI API key"
                return True, f"OpenAI endpoint reached (HTTP {e.code})"

        elif p == "anthropic" and api_key:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return True, "Connected successfully to Anthropic API"
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    return False, "Authentication failed (401 Unauthorized): Check your Anthropic API key"
                return True, f"Anthropic endpoint reached (HTTP {e.code})"

        elif p in ("ollama", "local") and base_url:
            test_url = base_url.rstrip("/")
            if test_url.endswith("/v1"):
                test_url = test_url[:-3]
            req = urllib.request.Request(test_url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status in (200, 404):
                    return True, f"Local service reached at {base_url}"

    except Exception as exc:
        return True, f"Connectivity check skipped ({type(exc).__name__}: sandboxed or offline)"

    return True, "Format verified"


def run_onboarding_wizard(
    console: Console | None = None,
    env_path: Path | str | None = None,
    prompt_ask: Callable[..., str] | None = None,
    confirm_ask: Callable[..., bool] | None = None,
    login_func: Callable[..., tuple[bool, str]] | None = None,
    is_reconfig: bool = False,
) -> bool:
    """
    Interactive first-time onboarding and model/provider configuration wizard.
    Allows selecting primary provider, entering credentials (masked), picking
    a model for each lead from the connection catalog or unverified suggestions.
    """
    ui = console or Console()
    ask = prompt_ask or Prompt.ask
    confirm = confirm_ask or Confirm.ask

    # 1. Header Banner
    title = "🔄 BuildRelay Configuration Wizard" if is_reconfig else "⚡ Welcome to BuildRelay! Setup Wizard"
    subtitle = (
        "Reconfigure your AI development team connection and per-lead models."
        if is_reconfig
        else "Let's connect your AI development team (Natasha, Odin, Taghi, Meti) to your preferred LLM provider."
    )

    header_panel = Panel(
        f"[bold white]{subtitle}[/bold white]\n[dim]Configure once; credentials are stored in plaintext .env with owner-only permissions (0600).[/dim]",
        title=f"[bold #818cf8]{title}[/bold #818cf8]",
        title_align="left",
        border_style="#818cf8",
        padding=(1, 2),
    )
    ui.print()
    ui.print(header_panel)

    # 2. Existing Status (if reconfiguring or credentials found)
    current_status = get_credential_status()
    if current_status["has_credentials"]:
        status_table = Table(title="Current Configuration", title_justify="left", border_style="dim")
        status_table.add_column("Property", style="bold cyan")
        status_table.add_column("Value", style="white")

        status_table.add_row("Configured Providers", ", ".join(current_status["configured_providers"]))
        status_table.add_row("Active Provider", current_status["active_provider"])
        status_table.add_row("Default Model", current_status["active_model"])
        status_table.add_row("Model selection", "Explicit per-lead choices")
        ui.print(status_table)
        ui.print()

    # 3. Provider Selection
    ui.print("[bold]Step 1: Choose Authentication Method & Provider[/bold]\n")
    ui.print("[bold cyan]── Web Browser Authentication ───────────────────────────────────[/bold cyan]")
    ui.print(
        "  [cyan][1][/cyan] [bold]Web Browser Login (ChatGPT Plus/Team Subscription)[/bold]\n"
        "      • Browser sign-in; provider access and usage limits apply\n"
        "      • Automatically redirects to browser for one-click authorization\n"
        "      • Model suggestions are unverified; select an account-supported model\n"
    )
    ui.print("[bold cyan]── Direct API Key / Local Authentication ────────────────────────[/bold cyan]")
    for idx, prov in enumerate(SUPPORTED_PROVIDERS[1:6], start=2):
        ui.print(
            f"  [cyan][{idx}][/cyan] [bold]{prov['name']}[/bold] [dim]({prov['badge']})[/dim]\n"
            f"      [dim]{prov['description']}[/dim]"
        )
    ui.print("[bold cyan]── Additional Subscription Options ─────────────────────────────[/bold cyan]")
    prov_claude = SUPPORTED_PROVIDERS[6]
    ui.print(
        f"  [cyan][7][/cyan] [bold]{prov_claude['name']}[/bold] [dim]({prov_claude['badge']})[/dim]\n"
        f"      [dim]{prov_claude['description']}[/dim]\n"
    )
    ui.print("  [red][q][/red] [dim]Cancel and exit[/dim]\n")

    choice = ask("Select provider or authentication method", choices=[str(i) for i in range(1, len(SUPPORTED_PROVIDERS) + 1)] + ["q"], default="1")
    if choice.lower() == "q":
        ui.print("[yellow]Setup cancelled. No changes were made.[/yellow]")
        return False

    selected_prov = SUPPORTED_PROVIDERS[int(choice) - 1]
    prov_id = selected_prov["id"]
    entries_to_save: dict[str, str] = {
        "BUILDRELAY_PROVIDER": prov_id,
        "USE_CHATGPT_OAUTH": "1" if prov_id == "chatgpt_oauth" else "0",
        "USE_CLAUDE_OAUTH": "1" if prov_id == "claude_oauth" else "0",
        "BUILDRELAY_MODEL_MODE": "selected",
        **{f"MODEL_{lead}": "" for lead in ("NATASHA", "ODIN", "TAGHI", "METI")},
    }
    selected_prov = dict(selected_prov)
    def load_catalog(api_key="", base_url=None):
        models, note = discover_models(prov_id, api_key=api_key, base_url=base_url)
        ui.print(note)
        entries_to_save["BUILDRELAY_MODEL_CATALOG"] = ",".join(models)
        if models:
            selected_prov["models"] = models
            selected_prov["default_model"] = models[0]
        else:
            ui.print("[yellow]Suggested model names below are not verified for this account.[/yellow]")
        entries_to_save["BUILDRELAY_MODEL_SUGGESTIONS"] = ",".join(selected_prov["models"]) if not models else ""


    # 4. Provider-Specific Credentials & Model Selection
    ui.print(f"\n[bold green]Configuring {selected_prov['name']}:[/bold green]")

    if prov_id == "chatgpt_oauth":
        ui.print(
            "BuildRelay connects directly to your ChatGPT Plus/Team browser session via Codex OAuth.\n"
            "[green]✓ Browser login; account access and usage limits apply[/green]"
        )
        from tools.chatgpt_auth import login_with_chatgpt_browser
        do_login = login_func or login_with_chatgpt_browser
        login_ok, login_msg = do_login(ui=ui)
        if not login_ok:
            ui.print("[yellow]Setup incomplete. Retry browser login before starting the task.[/yellow]")
            return False
        ui.print(f"  [bold green]✓ {login_msg}[/bold green]")

        entries_to_save["CHATGPT_AUTH_FILE"] = os.environ.get("CHATGPT_AUTH_FILE", ".env.chatgpt-auth.json")

        load_catalog()

    elif prov_id == "claude_oauth":
        ui.print(
            "BuildRelay connects directly to your Claude Pro/Max subscription via browser PKCE or token import.\n"
            "[green]✓ Browser login or claude setup-token; subscription limits apply[/green]"
        )
        from tools.claude_auth import login_with_claude_browser
        do_login = login_func or login_with_claude_browser
        login_ok, login_msg = do_login(ui=ui)
        if not login_ok:
            ui.print("[yellow]Setup incomplete. In headless Linux/SSH, paste the token from 'claude setup-token'.[/yellow]")
            return False
        ui.print(f"  [bold green]✓ {login_msg}[/bold green]")

        entries_to_save["CLAUDE_AUTH_FILE"] = os.environ.get("CLAUDE_AUTH_FILE", ".env.claude-auth.json")

        load_catalog()

    elif prov_id in ("openai", "anthropic", "gemini"):
        env_key = selected_prov["env_key"]
        api_key = ask(f"Enter your {selected_prov['name']} API key", password=True)

        is_valid, msg = validate_credential_format(prov_id, api_key)
        if not is_valid:
            ui.print(f"[bold red]Warning:[/bold red] {msg}")
            if not confirm("Continue and save anyway?", default=True):
                ui.print("[yellow]Setup aborted.[/yellow]")
                return False

        ping_ok, ping_msg = ping_provider_connectivity(prov_id, api_key=api_key)
        if not ping_ok:
            ui.print(f"[bold red]Validation error:[/bold red] {ping_msg}")
            if not confirm("Save this key anyway?", default=False):
                ui.print("[yellow]Setup aborted.[/yellow]")
                return False
        else:
            ui.print(f"[dim]{ping_msg}[/dim]")

        entries_to_save[env_key] = api_key
        if prov_id == "openai":
            entries_to_save["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
        load_catalog(api_key=api_key)


    elif prov_id == "ollama":
        base_url = ask("Enter local LLM Base URL", default=selected_prov["default_base_url"])
        load_catalog(api_key="ollama", base_url=base_url)

        entries_to_save["OPENAI_BASE_URL"] = base_url
        entries_to_save["OPENAI_API_KEY"] = "ollama"

    elif prov_id == "openrouter":
        base_url = ask("Enter gateway Base URL", default=selected_prov["default_base_url"])
        api_key = ask("Enter API Key", password=True)
        load_catalog(api_key=api_key, base_url=base_url)

        entries_to_save["OPENAI_BASE_URL"] = base_url
        entries_to_save["OPENAI_API_KEY"] = api_key

    prefix = {"anthropic": "anthropic", "gemini": "google"}.get(prov_id, "openai")
    def qualify(value):
        return qualify_model(value, prov_id)
    catalog = [qualify(value) for value in selected_prov["models"]]
    current = qualify(selected_prov["default_model"])
    ui.print("\n[bold]Choose a model for each lead. Enter reuses the previous choice.[/bold]")
    try:
        for lead in ("natasha", "odin", "taghi", "meti"):
            current = pick_model(catalog, current, lead.title(), ask, ui.print)
            current = qualify(current)
            entries_to_save[f"MODEL_{lead.upper()}"] = current
    except (EOFError, KeyboardInterrupt, ValueError):
        ui.print("[yellow]Setup cancelled; choose models from the selected connection. Assignments were not saved.[/yellow]")
        return False
    entries_to_save["BUILDRELAY_MODEL"] = entries_to_save["MODEL_NATASHA"]
    model_key = {"anthropic": "ANTHROPIC_MODEL", "gemini": "GEMINI_MODEL"}.get(prov_id, "OPENAI_MODEL")
    entries_to_save[model_key] = entries_to_save["MODEL_NATASHA"].split(":", 1)[-1]
    entries_to_save["DEFAULT_TIER"] = ""

    # 7. Safe Persistence
    saved_path = save_env_configuration(entries_to_save, env_path=env_path)

    # 8. Success Output Card
    success_table = Table(border_style="green", show_header=False, box=None)
    success_table.add_column("Key", style="bold cyan")
    success_table.add_column("Value", style="white")

    for k, v in entries_to_save.items():
        masked_v = f"{v[:4]}...{v[-4:]}" if ("KEY" in k and len(v) > 8) else v
        success_table.add_row(k, masked_v)

    success_panel = Panel(
        success_table,
        title=f"[bold green]✓ Configuration Saved ({saved_path.name})[/bold green]",
        subtitle="[dim]File secured with mode 0600 (Owner Read/Write only)[/dim]",
        border_style="green",
        padding=(1, 2),
    )
    ui.print()
    ui.print(success_panel)
    ui.print("[bold green]Setup completed successfully![/bold green] You are ready to run tasks with BuildRelay.\n")
    return True

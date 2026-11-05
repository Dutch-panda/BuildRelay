import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from pydantic_ai.models import infer_model, Model
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai_chatgpt import (
    OpenAIChatGPTCredentials,
    OpenAIChatGPTCredentialSource,
    OpenAIChatGPTOAuthFlow,
    OpenAIChatGPTProvider,
)


class FileCredentialSource(OpenAIChatGPTCredentialSource):
    def __init__(self, path: Path):
        self.path = path

    async def load(self) -> OpenAIChatGPTCredentials:
        return OpenAIChatGPTCredentials(**json.loads(self.path.read_text(encoding="utf-8")))

    async def save(self, credentials: OpenAIChatGPTCredentials) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                os.fchmod(temporary.fileno(), 0o600)
                json.dump(asdict(credentials), temporary)
                temporary.flush()
                os.fsync(temporary.fileno())
            temporary_path.replace(self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def is_chatgpt_oauth_available() -> bool:
    """Check if ChatGPT OAuth credentials file exists and has content."""
    project_dir = Path(__file__).resolve().parent.parent
    auth_path = Path(os.environ.get("CHATGPT_AUTH_FILE", ".env.chatgpt-auth.json")).expanduser()
    if not auth_path.is_absolute():
        auth_path = project_dir / auth_path
    return auth_path.is_file() and auth_path.stat().st_size > 10


def login_with_chatgpt_browser(
    auth_path: Path | None = None,
    open_browser: bool = True,
    ui: object | None = None,
) -> tuple[bool, str]:
    """
    Launch ChatGPT browser OAuth flow to authenticate.
    Opens the browser or displays the URL, waits for the local redirect callback,
    and saves credentials to the auth_path.
    """
    import asyncio
    import webbrowser

    project_dir = Path(__file__).resolve().parent.parent
    target_path = auth_path or Path(os.environ.get("CHATGPT_AUTH_FILE", ".env.chatgpt-auth.json")).expanduser()
    if not target_path.is_absolute():
        target_path = project_dir / target_path

    async def _async_flow() -> tuple[bool, str]:
        source = FileCredentialSource(target_path)
        saved = await source.load() if source.path.exists() else None
        if saved is not None and getattr(saved, "plan_usage_granted", False):
            return True, "Existing active session found"

        flow = OpenAIChatGPTOAuthFlow(
            app_name="BuildRelay",
            client_id=saved.client_id if saved else None,
            id_token_hint=saved.id_token if saved else None,
        )
        auth_url = flow.authorization_url(extra_params={"prompt": "consent"})
        if ui and hasattr(ui, "print"):
            ui.print(f"\n[bold cyan]Opening browser to sign in with ChatGPT:[/bold cyan]")
            ui.print(f"  [link={auth_url}]{auth_url}[/link]\n")
            ui.print("[dim]Waiting for browser authentication callback...[/dim]")
        else:
            print(f"\nOpening browser to sign in with ChatGPT:\n  {auth_url}\n")
            print("Waiting for browser authentication callback...")

        if open_browser:
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass

        creds = await asyncio.wait_for(flow.exchange_code_from_callback(), timeout=180)
        await source.save(creds)
        return True, "Successfully authenticated with ChatGPT"

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(_async_flow())).result(timeout=185)
        else:
            return asyncio.run(_async_flow())
    except Exception as exc:
        return False, f"Browser authentication failed ({type(exc).__name__}). Retry login; configuration was not completed."



def resolve_model_name(name: str) -> str:
    """Normalize model names by adding appropriate provider prefix if missing."""
    if ":" in name:
        return name
    lower = name.lower()
    if lower.startswith("claude"):
        return f"anthropic:{name}"
    if lower.startswith("gemini"):
        return f"google:{name}"
    if lower.startswith(("gpt-", "o1", "o3", "chatgpt", "text-embedding")):
        return f"openai:{name}"
    return name


async def get_model(model_name: str | None = None) -> Model:
    """
    Explicit BUILDRELAY_PROVIDER connections own authentication and endpoint choice.
    Model IDs are resolved within that connection, never by unrelated saved keys.
    Without an explicit connection, retain the legacy priority:
    1. Explicit model string or CLI argument (e.g. 'openai:gpt-4o', 'anthropic:claude-3-5-sonnet-latest')
    2. Environment model (LLM_MODEL or MODEL_NAME)
    3. Direct API Keys: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY / GOOGLE_API_KEY
    4. ChatGPT OAuth sign-in flow (fallback)
    """
    selected = os.environ.get("BUILDRELAY_PROVIDER")
    if selected:
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        from pydantic_ai.providers.anthropic import AnthropicProvider
        from pydantic_ai.providers.google import GoogleProvider
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.models.google import GoogleModel
        requested = model_name or os.environ.get("BUILDRELAY_MODEL")
        if not requested:
            raise ValueError("No selected model. Run buildrelay config.")
        if requested == "test":
            return infer_model("test")
        from tools.model_catalog import qualify_model
        raw = qualify_model(requested, selected).split(":", 1)[1]
        key_name = {"anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}.get(selected, "OPENAI_API_KEY")
        key = os.environ.get(key_name) or (os.environ.get("GOOGLE_API_KEY") if selected == "gemini" else None)
        if selected not in ("chatgpt_oauth", "claude_oauth") and not key:
            raise ValueError("Selected provider credentials are missing. Run buildrelay config.")
        if selected == "claude_oauth":
            from tools.claude_auth import get_claude_oauth_model
            return await get_claude_oauth_model(raw)
        if selected == "anthropic":
            return AnthropicModel(raw, provider=AnthropicProvider(api_key=key))
        if selected == "gemini":
            return GoogleModel(raw, provider=GoogleProvider(api_key=key))
        if selected in ("openai", "ollama", "openrouter"):
            endpoint = os.environ.get("OPENAI_BASE_URL") if selected != "openai" else "https://api.openai.com/v1"
            if selected != "openai" and not endpoint:
                raise ValueError("Selected endpoint is missing. Run buildrelay config.")
            provider = OpenAIProvider(api_key=key, base_url=endpoint)
            cls = OpenAIResponsesModel if selected == "openai" else OpenAIChatModel
            return cls(raw, provider=provider)
        if selected != "chatgpt_oauth":
            raise ValueError("Unsupported selected provider. Run buildrelay config.")
        # Explicit browser authentication must never fall through to an old API key.
        model_name = "openai:" + raw

    model_override = model_name or os.environ.get("LLM_MODEL") or os.environ.get("MODEL_NAME")
    resolved_name = resolve_model_name(model_override) if model_override else None

    # Check non-OpenAI or local/test models first
    if resolved_name:
        lower = resolved_name.lower()
        if lower.startswith(("anthropic:", "google:", "gemini:", "ollama:", "local:", "test")):
            return infer_model(resolved_name)
        if lower == "test" or lower.startswith("test:"):
            return infer_model("test")

        if lower.startswith("openai:"):
            # If direct API key is available, use standard infer_model
            if selected != "chatgpt_oauth" and os.environ.get("OPENAI_API_KEY") and os.environ.get("USE_CHATGPT_OAUTH", "").lower() not in ("1", "true", "yes"):
                return infer_model(resolved_name)
            # If no OPENAI_API_KEY, fall through to ChatGPT OAuth provider using the requested OpenAI model!

    if not model_name:
        if selected != "chatgpt_oauth" and os.environ.get("OPENAI_API_KEY") and os.environ.get("USE_CHATGPT_OAUTH", "").lower() not in ("1", "true", "yes"):
            openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o")
            return infer_model(resolve_model_name(openai_model if ":" in openai_model else f"openai:{openai_model}"))

        if os.environ.get("ANTHROPIC_API_KEY"):
            anthropic_model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
            return infer_model(resolve_model_name(anthropic_model if ":" in anthropic_model else f"anthropic:{anthropic_model}"))

        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            return infer_model(resolve_model_name(gemini_model if ":" in gemini_model else f"google:{gemini_model}"))

    # Fallback to ChatGPT OAuth provider
    project_dir = Path(__file__).resolve().parent.parent
    auth_path = Path(os.environ.get("CHATGPT_AUTH_FILE", ".env.chatgpt-auth.json")).expanduser()
    if not auth_path.is_absolute():
        auth_path = project_dir / auth_path
    source = FileCredentialSource(auth_path)
    saved = await source.load() if source.path.exists() else None
    if saved is None or not saved.plan_usage_granted:
        flow = OpenAIChatGPTOAuthFlow(
            app_name="BuildRelay",
            client_id=saved.client_id if saved else None,
            id_token_hint=saved.id_token if saved else None,
        )
        print("Open this URL in your browser and sign in with ChatGPT:")
        print(flow.authorization_url(extra_params={"prompt": "consent"}))
        await source.save(await flow.exchange_code_from_callback())

    raw_model = resolved_name or os.environ.get("OPENAI_MODEL", "gpt-4o")
    if ":" in raw_model:
        raw_model = raw_model.split(":", 1)[1]

    return OpenAIResponsesModel(
        raw_model,
        provider=OpenAIChatGPTProvider(credential_source=source),
    )


async def get_chatgpt_model(model_name: str | None = None) -> Model:
    """Backward-compatible wrapper for get_model."""
    return await get_model(model_name)

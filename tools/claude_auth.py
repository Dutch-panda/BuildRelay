"""
Anthropic Claude Web / Browser OAuth Authentication & Subscription Sharing.

Enables developers to connect their Claude account (Pro / Max subscription)
via browser PKCE OAuth or headless token import (claude setup-token).
Zero-cost token usage with full lead orchestration parity.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import re
import secrets
import socket
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

# Anthropic official OAuth Client ID
CLAUDE_OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
CLAUDE_AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
CLAUDE_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
CLAUDE_OAUTH_SCOPES = "org:create_api_key user:profile user:inference"
CLAUDE_BETA_HEADER = "oauth-2025-01-01"


@dataclass
class ClaudeCredentials:
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None
    token_type: str = "bearer"
    account_id: str | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        # Buffer 60 seconds before actual expiration
        return time.time() >= (self.expires_at - 60)


class ClaudeCredentialSource:
    def __init__(self, path: Path):
        self.path = path

    async def load(self) -> ClaudeCredentials | None:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return ClaudeCredentials(
                access_token=data.get("access_token", ""),
                refresh_token=data.get("refresh_token"),
                expires_at=data.get("expires_at"),
                token_type=data.get("token_type", "bearer"),
                account_id=data.get("account_id"),
            )
        except Exception:
            return None

    async def save(self, credentials: ClaudeCredentials) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                os.fchmod(temporary.fileno(), 0o600)
                json.dump(asdict(credentials), temporary, indent=2)
                temporary.flush()
                os.fsync(temporary.fileno())
            temporary_path.replace(self.path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink(missing_ok=True)


def get_claude_auth_path() -> Path:
    project_dir = Path(__file__).resolve().parent.parent
    auth_path = Path(os.environ.get("CLAUDE_AUTH_FILE", ".env.claude-auth.json")).expanduser()
    if not auth_path.is_absolute():
        auth_path = project_dir / auth_path
    return auth_path


def get_existing_claude_code_credentials_path() -> Path | None:
    """Check for official Claude Code credentials stored at ~/.claude/.credentials.json."""
    claude_code_path = Path.home() / ".claude" / ".credentials.json"
    if claude_code_path.is_file() and claude_code_path.stat().st_size > 10:
        return claude_code_path
    return None


def is_claude_oauth_available() -> bool:
    """Check if Claude OAuth credentials exist via file or environment."""
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True

    auth_path = get_claude_auth_path()
    if auth_path.is_file() and auth_path.stat().st_size > 10:
        try:
            data = json.loads(auth_path.read_text(encoding="utf-8"))
            return bool(data.get("access_token"))
        except Exception:
            pass

    existing_cli = get_existing_claude_code_credentials_path()
    if existing_cli:
        try:
            data = json.loads(existing_cli.read_text(encoding="utf-8"))
            return bool(data.get("accessToken") or data.get("access_token"))
        except Exception:
            pass

    return False


def parse_claude_token_input(raw_input: str) -> ClaudeCredentials | None:
    """
    Parse a token pasted by the user.
    Handles raw tokens (e.g. sk-ant-oat01-...), JSON output from claude setup-token,
    or key-value exports.
    """
    raw = raw_input.strip()
    if not raw:
        return None

    # Check if JSON
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            token = data.get("accessToken") or data.get("access_token")
            if token:
                expires_at = None
                if "expiresAt" in data and isinstance(data["expiresAt"], (int, float)):
                    expires_at = float(data["expiresAt"])
                elif "expires_in" in data and isinstance(data["expires_in"], (int, float)):
                    expires_at = time.time() + float(data["expires_in"])
                return ClaudeCredentials(
                    access_token=str(token),
                    refresh_token=data.get("refreshToken") or data.get("refresh_token"),
                    expires_at=expires_at,
                    token_type=data.get("tokenType", "bearer"),
                )
        except Exception:
            pass

    # Extract sk-ant-oat token via regex
    match = re.search(r"(sk-ant-oat[0-9a-zA-Z_-]+)", raw)
    if match:
        return ClaudeCredentials(access_token=match.group(1))

    # Fallback: if user pasted plain token string
    if raw.startswith("sk-"):
        return ClaudeCredentials(access_token=raw)

    return None


class ClaudeOAuthFlow:
    """Manages PKCE code generation, authorization URLs, and token exchange."""

    def __init__(self, client_id: str = CLAUDE_OAUTH_CLIENT_ID):
        self.client_id = client_id

    @staticmethod
    def generate_code_verifier() -> str:
        return secrets.token_urlsafe(64)

    @staticmethod
    def generate_code_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    def build_authorization_url(self, redirect_uri: str, state: str, challenge: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "scope": CLAUDE_OAUTH_SCOPES,
            "state": state,
        }
        return f"{CLAUDE_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        http_client: Any = None,
    ) -> ClaudeCredentials:
        """Exchange authorization code with console.anthropic.com."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }

        if http_client:
            resp = await http_client.post(CLAUDE_TOKEN_URL, data=payload)
            data = resp.json()
        else:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(CLAUDE_TOKEN_URL, data=payload)
                resp.raise_for_status()
                data = resp.json()

        token = data.get("access_token") or data.get("accessToken")
        if not token:
            raise ValueError(f"No access token in token response: {data}")

        expires_in = data.get("expires_in")
        expires_at = time.time() + float(expires_in) if expires_in else None

        return ClaudeCredentials(
            access_token=token,
            refresh_token=data.get("refresh_token") or data.get("refreshToken"),
            expires_at=expires_at,
            token_type=data.get("token_type", "bearer"),
            account_id=data.get("account_id"),
        )

    async def refresh_tokens(
        self,
        refresh_token: str,
        http_client: Any = None,
    ) -> ClaudeCredentials:
        """Refresh expired access token."""
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": refresh_token,
        }

        if http_client:
            resp = await http_client.post(CLAUDE_TOKEN_URL, data=payload)
            data = resp.json()
        else:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(CLAUDE_TOKEN_URL, data=payload)
                resp.raise_for_status()
                data = resp.json()

        token = data.get("access_token")
        if not token:
            raise ValueError(f"Failed to refresh token: {data}")

        expires_in = data.get("expires_in")
        expires_at = time.time() + float(expires_in) if expires_in else None

        return ClaudeCredentials(
            access_token=token,
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=expires_at,
            token_type=data.get("token_type", "bearer"),
        )


def _find_free_port(start_port: int = 8765) -> int:
    """Find an available TCP port for the local OAuth redirect listener."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    # Fallback to ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def login_with_claude_browser(
    auth_path: Path | None = None,
    open_browser: bool = True,
    ui: object | None = None,
    token_input: str | None = None,
) -> tuple[bool, str]:
    """
    Authenticate with Claude Account via browser OAuth PKCE or headless token input.
    Supports:
    - Desktop browser flow with local loopback listener.
    - Automatic detection and import of existing ~/.claude/.credentials.json.
    - Headless manual token paste (from 'claude setup-token').
    """
    import webbrowser

    target_path = auth_path or get_claude_auth_path()
    source = ClaudeCredentialSource(target_path)

    async def _async_flow() -> tuple[bool, str]:
        # 1. Direct token input bypass (e.g. headless or tests)
        if token_input:
            creds = parse_claude_token_input(token_input)
            if creds:
                await source.save(creds)
                return True, "Successfully configured Claude credentials from token input"
            return False, "Invalid token format. Must be an sk-ant-oat token or JSON credential payload."

        # 2. Existing valid file check
        existing = await source.load()
        if existing and not existing.is_expired and existing.access_token:
            return True, "Existing active Claude session found"

        # 3. Check for existing Claude Code CLI credentials in ~/.claude/.credentials.json
        existing_cli = get_existing_claude_code_credentials_path()
        if existing_cli:
            try:
                data = json.loads(existing_cli.read_text(encoding="utf-8"))
                cli_token = data.get("accessToken") or data.get("access_token")
                if cli_token:
                    creds = ClaudeCredentials(
                        access_token=cli_token,
                        refresh_token=data.get("refreshToken") or data.get("refresh_token"),
                    )
                    await source.save(creds)
                    return True, "Successfully imported active session from Claude Code (~/.claude/.credentials.json)"
            except Exception:
                pass

        # 4. Check for environment token
        env_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        if env_token:
            creds = parse_claude_token_input(env_token)
            if creds:
                await source.save(creds)
                return True, "Successfully configured Claude credentials from environment variable"

        # 5. Dual-Mode Flow: Interactive Desktop vs Headless Detection
        flow = ClaudeOAuthFlow()
        verifier = flow.generate_code_verifier()
        challenge = flow.generate_code_challenge(verifier)
        state = secrets.token_urlsafe(16)

        port = _find_free_port()
        redirect_uri = f"http://localhost:{port}/callback"
        auth_url = flow.build_authorization_url(redirect_uri, state, challenge)

        is_headless = not (
            os.environ.get("DISPLAY")
            or os.environ.get("WAYLAND_DISPLAY")
            or sys.platform in ("darwin", "win32")
        )

        if ui and hasattr(ui, "print"):
            ui.print("\n[bold cyan]Authenticate with your Claude Account (Pro / Max Subscription):[/bold cyan]")
            ui.print(f"  [link={auth_url}]{auth_url}[/link]\n")
            ui.print("[dim]Tip: In headless Linux/SSH, run 'claude setup-token' and paste the token directly.[/dim]")
        else:
            print(f"\nAuthenticate with your Claude Account:\n  {auth_url}\n")
            print("Tip: In headless Linux/SSH, run 'claude setup-token' and paste the token directly.")

        received_code: list[str] = []
        server_error: list[str] = []

        class OAuthCallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                if parsed.path == "/callback":
                    query = parse_qs(parsed.query)
                    req_state = query.get("state", [""])[0]
                    if req_state != state:
                        self.send_response(400)
                        self.send_header("Content-Type", "text/html")
                        self.end_headers()
                        self.wfile.write(b"State parameter mismatch. Authentication failed.")
                        server_error.append("State parameter mismatch")
                        return

                    code = query.get("code", [""])[0]
                    if code:
                        received_code.append(code)
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.end_headers()
                        self.wfile.write(
                            b"<!doctype html><html><body style='font-family:system-ui;padding:2rem;text-align:center'>"
                            b"<h2>Authentication successful!</h2>"
                            b"<p>You can close this tab and return to BuildRelay.</p>"
                            b"</body></html>"
                        )
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"No code provided.")
                else:
                    self.send_response(404)
                    self.end_headers()

        httpd = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
        httpd.timeout = 1.0

        if open_browser and not is_headless:
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass

        start_time = time.time()
        timeout = 180.0

        while time.time() - start_time < timeout:
            httpd.handle_request()
            if received_code or server_error:
                break

        httpd.server_close()

        if server_error:
            return False, f"Authentication failed: {server_error[0]}"

        if not received_code:
            return False, "Authentication timed out (180s). In headless environments, paste a token directly."

        try:
            creds = await flow.exchange_code_for_tokens(
                code=received_code[0],
                code_verifier=verifier,
                redirect_uri=redirect_uri,
            )
            await source.save(creds)
            return True, "Successfully authenticated with Claude account"
        except Exception as exc:
            return False, f"Failed to exchange code for tokens ({type(exc).__name__}: {exc})"

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
        return False, f"Claude authentication failed ({type(exc).__name__}: {exc})"


async def get_claude_oauth_model(model_name: str | None = None) -> Model:
    """
    Construct a Pydantic AI AnthropicModel configured with Claude OAuth bearer credentials.
    Supports auto-refreshing expired access tokens via refresh_token.
    """
    import anthropic

    raw_model = model_name or "claude-3-7-sonnet"
    if ":" in raw_model:
        raw_model = raw_model.split(":", 1)[1]

    # 1. Check environment variable token first
    env_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if env_token:
        creds = parse_claude_token_input(env_token)
        token = creds.access_token if creds else env_token
        client = anthropic.AsyncAnthropic(
            auth_token=token,
            default_headers={"anthropic-beta": CLAUDE_BETA_HEADER},
        )
        return AnthropicModel(raw_model, provider=AnthropicProvider(anthropic_client=client))

    # 2. Load from credential file
    source = ClaudeCredentialSource(get_claude_auth_path())
    creds = await source.load()

    if not creds:
        # Check CLI credentials fallback
        existing_cli = get_existing_claude_code_credentials_path()
        if existing_cli:
            try:
                data = json.loads(existing_cli.read_text(encoding="utf-8"))
                token = data.get("accessToken") or data.get("access_token")
                if token:
                    creds = ClaudeCredentials(access_token=token)
            except Exception:
                pass

    if not creds or not creds.access_token:
        raise ValueError(
            "Claude OAuth credentials missing. Run 'buildrelay config' to sign in with your Claude account."
        )

    # 3. Check expiration and attempt refresh if possible
    if creds.is_expired and creds.refresh_token:
        try:
            flow = ClaudeOAuthFlow()
            creds = await flow.refresh_tokens(creds.refresh_token)
            await source.save(creds)
        except Exception:
            pass  # Fall back to existing token

    client = anthropic.AsyncAnthropic(
        auth_token=creds.access_token,
        default_headers={"anthropic-beta": CLAUDE_BETA_HEADER},
    )
    return AnthropicModel(raw_model, provider=AnthropicProvider(anthropic_client=client))

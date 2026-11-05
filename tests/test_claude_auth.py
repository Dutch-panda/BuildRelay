"""Unit tests for Claude OAuth browser authentication and subscription sharing."""

import asyncio
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic_ai.models.anthropic import AnthropicModel

from tools.claude_auth import (
    CLAUDE_OAUTH_CLIENT_ID,
    ClaudeCredentials,
    ClaudeCredentialSource,
    ClaudeOAuthFlow,
    get_claude_oauth_model,
    is_claude_oauth_available,
    login_with_claude_browser,
    parse_claude_token_input,
)
from tools.model_tiers import (
    CLAUDE_OAUTH_TIERS,
    detect_provider,
    estimate_pipeline_budget,
    resolve_pipeline_models,
)
from tools.onboarding import check_credentials_configured, get_credential_status


def test_pkce_generation():
    flow = ClaudeOAuthFlow()
    verifier = flow.generate_code_verifier()
    assert len(verifier) >= 43
    challenge = flow.generate_code_challenge(verifier)
    assert len(challenge) >= 43
    assert "=" not in challenge


def test_authorization_url_building():
    flow = ClaudeOAuthFlow()
    url = flow.build_authorization_url(
        redirect_uri="http://localhost:8765/callback",
        state="xyz123",
        challenge="testchallenge",
    )
    assert "https://claude.ai/oauth/authorize" in url
    assert f"client_id={CLAUDE_OAUTH_CLIENT_ID}" in url
    assert "code_challenge=testchallenge" in url
    assert "code_challenge_method=S256" in url
    assert "state=xyz123" in url


@pytest.mark.anyio
async def test_credential_save_and_load(tmp_path):
    target = tmp_path / "subdir" / ".env.claude-auth.json"
    source = ClaudeCredentialSource(target)

    assert await source.load() is None

    creds = ClaudeCredentials(
        access_token="sk-ant-oat01-test-token-123",
        refresh_token="ref-456",
        expires_at=1893456000.0,
    )
    await source.save(creds)

    assert target.exists()
    assert (target.stat().st_mode & 0o777) == 0o600

    loaded = await source.load()
    assert loaded is not None
    assert loaded.access_token == "sk-ant-oat01-test-token-123"
    assert loaded.refresh_token == "ref-456"
    assert loaded.expires_at == 1893456000.0
    assert not loaded.is_expired


def test_parse_claude_token_input():
    # 1. Plain token
    c1 = parse_claude_token_input("sk-ant-oat01-plain-token-abc_123")
    assert c1 is not None
    assert c1.access_token == "sk-ant-oat01-plain-token-abc_123"

    # 2. JSON token payload (e.g. from claude setup-token or ~/.claude/.credentials.json)
    json_payload = json.dumps({
        "accessToken": "sk-ant-oat01-json-token-999",
        "refreshToken": "ref-xyz",
        "expiresAt": 1900000000.0,
    })
    c2 = parse_claude_token_input(json_payload)
    assert c2 is not None
    assert c2.access_token == "sk-ant-oat01-json-token-999"
    assert c2.refresh_token == "ref-xyz"

    # 3. Invalid token
    assert parse_claude_token_input("random string without token") is None


def test_is_claude_oauth_available_via_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat01-test-env")
    assert is_claude_oauth_available() is True


def test_is_claude_oauth_available_via_file(tmp_path, monkeypatch):
    auth_file = tmp_path / ".env.claude-auth.json"
    monkeypatch.setenv("CLAUDE_AUTH_FILE", str(auth_file))
    assert is_claude_oauth_available() is False

    auth_file.write_text(json.dumps({"access_token": "sk-ant-oat01-test-file"}), encoding="utf-8")
    assert is_claude_oauth_available() is True


def test_login_with_claude_token_input(tmp_path):
    target = tmp_path / ".env.claude-auth.json"
    ok, msg = login_with_claude_browser(
        auth_path=target,
        token_input="sk-ant-oat01-direct-input-456",
        open_browser=False,
    )
    assert ok is True
    assert "token input" in msg
    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["access_token"] == "sk-ant-oat01-direct-input-456"


def test_login_with_claude_browser_existing_active_session(tmp_path):
    target = tmp_path / ".env.claude-auth.json"
    target.write_text(
        json.dumps({
            "access_token": "sk-ant-oat01-active-session",
            "expires_at": 2000000000.0,
        }),
        encoding="utf-8",
    )
    ok, msg = login_with_claude_browser(auth_path=target, open_browser=False)
    assert ok is True
    assert "Existing active Claude session" in msg


@pytest.mark.anyio
async def test_get_claude_oauth_model_with_env(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat01-model-token")
    model = await get_claude_oauth_model("claude-3-7-sonnet")
    assert isinstance(model, AnthropicModel)
    assert model.model_name == "claude-3-7-sonnet"


def test_model_tiers_claude_oauth(monkeypatch):
    monkeypatch.setenv("BUILDRELAY_PROVIDER", "claude_oauth")
    assert detect_provider() == "claude_oauth"

    lineup = resolve_pipeline_models(tier="balanced")
    assert lineup["natasha"] == CLAUDE_OAUTH_TIERS["balanced"]["natasha"]
    assert lineup["taghi"] == CLAUDE_OAUTH_TIERS["balanced"]["taghi"]
    assert lineup["meti"] == CLAUDE_OAUTH_TIERS["balanced"]["meti"]

    monkeypatch.setattr("tools.model_tiers.is_claude_oauth_available", lambda: True)
    cost, text = estimate_pipeline_budget(lineup)
    assert cost == 0.0
    assert text == "$0.00 (Claude Subscription)"


def test_onboarding_credential_status_claude(monkeypatch, tmp_path):
    auth_file = tmp_path / ".env.claude-auth.json"
    auth_file.write_text(json.dumps({"access_token": "sk-ant-oat01-valid"}), encoding="utf-8")
    monkeypatch.setenv("CLAUDE_AUTH_FILE", str(auth_file))

    assert check_credentials_configured() is True
    status = get_credential_status()
    assert status["claude_oauth"] is True
    assert "Claude OAuth (Subscription)" in status["configured_providers"]

import json
from pathlib import Path
import pytest
from tools.graphify_tool import GraphifyVaultManager


def test_build_local_vault_graph_parses_multiline_and_inline_tags(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    specs_dir = vault / "specs"
    specs_dir.mkdir()

    # Note 1: Multiline bullet list tags
    note1 = specs_dir / "spec-auth.md"
    note1.write_text(
        "---\n"
        "id: task-auth-implement-claude-oauth-20261105\n"
        "domain: auth\n"
        "action: implement\n"
        "target: claude-oauth\n"
        "tags:\n"
        "  - auth\n"
        "  - oauth\n"
        "  - claude\n"
        "---\n"
        "# Implement Claude OAuth\n"
        "Body content here with [[spec-ui]].\n",
        encoding="utf-8",
    )

    # Note 2: Inline bracketed tags
    note2 = specs_dir / "spec-ui.md"
    note2.write_text(
        "---\n"
        "id: task-ui-redesign-login-screen-20261105\n"
        "domain: ui\n"
        "action: redesign\n"
        "target: login-screen\n"
        "tags: [ui, login, tailwind]\n"
        "---\n"
        "# Redesign Login Screen\n"
        "UI specification.\n",
        encoding="utf-8",
    )

    manager = GraphifyVaultManager(vault_path=str(vault))
    graph_data = manager._build_local_vault_graph()

    nodes = {n["id"]: n for n in graph_data["nodes"]}
    assert "task-auth-implement-claude-oauth-20261105" in nodes
    auth_node = nodes["task-auth-implement-claude-oauth-20261105"]
    assert auth_node["domain"] == "auth"
    assert auth_node["action"] == "implement"
    assert auth_node["tags"] == ["auth", "oauth", "claude"]
    assert auth_node["label"] == "Implement Claude OAuth"

    assert "task-ui-redesign-login-screen-20261105" in nodes
    ui_node = nodes["task-ui-redesign-login-screen-20261105"]
    assert ui_node["domain"] == "ui"
    assert ui_node["action"] == "redesign"
    assert ui_node["tags"] == ["ui", "login", "tailwind"]


def test_query_by_keywords_tag_match_scores_higher_than_body_match(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    manager = GraphifyVaultManager(vault_path=str(vault))

    # Construct two nodes directly in graph.json:
    # Node 1: Tag match on 'oauth'
    # Node 2: Incidental body/property match on 'oauth'
    manager.graph_json_path.write_text(
        json.dumps({
            "nodes": [
                {
                    "id": "task-auth-spec",
                    "label": "Authentication System",
                    "domain": "auth",
                    "tags": ["oauth", "security"],
                    "properties": {},
                },
                {
                    "id": "task-docs-spec",
                    "label": "Documentation Guide",
                    "domain": "core",
                    "tags": ["docs"],
                    "properties": {"notes": "Mentions oauth in a passing sentence"},
                },
            ],
            "edges": [],
        }),
        encoding="utf-8",
    )

    results = manager.query_by_keywords(["oauth"], min_score=0.05)
    assert len(results) == 2
    top_node, top_score = results[0]
    second_node, second_score = results[1]

    assert top_node["id"] == "task-auth-spec"
    assert second_node["id"] == "task-docs-spec"
    assert top_score > second_score


def test_query_by_keywords_multi_term_across_different_fields(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    manager = GraphifyVaultManager(vault_path=str(vault))

    manager.graph_json_path.write_text(
        json.dumps({
            "nodes": [
                {
                    "id": "task-sync-webhook",
                    "label": "Stripe Webhook Sync Handler",
                    "domain": "sync",
                    "tags": ["stripe", "billing"],
                    "properties": {"target": "stripe-webhook"},
                },
                {
                    "id": "task-other",
                    "label": "Generic Utility",
                    "domain": "core",
                    "tags": ["utility"],
                    "properties": {},
                },
            ],
            "edges": [],
        }),
        encoding="utf-8",
    )

    # Query has keywords appearing across different fields: 'sync' (domain) and 'stripe' (tag)
    results = manager.query_by_keywords(["sync", "stripe"], min_score=0.15)
    assert len(results) == 1
    node, score = results[0]
    assert node["id"] == "task-sync-webhook"
    assert score > 0.20


def test_query_by_keywords_filtering_and_top_k(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    manager = GraphifyVaultManager(vault_path=str(vault))

    manager.graph_json_path.write_text(
        json.dumps({
            "nodes": [
                {"id": f"node-{i}", "tags": ["search"], "label": f"Search Node {i}", "domain": "core"}
                for i in range(10)
            ],
            "edges": [],
        }),
        encoding="utf-8",
    )

    results = manager.query_by_keywords(["search"], top_k=3)
    assert len(results) == 3


def test_query_by_keywords_accepts_raw_string(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    manager = GraphifyVaultManager(vault_path=str(vault))

    manager.graph_json_path.write_text(
        json.dumps({
            "nodes": [
                {"id": "node-auth", "tags": ["auth", "token"], "domain": "auth", "label": "Token Auth"},
            ],
            "edges": [],
        }),
        encoding="utf-8",
    )

    results = manager.query_by_keywords("auth token", top_k=5)
    assert len(results) == 1
    assert results[0][0]["id"] == "node-auth"


def test_query_by_keywords_empty_query(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    manager = GraphifyVaultManager(vault_path=str(vault))

    assert manager.query_by_keywords([]) == []
    assert manager.query_by_keywords("") == []


@pytest.mark.anyio
async def test_natasha_and_graphify_end_to_end(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    manager = GraphifyVaultManager(vault_path=str(vault))

    from agents.natasha import NatashaRouter, TaskBrief
    from tools.project_notes import prepare_project

    router = NatashaRouter(vault_path=vault, model_name="test", graph_manager=manager)
    project = prepare_project(vault, "auth-app")

    brief = TaskBrief(
        task_id="task-auth-implement-google-oauth-20261105",
        project_id="auth-app",
        title="Implement Google OAuth Login",
        objective="Add OAuth2 token authentication for Google API login flow",
        slug="google-oauth-login",
        target_lead="taghi",
        research_questions=[],
    )

    saved_note = await router._write_brief_note(brief, project)
    assert saved_note.is_file()
    note_text = saved_note.read_text(encoding="utf-8")
    assert 'domain: "auth"' in note_text
    assert 'action: "implement"' in note_text
    assert "tags:" in note_text
    assert "- auth" in note_text

    # Now verify Graphify local graph extraction indexes this note
    graph_data = manager._build_local_vault_graph()
    matching_nodes = [n for n in graph_data["nodes"] if n["id"] == "task-auth-implement-google-oauth-20261105"]
    assert len(matching_nodes) == 1
    indexed_node = matching_nodes[0]
    assert indexed_node["domain"] == "auth"
    assert "auth" in indexed_node["tags"]

    # Now query by keywords
    results = manager.query_by_keywords(["auth", "oauth"])
    assert len(results) > 0
    top_node, score = results[0]
    assert top_node["id"] == "task-auth-implement-google-oauth-20261105"
    assert score > 0.20


@pytest.mark.anyio
async def test_session_repl_graph_command(tmp_path, capsys):
    vault = tmp_path / "vault"
    ws = tmp_path / "workspace"
    manager = GraphifyVaultManager(vault_path=str(vault))

    manager.graph_json_path.write_text(
        json.dumps({
            "nodes": [
                {
                    "id": "task-auth-token-session",
                    "label": "Token Session Manager",
                    "domain": "auth",
                    "tags": ["auth", "token", "session"],
                    "properties": {},
                }
            ],
            "edges": [],
        }),
        encoding="utf-8",
    )

    from tools.session import run_project_session

    inputs = ["/graph auth", "/exit"]
    await run_project_session(
        project_id="test-graph-proj",
        vault_path=vault,
        workspace_root=ws,
        input_func=lambda _: inputs.pop(0),
    )

    out = capsys.readouterr().out
    assert "Knowledge Graph Results for 'auth'" in out
    assert "task-auth-token-session" in out
    assert "Token Session Manager" in out


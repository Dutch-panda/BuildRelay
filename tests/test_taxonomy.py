"""Unit tests for ISSUE-05: Taxonomic Task Naming & Keyword Engine."""

import pytest
from tools.taxonomy import (
    DOMAINS,
    ACTIONS,
    classify_prompt,
    extract_keywords,
    generate_taxonomic_task_id,
    get_taxonomic_classification,
)


def test_extract_keywords():
    prompt = "Add persistent OAuth2 login authentication for Claude subscription!"
    kws = extract_keywords(prompt)
    assert "oauth2" in kws
    assert "login" in kws
    assert "authentication" in kws
    assert "claude" in kws
    assert "subscription" in kws
    # Stop words must be filtered
    assert "for" not in kws
    assert "the" not in kws


def test_classify_prompt_auth():
    prompt = "Implement persistent OAuth login for Claude subscription"
    domain, action, target = classify_prompt(prompt)
    assert domain == "auth"
    assert action == "implement"
    assert "claude" in target


def test_classify_prompt_ui():
    prompt = "Improve visual design and styling in bistro-erp"
    domain, action, target = classify_prompt(prompt)
    assert domain == "ui"
    assert action == "refactor"
    assert "bistro-erp" in target


def test_classify_prompt_db():
    prompt = "Refactor sqlite database schema and create migration tables"
    domain, action, target = classify_prompt(prompt)
    assert domain == "db"
    assert action == "refactor"


def test_classify_prompt_api():
    prompt = "Build REST API webhook route for spreadsheet sync"
    domain, action, target = classify_prompt(prompt)
    assert domain in ("api", "sync")
    assert action == "implement"


def test_generate_taxonomic_task_id():
    prompt = "Implement OAuth login for Claude"
    task_id = generate_taxonomic_task_id(prompt, date_str="20261106")
    assert task_id.startswith("task-auth-implement-claude-")
    assert task_id.endswith("-20261106")


def test_generate_taxonomic_task_id_fallback():
    # Prompt without clear domain or action
    prompt = "Random undefined activity"
    task_id = generate_taxonomic_task_id(prompt, date_str="20261106")
    assert task_id.startswith("task-")
    assert task_id.endswith("-20261106")
    assert "undefined" in task_id or "activity" in task_id


def test_generate_taxonomic_task_id_length_limit():
    long_prompt = "Implement very detailed and extremely complex multi-service architecture with thousands of distributed database shards and advanced real-time visualization dashboards"
    task_id = generate_taxonomic_task_id(long_prompt, date_str="20261106", max_chars=50)
    assert len(task_id) <= 50
    assert task_id.endswith("-20261106")


def test_get_taxonomic_classification():
    prompt = "Fix container volume permissions for Docker runtime"
    c = get_taxonomic_classification(prompt, date_str="20261106")
    assert c.domain == "infra"
    assert c.action == "fix"
    assert "container" in c.keywords or "docker" in c.keywords
    assert c.task_id.startswith("task-infra-fix-")

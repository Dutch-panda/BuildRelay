"""Taxonomic Task Naming & Keyword Engine.

Classifies developer prompts into structured engineering domains and actions,
extracts ranked search keywords, and generates semantic, predictable task IDs:
    task-<domain>-<action>-<target>-<date>
with fallback to:
    task-<slug>-<date>
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

# Domain taxonomy dictionaries: vertical -> keyword stems
DOMAINS: dict[str, set[str]] = {
    "auth": {
        "auth", "authentication", "oauth", "oauth2", "login", "signin", "signup",
        "logout", "token", "session", "sessions", "jwt", "password", "credential",
        "credentials", "permission", "permissions", "rbac", "authorisation",
        "authorization", "pkce", "secret", "secrets",
    },
    "ui": {
        "ui", "ux", "frontend", "front-end", "design", "redesign", "styling",
        "styles", "layout", "theme", "bento", "form", "forms", "dashboard",
        "dashboards", "component", "components", "css", "tailwind", "screen",
        "screens", "dialog", "modal", "page", "pages", "view", "views",
        "navbar", "sidebar", "widget", "widgets", "tui", "gui", "ergonomics",
    },
    "api": {
        "api", "rest", "endpoint", "endpoints", "route", "routes", "webhook",
        "webhooks", "graphql", "server", "controller", "handler", "handlers",
        "request", "response", "http", "router", "rpc", "payload",
    },
    "sync": {
        "sync", "synchronize", "synchronization", "ingest", "ingestion", "import",
        "export", "feed", "fetch", "pull", "stream", "backup", "pipeline",
        "polling", "batch",
    },
    "db": {
        "db", "database", "sqlite", "postgres", "postgresql", "mysql", "schema",
        "schemas", "migration", "migrations", "model", "models", "table", "tables",
        "query", "queries", "sql", "entity", "repository", "crud", "persistence",
        "storage",
    },
    "cli": {
        "cli", "terminal", "repl", "prompt", "console", "shell", "command",
        "commands", "argument", "arguments", "flag", "flags", "subcommand",
    },
    "eval": {
        "eval", "evaluate", "evaluation", "score", "scorecard", "benchmark",
        "benchmarks", "metric", "metrics", "audit", "assess", "assessment",
        "supervision",
    },
    "infra": {
        "infra", "infrastructure", "docker", "container", "containers", "sandbox",
        "image", "images", "volume", "volumes", "port", "ports", "compose",
        "deploy", "deployment", "runtime",
    },
    "test": {
        "test", "tests", "testing", "unittest", "regression", "fixture", "fixtures",
        "mock", "mocks", "assertion", "assertions", "coverage", "smoke",
    },
    "core": {
        "core", "workflow", "orchestrator", "engine", "agent", "agents", "lead",
        "leads", "relay", "coordination", "state", "ledger",
    },
}

# Action verbs taxonomy: canonical action -> synonyms/stems
ACTIONS: dict[str, set[str]] = {
    "setup": {
        "setup", "init", "initialize", "initialization", "bootstrap", "configure",
        "config", "configuration", "install", "installation", "start",
    },
    "implement": {
        "implement", "implementation", "add", "build", "create", "develop",
        "generate", "produce", "code", "write", "new", "integrate", "integration",
    },
    "refactor": {
        "refactor", "refactoring", "improve", "improvement", "enhance",
        "enhancement", "polish", "update", "modernize", "clean", "rewrite",
        "restructure", "rework", "redesign",
    },
    "fix": {
        "fix", "fixed", "patch", "repair", "resolve", "debug", "correct",
        "bugfix", "hotfix", "handle",
    },
    "migrate": {
        "migrate", "migration", "port", "convert", "conversion", "transition",
    },
    "verify": {
        "verify", "verification", "validate", "validation", "check", "inspect",
        "audit",
    },
    "optimize": {
        "optimize", "optimization", "accelerate", "speedup", "prune", "cache",
        "streamline",
    },
}

STOP_WORDS: set[str] = {
    # Articles, conjunctions, prepositions
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "at",
    "from", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "of", "in", "on", "up",
    "down", "as",
    # Pronouns & demonstratives
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "she", "it", "its",
    "it's", "they", "them", "this", "that", "these", "those", "which", "what",
    "who", "whom", "whose", "why", "how", "where",
    # Auxiliaries & common modals
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "can", "could", "should", "would",
    "will", "shall", "may", "might", "must",
    # Contraction fragments
    "t", "s", "d", "ll", "ve", "re", "m", "don", "doesn", "didn", "isn", "aren", "won",
    # Conversational filler
    "please", "just", "want", "need", "like", "also", "some", "any", "all",
    "each", "every", "other", "another", "than", "so", "tool", "app", "project",
    "task", "via",
}


@dataclass
class TaxonomicClassification:
    domain: str | None
    action: str | None
    target: str
    slug: str
    task_id: str
    keywords: list[str] = field(default_factory=list)


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    """Extract a deduplicated list of search keywords from text.

    Excludes standard stop words and single/two-character words (preserving digits).
    Preserves order of appearance.
    """
    cleaned = re.sub(r"'\w+", "", text.lower())
    tokens = re.findall(r"[a-z0-9_-]+", cleaned)
    keywords: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        token = token.strip("-_")
        if not token:
            continue
        if token in STOP_WORDS:
            continue
        if len(token) < 3 and not token.isdigit():
            continue
        if token not in seen:
            seen.add(token)
            keywords.append(token)
            if len(keywords) >= max_keywords:
                break

    return keywords


def classify_prompt(prompt: str) -> tuple[str | None, str | None, str]:
    """Classify a prompt into (domain, action, target_slug).

    Returns:
        domain: Detected canonical domain (e.g. 'auth', 'ui', 'db') or None.
        action: Detected canonical action (e.g. 'implement', 'refactor', 'fix') or None.
        target_slug: 1-3 word kebab-case slug identifying the primary entity/target.
    """
    cleaned = re.sub(r"'\w+", "", prompt.lower())
    tokens = re.findall(r"[a-z0-9_-]+", cleaned)

    # 1. Detect Domain
    detected_domain: str | None = None
    domain_match_count: int = 0
    for domain, kws in DOMAINS.items():
        count = sum(1 for t in tokens if t in kws)
        if count > domain_match_count:
            domain_match_count = count
            detected_domain = domain

    # 2. Detect Action
    detected_action: str | None = None
    for token in tokens:
        for action, verbs in ACTIONS.items():
            if token in verbs:
                detected_action = action
                break
        if detected_action:
            break

    # 3. Extract Target Nouns / Entities
    domain_kws = DOMAINS.get(detected_domain, set()) if detected_domain else set()
    action_verbs = ACTIONS.get(detected_action, set()) if detected_action else set()
    consumed_words = domain_kws | action_verbs | STOP_WORDS

    target_tokens = [
        t.strip("-_")
        for t in tokens
        if t not in consumed_words and (len(t) >= 3 or t.isdigit())
    ]

    if not target_tokens:
        # Fallback to general meaningful keywords if all were consumed
        target_tokens = [
            t.strip("-_")
            for t in tokens
            if t not in STOP_WORDS and (len(t) >= 3 or t.isdigit())
        ]

    target_slug = "-".join(target_tokens[:3]) if target_tokens else "system"
    # Ensure safe slug
    target_slug = re.sub(r"-+", "-", target_slug).strip("-")

    return detected_domain, detected_action, target_slug


def generate_taxonomic_task_id(
    prompt: str,
    date_str: str | None = None,
    max_chars: int = 60,
) -> str:
    """Generate a predictable, taxonomic task ID from a user prompt.

    Standard Format:
        task-<domain>-<action>-<target>-<date>
    Fallback Format (conversational/unclassified prompts):
        task-<slug>-<date>
    """
    date_part = date_str or datetime.now().strftime("%Y%m%d")
    domain, action, target = classify_prompt(prompt)

    parts = ["task"]
    if domain:
        parts.append(domain)
    if action:
        parts.append(action)
    if target:
        parts.append(target)

    # If neither domain nor action was identified, use standard slugification
    if not domain and not action:
        keywords = extract_keywords(prompt, max_keywords=4)
        slug = "-".join(keywords) if keywords else "task"
        parts = ["task", slug]

    parts.append(date_part)
    raw_id = "-".join(parts)
    # Sanitize kebab-case
    task_id = re.sub(r"[^a-z0-9-]+", "-", raw_id.lower())
    task_id = re.sub(r"-+", "-", task_id).strip("-")

    # Enforce max length constraint while preserving date suffix
    if len(task_id) > max_chars:
        excess = len(task_id) - max_chars
        prefix_limit = len(task_id) - len(date_part) - 1 - excess
        if prefix_limit > 10:
            prefix = task_id[:prefix_limit].rsplit("-", 1)[0]
            task_id = f"{prefix}-{date_part}"
        else:
            task_id = task_id[:max_chars].rstrip("-")

    return task_id


def get_taxonomic_classification(
    prompt: str,
    date_str: str | None = None,
) -> TaxonomicClassification:
    """Return a full structured TaxonomicClassification object for a prompt."""
    domain, action, target = classify_prompt(prompt)
    task_id = generate_taxonomic_task_id(prompt, date_str=date_str)
    keywords = extract_keywords(prompt, max_keywords=10)

    # Derive clean slug
    slug_parts = []
    if domain:
        slug_parts.append(domain)
    if action:
        slug_parts.append(action)
    if target:
        slug_parts.append(target)
    slug = "-".join(slug_parts) if slug_parts else target

    return TaxonomicClassification(
        domain=domain,
        action=action,
        target=target,
        slug=slug,
        task_id=task_id,
        keywords=keywords,
    )

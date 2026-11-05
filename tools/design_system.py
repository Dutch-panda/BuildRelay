"""Curated Design Archetypes & UI Design System for BuildRelay.

Provides studio-grade visual blueprints, Tailwind color tokens, layout structures,
and interactive state standards for Diba (UI/UX Design Lead) and Meti (Implementer).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from contracts import ClarificationOption, ClarificationQuestion


@dataclass(frozen=True)
class DesignArchetype:
    key: str
    name: str
    description: str
    surface_type: str
    theme: str
    color_palette: dict[str, str]
    layout_wireframe: str
    typography_scale: str
    state_styling: dict[str, str]
    recommended_keywords: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "surface_type": self.surface_type,
            "theme": self.theme,
            "color_palette": self.color_palette,
            "layout_wireframe": self.layout_wireframe,
            "typography_scale": self.typography_scale,
            "state_styling": self.state_styling,
        }


ARCHETYPES: dict[str, DesignArchetype] = {
    "linear_dark": DesignArchetype(
        key="linear_dark",
        name="Linear Dark Minimalist",
        description="Deep midnight palette, subtle 1px borders, ambient glowing accents, and keyboard-first command ergonomics.",
        surface_type="web_form",
        theme="linear_dark",
        color_palette={
            "primary": "#5e6ad2",       # Linear purple/indigo
            "background": "#08090a",    # Deep midnight void
            "surface": "#121417",       # Elevated card zinc
            "text": "#e6e8eb",          # Crisp light gray
            "border": "#22262b",        # Subtle dark border
            "success": "#4ade80",       # Clean emerald
            "error": "#f87171",         # Soft red alert
        },
        layout_wireframe=(
            "Sticky top navbar with brand mark and active project pill; "
            "centered max-w-xl card container with rounded-2xl border border-zinc-800/80 bg-zinc-950/70 backdrop-blur-xl shadow-2xl; "
            "floating action dock with primary action and keyboard shortcut badge (Cmd+Enter); "
            "subtle ambient radial gradient glow in page background."
        ),
        typography_scale="Inter/Geist: h1 text-2xl font-semibold tracking-tight, body text-sm text-zinc-300, labels text-xs font-medium uppercase tracking-wider text-zinc-400",
        state_styling={
            "empty": "Subtle dashed border card with centered icon and 'No items created yet' prompt.",
            "validating": "Micro-feedback text-rose-400 text-xs mt-1 transition-all duration-200 with shake animation.",
            "submitting": "Button opacity-80 cursor-wait with inline SVG spinner and disabled field inputs.",
            "success": "Fixed bottom-right sliding toast banner with emerald glow and auto-dismiss timer.",
            "error": "Prominent rounded-xl border border-rose-500/30 bg-rose-950/40 text-rose-200 px-4 py-3 alert card.",
        },
        recommended_keywords=("command", "linear", "minimalist", "clean", "dark", "dev", "tool", "fast", "input", "form"),
    ),
    "bento_dashboard": DesignArchetype(
        key="bento_dashboard",
        name="Executive Bento Dashboard",
        description="Asymmetrical responsive grid with live KPI metric tiles, status pulse pills, rounded-2xl bordered cards, and filter streams.",
        surface_type="dashboard",
        theme="bento_dark",
        color_palette={
            "primary": "#10b981",       # Vibrant emerald accent
            "background": "#09090b",    # Zinc black
            "surface": "#18181b",       # Card surface
            "text": "#f4f4f5",          # Off-white text
            "border": "#27272a",        # Card border
            "success": "#10b981",       # Metric positive
            "error": "#ef4444",         # Metric alert
        },
        layout_wireframe=(
            "Header with title, date badge, and live refresh status pulse; "
            "top row 3-column KPI metric summary tiles (count, rate, status) with trend badges; "
            "main area 2-column asymmetric Bento grid: left 2/3 live activity feed & table, right 1/3 quick entry form and filter toggles; "
            "responsive single-column collapse on mobile viewports (<768px)."
        ),
        typography_scale="Inter: metrics text-3xl font-bold font-mono, card titles text-base font-medium text-zinc-100, captions text-xs text-zinc-400",
        state_styling={
            "empty": "Hero metric tiles displaying '--' with an inviting 'Get Started' action card.",
            "validating": "Inline border-rose-500 focus ring with immediate input helper text.",
            "submitting": "Pulsing skeleton loader bars replacing metric values during fetch/sync.",
            "success": "KPI card border flashes emerald with smooth count-up animation.",
            "error": "Global warning pill at header top with retry button.",
        },
        recommended_keywords=("dashboard", "bento", "analytics", "metrics", "monitor", "overview", "stats", "kpi", "summary"),
    ),
    "stripe_enterprise": DesignArchetype(
        key="stripe_enterprise",
        name="Stripe Enterprise Clean",
        description="High-density clean light surface, subtle slate borders, crisp status badges, structured tabular data, and prominent action buttons.",
        surface_type="web_form",
        theme="stripe_light",
        color_palette={
            "primary": "#6366f1",       # Royal indigo
            "background": "#f8fafc",    # Slate off-white
            "surface": "#ffffff",       # Pure white card
            "text": "#0f172a",          # Deep slate text
            "border": "#e2e8f0",        # Light slate border
            "success": "#059669",       # Deep emerald badge
            "error": "#dc2626",         # Deep ruby alert
        },
        layout_wireframe=(
            "Clean top header with brand logo and account status; "
            "elevated white card with soft shadow-sm and 1px border-slate-200; "
            "2-column balanced form grid with explicit field labels, helper tooltips, and required markers; "
            "sticky bottom footer bar with secondary 'Cancel' and primary 'Submit' action buttons."
        ),
        typography_scale="system-ui: titles text-xl font-semibold text-slate-900, labels text-sm font-medium text-slate-700, helpers text-xs text-slate-500",
        state_styling={
            "empty": "Clean blank inputs with subtle placeholder examples (e.g. 'e.g. ACME Corp').",
            "validating": "Input border turns ruby-500 with exclamation icon and red validation message.",
            "submitting": "Primary button switches to loading state with spinner and disabled pointer.",
            "success": "Smooth green checkmark banner confirming submission with record ID copy link.",
            "error": "Bordered alert banner at form top detailing failure reasons.",
        },
        recommended_keywords=("enterprise", "stripe", "light", "business", "billing", "settings", "portal", "classic", "table"),
    ),
    "split_pane_workspace": DesignArchetype(
        key="split_pane_workspace",
        name="Split-Pane Studio Workspace",
        description="Left sidebar navigation and filterable item list with right-hand master-detail inspector, live editor, and responsive drawer.",
        surface_type="dashboard",
        theme="workspace_neutral",
        color_palette={
            "primary": "#38bdf8",       # Sky cyan accent
            "background": "#0f172a",    # Dark slate void
            "surface": "#1e293b",       # Slate surface
            "text": "#f8fafc",          # High-contrast white
            "border": "#334155",        # Slate border
            "success": "#34d399",       # Mint green
            "error": "#f87171",         # Coral red
        },
        layout_wireframe=(
            "Full-height split layout: "
            "left sidebar (w-72) featuring search bar, category filter pills, and active item list; "
            "right master-detail pane featuring selected item header, tabbed detail views, and live editing form; "
            "collapsible on mobile into tabbed views."
        ),
        typography_scale="Inter: headings text-lg font-semibold, list items text-sm font-medium, meta tags text-xs font-mono",
        state_styling={
            "empty": "Right pane renders an empty-state illustration: 'Select an item from the left to view details.'",
            "validating": "Badge on edited tab turns amber until required fields are valid.",
            "submitting": "Saving pill indicator appears in top right corner: 'Syncing changes...'",
            "success": "Pill changes to green: 'All changes saved.'",
            "error": "Sticky alert banner above detail pane with retry action.",
        },
        recommended_keywords=("split", "workspace", "editor", "sidebar", "master", "detail", "explorer", "browser", "manage"),
    ),
}

DEFAULT_ARCHETYPE = ARCHETYPES["linear_dark"]


def get_archetype(key: str | None) -> DesignArchetype:
    """Retrieve an archetype by key, defaulting to Linear Dark."""
    if not key:
        return DEFAULT_ARCHETYPE
    clean_key = key.strip().lower()
    return ARCHETYPES.get(clean_key, DEFAULT_ARCHETYPE)


def list_archetypes() -> list[DesignArchetype]:
    """Return all available curated design archetypes."""
    return list(ARCHETYPES.values())


def detect_recommended_archetype(prompt: str) -> DesignArchetype:
    """
    Deterministically suggest the best-fitting design archetype based on prompt semantics.
    """
    text = prompt.lower()
    scores: dict[str, int] = {}
    for key, archetype in ARCHETYPES.items():
        score = sum(1 for kw in archetype.recommended_keywords if re.search(r"\b" + re.escape(kw) + r"\b", text))
        scores[key] = score

    best_key = max(scores, key=lambda k: scores[k])
    if scores[best_key] > 0:
        return ARCHETYPES[best_key]
    return DEFAULT_ARCHETYPE


def format_archetypes_for_prompt() -> str:
    """Format available archetypes into a rich Markdown guide for agent prompts."""
    lines = ["### Curated Design Archetypes Available:"]
    for arch in ARCHETYPES.values():
        lines.append(f"- **{arch.name}** (`{arch.key}`): {arch.description}")
        lines.append(f"  *Palette:* Primary `{arch.color_palette['primary']}`, Background `{arch.color_palette['background']}`, Surface `{arch.color_palette['surface']}`")
        lines.append(f"  *Layout:* {arch.layout_wireframe}")
    return "\n".join(lines)


def format_archetype_grill_question(recommended_key: str | None = None) -> ClarificationQuestion:
    """Generate the standard Design Archetype grill question with options."""
    rec_key = recommended_key or "linear_dark"
    options = []
    for key, arch in ARCHETYPES.items():
        is_rec = (key == rec_key)
        label = f"{arch.name} — {arch.description[:60]}..."
        if is_rec:
            label = f"[Recommended] {label}"
        options.append(ClarificationOption(key=key, label=label, is_default=is_rec))

    # Ensure exactly one option is marked is_default
    has_default = any(o.is_default for o in options)
    if not has_default and options:
        options[0].is_default = True

    return ClarificationQuestion(
        id="ui_design_archetype",
        category="ui_archetype",
        question="Which curated visual design archetype should Diba apply to this user interface?",
        options=options,
    )

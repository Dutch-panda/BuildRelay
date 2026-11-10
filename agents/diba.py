"""Diba — Principal UI/UX & Product Design Lead for BuildRelay.

Diba is an on-demand specialist agent responsible for visual hierarchy, design systems,
Tailwind CSS tokens, layout wireframes, responsive ergonomics, and interactive UI states.
She wakes up whenever a task requires a frontend or user entry surface, conducting dedicated
design grill-me interviews and producing studio-grade UIDesignSpec deliverables.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from pydantic_ai import Agent
from pydantic_ai.models import Model

from contracts import ClarificationOption, ClarificationQuestion, TechnicalSpec, UIDesignSpec, UIFieldSpec, UIPrototypeResult
from tools.design_system import (
    DEFAULT_ARCHETYPE,
    detect_recommended_archetype,
    format_archetype_grill_question,
    format_archetypes_for_prompt,
    get_archetype,
)
from tools.graphify_tool import GraphifyVaultManager
from tools.project_notes import prepare_project
from tools.token_analytics import extract_usage
from tools.ui import print_agent
from tools.vault_infra import register_graph_tools, register_note_writer_tool, update_vault_graph


class DibaDesigner:
    """
    Principal UI/UX & Product Design Lead.
    """

    def __init__(
        self,
        vault_path: str | Path = "./vault",
        model_name: str | Model = "openai:gpt-4o",
        graph_manager: GraphifyVaultManager | None = None,
        specs_dir: str | Path | None = None,
    ):
        self.vault_path = Path(vault_path)
        self.model_name = model_name
        self.specs_dir = Path(specs_dir) if specs_dir is not None else self.vault_path / "specs"
        self.graph_manager = graph_manager or GraphifyVaultManager(vault_path=str(self.vault_path))

        archetypes_guide = format_archetypes_for_prompt()

        self.agent = Agent(
            model_name,
            output_type=UIDesignSpec,
            model_settings={"cache": True},
            system_prompt=(
                "You are Diba, the Principal UI/UX & Product Design Lead of BuildRelay. "
                "Your mission is to transform user requests and technical backend architecture into world-class, "
                "production-grade user interfaces that feel like modern, high-end SaaS applications (e.g. Linear, Stripe, Vercel). "
                "Never produce bland, generic HTML forms or primitive unstyled tables.\n\n"
                f"{archetypes_guide}\n\n"
                "STUDIO-GRADE DESIGN SYSTEM & STYLING STANDARDS:\n"
                "1. Visual Archetype & Theme:\n"
                "   - Assign 'archetype' to one of: 'linear_dark', 'bento_dashboard', 'stripe_enterprise', 'split_pane_workspace'.\n"
                "   - Populate explicit hex tokens in 'color_palette' (primary, background, surface, text, border, success, error).\n"
                "   - Surface Type: 'web_form', 'dashboard', 'apps_script_dialog', 'cli_interactive', or 'webhook_portal'.\n"
                "2. Component Wireframe & Visual Hierarchy ('component_layout'):\n"
                "   - Specify concrete visual hierarchy: sticky brand header with live status pill, elevated card containers with subtle borders (e.g. border-zinc-800 bg-zinc-900/60 backdrop-blur-xl shadow-2xl), rounded-xl data tables, floating action dock, and modal overlays.\n"
                "3. User Fields & Input Ergonomics ('form_fields'):\n"
                "   - Specify every input with clear id, label, input_type, placeholder example (e.g. 'e.g. ACME Corp'), required flag, and explicit validation_rules.\n"
                "4. Complete Interactive States ('states' dict):\n"
                "   - Always provide distinct specifications for all 5 interactive states: 'empty', 'validating', 'submitting', 'success', 'error'.\n"
                "5. Responsive Ergonomics ('responsive_breakpoints'):\n"
                "   - Mobile-first single-column (<640px), balanced multi-column grid on desktop (>=768px).\n"
                "6. Design Grill-Me Questions ('clarification_questions'):\n"
                "   - Emit up to 6 targeted, highly ergonomic UI clarification questions covering archetype, layout density, validation timing, and empty states.\n"
                "   - Every question MUST provide 2 to 4 options with exactly one marked is_default=True."
            ),
        )

        register_graph_tools(self.agent, self.graph_manager, "Diba")
        register_note_writer_tool(
            self.agent,
            self.specs_dir,
            tool_name="write_specs_note",
            category="Specs",
            directory_name="Specs",
            agent_name="Diba",
        )

        self.prototype_agent = Agent(
            model_name,
            output_type=str,
            model_settings={"cache": True},
            system_prompt=(
                "You are Diba, the Principal UI/UX & Product Design Lead. "
                "Your job is to generate a standalone, studio-grade, fully working HTML/Tailwind CSS interactive prototype. "
                "The prototype must run 100% offline in a web browser with ZERO backend API dependencies.\n\n"
                "MANDATORY PROTOTYPE STANDARDS:\n"
                "1. Self-contained HTML with Tailwind CSS CDN: <script src='https://cdn.tailwindcss.com'></script>\n"
                "2. Modern typography (Plus Jakarta Sans or Inter font).\n"
                "3. Visual Archetype styling (deep dark or crisp executive theme with subtle borders and shadows).\n"
                "4. An interactive top state-switcher bar allowing the user to click between 5 states: 'empty', 'validating', 'submitting', 'success', 'error'.\n"
                "5. Embedded client-side in-memory mock engine in a <script> block:\n"
                "   - Intercepts form submissions and click events without network calls.\n"
                "   - Pre-populates mock data in table/cards.\n"
                "   - Simulates validation errors when inputs are invalid.\n"
                "   - Shows button loading spinner on submit, then displays success confirmation with transaction ID.\n"
                "6. Return ONLY the raw valid HTML code without markdown code fences or conversational prose."
            ),
        )

    @staticmethod
    def is_ui_task(prompt: str, spec: TechnicalSpec | None = None) -> bool:
        """
        Determines whether a task requires frontend/UI surface design.
        """
        if spec and getattr(spec, "ui_spec", None):
            return True
        if spec and getattr(spec, "input_interface_spec", None):
            interface_desc = str(spec.input_interface_spec).lower()
            if any(w in interface_desc for w in ("form", "html", "web", "dashboard", "ui", "view", "page", "table")):
                return True

        text = prompt.lower()
        ui_keywords = {
            "ui", "ux", "design", "redesign", "frontend", "front-end", "web", "website", "form",
            "html", "page", "dashboard", "preview", "button", "screen", "dialog",
            "modal", "view", "component", "tailwind", "css", "layout", "style", "styling", "styles",
            "theme", "tui", "interface", "portal", "display", "look", "aesthetic", "colors",
            "visual", "visuals", "bento", "navbar", "sidebar", "cleaner", "erp", "gui",
            "typography", "cards", "responsive", "mobile", "darkmode", "palette", "wireframe",
            "archetype", "banner", "header", "footer", "icon", "icons", "widgets"
        }
        words = set(re.findall(r"[a-z0-9_-]+", text))
        return bool(words & ui_keywords)

    async def design_ui(
        self,
        task_id: str,
        prompt_context: str,
        spec: TechnicalSpec | None = None,
        project_id: str | None = None,
    ) -> UIDesignSpec:
        """
        Produce a studio-grade UIDesignSpec for the task.
        """
        print_agent("diba", f"Designing studio-grade UI/UX surface specification for task: {task_id}")

        recommended_archetype = detect_recommended_archetype(prompt_context)
        backend_summary = ""
        if spec:
            backend_summary = (
                f"\n\n--- Backend Architecture Overview ---\n"
                f"{spec.architecture_overview[:600]}\n"
                f"Input Interface Spec: {spec.input_interface_spec or 'Standard web entry'}\n"
                f"--- End Backend Context ---"
            )

        prompt = (
            f"Task ID: {task_id}\n"
            f"Project ID: {project_id or 'none'}\n"
            f"Recommended Default Archetype: {recommended_archetype.name} ('{recommended_archetype.key}')\n\n"
            f"User Prompt / Design Context:\n{prompt_context}{backend_summary}\n\n"
            f"Design the complete, production-grade UI/UX specification adhering to BuildRelay design system standards."
        )

        result = await self.agent.run(prompt)
        ui_spec: UIDesignSpec = result.output

        if not getattr(ui_spec, "archetype", None):
            ui_spec.archetype = recommended_archetype.key

        # Inject archetype grill question if missing
        existing_keys = {q.id for q in (ui_spec.clarification_questions or [])}
        if "ui_design_archetype" not in existing_keys:
            archetype_q = format_archetype_grill_question(ui_spec.archetype)
            ui_spec.clarification_questions = [archetype_q] + (ui_spec.clarification_questions or [])

        # Extract and record token usage
        token_usage = extract_usage(result)
        if token_usage:
            token_usage["model"] = str(self.model_name)
            ui_spec.token_usage = token_usage

        # Persist markdown spec note
        await self.write_ui_spec_note(task_id, ui_spec, project_id=project_id)
        return ui_spec

    async def conduct_ui_review(
        self,
        ui_spec: UIDesignSpec,
        task_id: str,
        prompt_context: str,
        auto: bool = False,
        input_func: Callable[[str], str] | None = None,
        project_id: str | None = None,
    ) -> tuple[UIDesignSpec, bool]:
        """
        Conduct the interactive Diba UI/UX Grill-Me interview and review gate.
        Returns: (updated_ui_spec, quit_requested)
        """
        from tools.grill import format_grill_answers_for_prompt, has_non_default_answers, run_grill_session
        from tools.ui import prompt_spec_approval_gate

        current_ui = ui_spec
        grill_completed = False

        while True:
            # Step 1: Run Diba's dedicated UI/UX grill questions once
            if not grill_completed and getattr(current_ui, "clarification_questions", None):
                answers, quit_requested = run_grill_session(
                    current_ui.clarification_questions,
                    agent_name="diba",
                    title="🎨 Diba UI/UX & Product Design Grill",
                    auto=auto,
                    input_func=input_func,
                    max_questions=8,
                )
                if quit_requested:
                    return current_ui, True
                grill_completed = True

                # Check if chosen archetype changed
                for q in (current_ui.clarification_questions or []):
                    if q.id == "ui_design_archetype":
                        chosen_val = q.selected_option or answers.get(q.id)
                        chosen_arch = None
                        if chosen_val:
                            # Check by key or by description/label
                            chosen_arch = get_archetype(str(chosen_val))
                            if not chosen_arch:
                                for opt in q.options:
                                    if str(opt.key) == str(chosen_val) or opt.label == chosen_val:
                                        chosen_arch = get_archetype(opt.description or opt.key)
                                        break
                        if chosen_arch and chosen_arch.key != current_ui.archetype:
                            current_ui.archetype = chosen_arch.key
                            current_ui.theme = chosen_arch.theme
                            current_ui.color_palette = dict(chosen_arch.color_palette)
                            current_ui.component_layout = chosen_arch.layout_wireframe
                            current_ui.states = dict(chosen_arch.state_styling)

                if not auto and has_non_default_answers(current_ui.clarification_questions, answers):
                    from tools.ui import print_agent
                    print_agent("diba", "Re-synthesizing UI/UX design with user decisions (AI analyzing)...")
                    formatted_decisions = format_grill_answers_for_prompt(answers, current_ui.clarification_questions)
                    updated_context = f"{prompt_context}\n\nUser UI/UX Decisions:\n{formatted_decisions}"
                    current_ui = await self.design_ui(task_id, updated_context, project_id=project_id)

            # Step 2: Present UI spec approval gate
            action, feedback = prompt_spec_approval_gate(
                current_ui,
                auto=auto,
                input_func=input_func,
            )
            if action == "quit":
                return current_ui, True
            elif action == "revise" and feedback:
                updated_context = f"{prompt_context}\n\nUser UI/UX Revisions Required:\n{feedback}"
                current_ui = await self.design_ui(task_id, updated_context, project_id=project_id)
            else:
                return current_ui, False

    async def write_ui_spec_note(
        self,
        task_id: str,
        ui_spec: UIDesignSpec,
        project_id: str | None = None,
    ) -> Path:
        """
        Persist the studio-grade UI/UX design specification to vault/specs/spec-<task_id>-ui.md.
        """
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        note_path = self.specs_dir / f"spec-{task_id}-ui.md"
        project = prepare_project(self.vault_path, project_id)
        timestamp = datetime.now().isoformat()

        fields_table = "| Field ID | Label | Type | Required | Constraints |\n| :--- | :--- | :---: | :---: | :--- |\n"
        for fld in getattr(ui_spec, "form_fields", []):
            fields_table += f"| `{fld.id}` | {fld.label} | `{fld.input_type}` | {'Yes' if fld.required else 'No'} | {fld.validation_rules or 'Standard'} |\n"

        palette_table = "| Token | Value |\n| :--- | :---: |\n"
        for tok, col in getattr(ui_spec, "color_palette", {}).items():
            palette_table += f"| {tok.capitalize()} | `{col}` |\n"

        states_list = ""
        for st_name, st_desc in getattr(ui_spec, "states", {}).items():
            states_list += f"- **{st_name.capitalize()}:** {st_desc}\n"

        archetype_name = getattr(ui_spec, "archetype", "linear_dark")

        from tools.taxonomy import get_taxonomic_classification
        classification = get_taxonomic_classification(f"{task_id} {ui_spec.surface_type}")
        diba_tags = [t for t in ["ui", "ux", "design", "diba", classification.target, *classification.keywords] if t]
        diba_tags = list(dict.fromkeys(diba_tags))
        tags_block = "tags:\n" + "\n".join(f"  - {t}" for t in diba_tags) + "\n"

        markdown_content = f"""---
id: "spec-{task_id}-ui"
type: "ui-design-spec"
agent: "diba"
task_id: "{task_id}"
domain: "ui"
action: "{classification.action or 'implement'}"
target: "{classification.target}"
archetype: "{archetype_name}"
{tags_block}{project.frontmatter}created_at: "{timestamp}"
links: ["[[spec-{task_id}]]"]
---
# UI/UX Design Specification: {task_id}

> **Lead:** Diba (UI/UX & Product Design Lead)  
> **Visual Archetype:** `{archetype_name}`

## Surface Type & Visual Theme
- **Surface Type:** `{ui_spec.surface_type}`
- **Theme:** `{ui_spec.theme}`
- **Design Archetype:** `{archetype_name}`
- **Responsive Breakpoints:** {ui_spec.responsive_breakpoints}

## Color System Tokens
{palette_table}

## Component Hierarchy & Wireframe
{ui_spec.component_layout}

## Form Fields & Input Constraints
{fields_table}

## Interactive UI States (5 Discrete States)
{states_list}
"""
        note_path.write_text(markdown_content, encoding="utf-8")
        print_agent("diba", f"Saved UI/UX design specification to: {note_path}")
        await update_vault_graph(self.graph_manager, note_path)
        return note_path

    def _build_default_prototype_html(
        self,
        task_id: str,
        prompt_context: str,
        ui_spec: UIDesignSpec | None = None,
        feedback: str | None = None,
    ) -> str:
        """
        Builds a self-contained, working HTML/Tailwind CSS interactive prototype with an in-memory mock engine.
        Supports 5 discrete interactive states: empty, validating, submitting, success, error.
        """
        palette = (ui_spec.color_palette if ui_spec else None) or {
            "primary": "#3b82f6",
            "background": "#0f172a",
            "surface": "#1e293b",
            "text": "#f8fafc",
            "border": "#334155",
            "success": "#10b981",
            "error": "#ef4444",
        }
        archetype_name = getattr(ui_spec, "archetype", "linear_dark") if ui_spec else "linear_dark"

        # Build dynamic form fields HTML
        fields = (ui_spec.form_fields if ui_spec else None) or [
            UIFieldSpec(id="title", label="Item Title", input_type="text", placeholder="e.g. Inbound Inquiry #402", required=True),
            UIFieldSpec(id="contact_email", label="Contact Email", input_type="email", placeholder="alex@company.com", required=True),
            UIFieldSpec(id="description", label="Description & Scope", input_type="textarea", placeholder="Provide relevant details...", required=False),
        ]

        inputs_html = []
        for f in fields:
            req_mark = '<span class="text-rose-400">*</span>' if f.required else '<span class="text-xs text-slate-500 font-normal ml-1">(optional)</span>'
            if f.input_type == "textarea":
                inputs_html.append(f"""
                <div class="field-group">
                    <label for="{f.id}" class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">{f.label} {req_mark}</label>
                    <textarea id="{f.id}" name="{f.id}" rows="3" placeholder="{f.placeholder or ''}" {"required" if f.required else ""}
                        class="w-full px-3.5 py-2.5 rounded-lg bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"></textarea>
                    <p id="{f.id}-error" class="hidden text-xs text-rose-400 mt-1">Please enter a valid value.</p>
                </div>""")
            else:
                inputs_html.append(f"""
                <div class="field-group">
                    <label for="{f.id}" class="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">{f.label} {req_mark}</label>
                    <input type="{f.input_type}" id="{f.id}" name="{f.id}" placeholder="{f.placeholder or ''}" {"required" if f.required else ""}
                        class="w-full px-3.5 py-2.5 rounded-lg bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all" />
                    <p id="{f.id}-error" class="hidden text-xs text-rose-400 mt-1">Please enter a valid value.</p>
                </div>""")

        fields_block = "\n".join(inputs_html)
        feedback_notice = ""
        if feedback:
            feedback_notice = f"""
            <div class="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-200 text-xs flex items-center gap-2">
                <span>⚡</span> <span>Refinement applied: {feedback}</span>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-950">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BuildRelay Prototype — {task_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
        code, pre {{ font-family: 'JetBrains Mono', monospace; }}
    </style>
</head>
<body class="min-h-full bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-indigo-500 selection:text-white">

    <!-- Top State-Switcher Toolbar (Interactive Human-in-the-Loop HUD) -->
    <header class="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-4 py-2.5 shadow-lg">
        <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs">
            <div class="flex items-center gap-2">
                <span class="inline-flex items-center justify-center w-6 h-6 rounded-md bg-indigo-600/30 text-indigo-400 font-bold border border-indigo-500/40">✦</span>
                <span class="font-bold text-white tracking-wide">Diba Prototype HUD</span>
                <span class="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-mono text-[11px]">{archetype_name}</span>
            </div>

            <!-- 5 Discrete States Switcher Bar -->
            <div class="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-lg border border-slate-800" role="toolbar" aria-label="Interactive State Controls">
                <span class="text-slate-500 font-semibold px-2 uppercase tracking-wider text-[10px]">Test State:</span>
                <button type="button" onclick="switchState('empty')" id="btn-state-empty" class="state-btn px-2.5 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition active bg-indigo-600/30 text-indigo-300 font-semibold">1. Empty</button>
                <button type="button" onclick="switchState('validating')" id="btn-state-validating" class="state-btn px-2.5 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition">2. Validating</button>
                <button type="button" onclick="switchState('submitting')" id="btn-state-submitting" class="state-btn px-2.5 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition">3. Submitting</button>
                <button type="button" onclick="switchState('success')" id="btn-state-success" class="state-btn px-2.5 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition">4. Success</button>
                <button type="button" onclick="switchState('error')" id="btn-state-error" class="state-btn px-2.5 py-1 rounded-md text-slate-300 hover:text-white hover:bg-slate-800 transition">5. Error</button>
            </div>

            <div class="flex items-center gap-2">
                <button type="button" onclick="resetPrototype()" class="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition border border-slate-700">↺ Reset Form</button>
            </div>
        </div>
    </header>

    <!-- Main Prototype Canvas -->
    <main class="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col justify-center">
        {feedback_notice}

        <!-- Status & Feedback Banners for States -->
        <div id="state-banner-container" class="space-y-3 mb-6">
            <!-- Validating State Banner -->
            <div id="state-banner-validating" class="hidden p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-200 text-xs flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                    <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                    <span><strong>Validation in Progress:</strong> Checking format constraints and required entries...</span>
                </div>
                <span class="text-amber-400/80 font-mono text-[11px]">Real-time Client Linting</span>
            </div>

            <!-- Success State Banner -->
            <div id="state-banner-success" class="hidden p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-200 text-sm flex items-start gap-3">
                <span class="text-emerald-400 text-lg leading-none mt-0.5">✓</span>
                <div class="flex-1">
                    <p class="font-bold text-emerald-300">Submission Successful!</p>
                    <p class="text-xs text-emerald-400/90 mt-0.5" id="success-message">Record persisted in local in-memory mock engine with zero backend latency.</p>
                </div>
            </div>

            <!-- Error State Banner -->
            <div id="state-banner-error" class="hidden p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-200 text-sm flex items-start gap-3">
                <span class="text-rose-400 text-lg leading-none mt-0.5">✕</span>
                <div class="flex-1">
                    <p class="font-bold text-rose-300">Action Failed</p>
                    <p class="text-xs text-rose-400/90 mt-0.5" id="error-message">Simulated server error. Check required inputs or retry.</p>
                </div>
            </div>
        </div>

        <!-- Working Prototype Card -->
        <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden backdrop-blur-xl">
            <div class="flex items-center justify-between pb-6 mb-6 border-b border-slate-800">
                <div>
                    <h1 class="text-xl sm:text-2xl font-bold text-white tracking-tight">{task_id}</h1>
                    <p class="text-xs text-slate-400 mt-1">{prompt_context[:120]}...</p>
                </div>
                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                    Live Mock
                </span>
            </div>

            <!-- Form with In-Memory Mock Handler -->
            <form id="prototype-form" onsubmit="handleMockSubmit(event)" class="space-y-4">
                {fields_block}

                <div class="pt-4 flex items-center justify-end gap-3 border-t border-slate-800/80">
                    <button type="button" onclick="resetPrototype()" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition border border-slate-700/80">
                        Clear
                    </button>
                    <button type="submit" id="btn-submit" class="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition flex items-center gap-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed">
                        <span id="btn-submit-spinner" class="hidden w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                        <span id="btn-submit-text">Submit Action</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- In-Memory Data Table (Zero-to-One Realistic Feel) -->
        <div class="mt-8 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div class="flex items-center justify-between mb-3 text-xs">
                <span class="font-bold text-slate-300 uppercase tracking-wider">In-Memory Mock Fixtures (<span id="mock-count">2</span>)</span>
                <span class="text-slate-500 text-[11px]">Stored locally in browser session</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs text-slate-300">
                    <thead class="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                        <tr>
                            <th class="py-2.5 px-3">ID</th>
                            <th class="py-2.5 px-3">Title / Record</th>
                            <th class="py-2.5 px-3">Email</th>
                            <th class="py-2.5 px-3">Timestamp</th>
                            <th class="py-2.5 px-3 text-right">Status</th>
                        </tr>
                    </thead>
                    <tbody id="mock-table-body" class="divide-y divide-slate-800/60 font-mono">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Embedded In-Memory Mock Engine Script -->
    <script>
        // In-Memory Database Fixtures
        let mockDatabase = [
            {{ id: "REC-101", title: "Enterprise Inquiry — ACME Corp", email: "contact@acme.com", time: "10:24 AM", status: "Active" }},
            {{ id: "REC-102", title: "Partner Signup — Starlight Labs", email: "dev@starlight.io", time: "11:15 AM", status: "Verified" }}
        ];

        function renderMockTable() {{
            const tbody = document.getElementById("mock-table-body");
            const count = document.getElementById("mock-count");
            if (!tbody) return;
            tbody.innerHTML = "";
            count.textContent = mockDatabase.length;

            mockDatabase.forEach(item => {{
                const tr = document.createElement("tr");
                tr.className = "hover:bg-slate-800/40 transition";
                tr.innerHTML = `
                    <td class="py-2 px-3 text-indigo-400 font-bold">${{item.id}}</td>
                    <td class="py-2 px-3 text-slate-200">${{item.title}}</td>
                    <td class="py-2 px-3 text-slate-400">${{item.email}}</td>
                    <td class="py-2 px-3 text-slate-500">${{item.time}}</td>
                    <td class="py-2 px-3 text-right"><span class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-sans font-semibold">${{item.status}}</span></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function switchState(stateName) {{
            document.querySelectorAll(".state-btn").forEach(btn => {{
                btn.classList.remove("bg-indigo-600/30", "text-indigo-300", "font-semibold");
            }});
            const activeBtn = document.getElementById("btn-state-" + stateName);
            if (activeBtn) {{
                activeBtn.classList.add("bg-indigo-600/30", "text-indigo-300", "font-semibold");
            }}

            const bannerValidating = document.getElementById("state-banner-validating");
            const bannerSuccess = document.getElementById("state-banner-success");
            const bannerError = document.getElementById("state-banner-error");
            const btnSubmit = document.getElementById("btn-submit");
            const spinner = document.getElementById("btn-submit-spinner");
            const btnText = document.getElementById("btn-submit-text");

            // Hide all banners
            bannerValidating.classList.add("hidden");
            bannerSuccess.classList.add("hidden");
            bannerError.classList.add("hidden");
            btnSubmit.disabled = false;
            spinner.classList.add("hidden");
            btnText.textContent = "Submit Action";

            // Clear input validation outlines
            document.querySelectorAll("#prototype-form input, #prototype-form textarea").forEach(el => {{
                el.classList.remove("border-rose-500", "ring-2", "ring-rose-500/40");
            }});
            document.querySelectorAll("#prototype-form p[id$='-error']").forEach(p => p.classList.add("hidden"));

            if (stateName === "validating") {{
                bannerValidating.classList.remove("hidden");
                const firstInput = document.querySelector("#prototype-form input");
                if (firstInput) {{
                    firstInput.classList.add("border-rose-500", "ring-2", "ring-rose-500/40");
                    const errP = document.getElementById(firstInput.id + "-error");
                    if (errP) errP.classList.remove("hidden");
                }}
            }} else if (stateName === "submitting") {{
                btnSubmit.disabled = true;
                spinner.classList.remove("hidden");
                btnText.textContent = "Processing...";
            }} else if (stateName === "success") {{
                bannerSuccess.classList.remove("hidden");
            }} else if (stateName === "error") {{
                bannerError.classList.remove("hidden");
            }}
        }}

        function handleMockSubmit(event) {{
            event.preventDefault();
            switchState("submitting");

            setTimeout(() => {{
                const form = document.getElementById("prototype-form");
                const formData = new FormData(form);
                const titleVal = formData.get("title") || formData.get(form.elements[0]?.name) || "Custom Entry";
                const emailVal = formData.get("contact_email") || formData.get("email") || "user@mock.local";

                const newRec = {{
                    id: "REC-" + (100 + mockDatabase.length + 1),
                    title: String(titleVal),
                    email: String(emailVal),
                    time: new Date().toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}}),
                    status: "Submitted"
                }};
                mockDatabase.unshift(newRec);
                renderMockTable();
                switchState("success");
                form.reset();
            }}, 650);
        }}

        function resetPrototype() {{
            document.getElementById("prototype-form")?.reset();
            switchState("empty");
        }}

        document.addEventListener("DOMContentLoaded", renderMockTable);
    </script>
</body>
</html>"""

    async def generate_standalone_prototype(
        self,
        task_id: str,
        prompt_context: str,
        ui_spec: UIDesignSpec | None = None,
        workspace_dir: str | Path | None = None,
        feedback: str | None = None,
        project_id: str | None = None,
    ) -> UIPrototypeResult:
        """
        Generate a working, standalone Zero-to-One HTML/Tailwind CSS interactive prototype
        with an in-memory client-side mock engine and the 5 verified interactive states.
        """
        if workspace_dir is not None:
            ws_path = Path(workspace_dir)
        elif project_id:
            ws_path = Path("./workspace") / project_id
        else:
            ws_path = Path("./workspace") / task_id

        ws_path.mkdir(parents=True, exist_ok=True)
        print_agent("diba", f"Generating Zero-to-One working UI prototype for task: {task_id}")

        html_code = ""
        try:
            prompt = (
                f"Task ID: {task_id}\n"
                f"Prompt Context: {prompt_context}\n"
                f"Archetype: {getattr(ui_spec, 'archetype', 'linear_dark') if ui_spec else 'linear_dark'}\n"
                f"Layout: {ui_spec.component_layout if ui_spec else 'responsive single-column'}\n"
                f"Fields: {[f.id for f in ui_spec.form_fields] if ui_spec else []}\n"
                f"States: {ui_spec.states if ui_spec else ['empty', 'validating', 'submitting', 'success', 'error']}\n"
            )
            if feedback:
                prompt += f"\nDeveloper Feedback from Preview Gate:\n{feedback}\n"
            res = await self.prototype_agent.run(prompt)
            if hasattr(res, "output") and res.output:
                raw = str(res.output).strip()
            elif hasattr(res, "data") and res.data:
                raw = str(res.data).strip()
            else:
                raw = str(res).strip()

            # Handle possible string wrappers if output was serialized as literal representation
            if raw.startswith("AgentRunResult(output="):
                raw = raw.removeprefix("AgentRunResult(output=").removesuffix(")")
                if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
                    raw = raw[1:-1]
                raw = raw.encode().decode("unicode_escape", errors="ignore")

            if "```html" in raw:
                raw = raw.split("```html", 1)[1].split("```", 1)[0].strip()
            elif "```" in raw:
                raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
            if "<html" in raw.lower() and "</html>" in raw.lower():
                html_code = raw
        except Exception:
            html_code = ""

        if not html_code or "<html" not in html_code.lower():
            html_code = self._build_default_prototype_html(task_id, prompt_context, ui_spec, feedback)

        proto_file = ws_path / "prototype.html"
        proto_file.write_text(html_code, encoding="utf-8")

        form_file = ws_path / "form.html"
        form_file.write_text(html_code, encoding="utf-8")

        print_agent("diba", f"Saved working prototype to: {proto_file}")

        mock_fixtures = [
            {"id": "REC-101", "title": "Enterprise Inquiry — ACME Corp", "email": "contact@acme.com", "status": "Active"},
            {"id": "REC-102", "title": "Partner Signup — Starlight Labs", "email": "dev@starlight.io", "status": "Verified"},
        ]

        return UIPrototypeResult(
            task_id=task_id,
            project_id=project_id,
            prototype_path="prototype.html",
            preview_url="http://localhost:4173/prototype.html",
            mock_fixtures=mock_fixtures,
            state_handlers=["empty", "validating", "submitting", "success", "error"],
            html_content=html_code,
            feedback_history=[feedback] if feedback else [],
            approved=False,
        )


# Convenient alias
DibaDesignLead = DibaDesigner

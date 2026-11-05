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

from contracts import ClarificationOption, ClarificationQuestion, TechnicalSpec, UIDesignSpec, UIFieldSpec
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
                        chosen_key = q.selected_option or answers.get(q.id)
                        if chosen_key:
                            chosen_arch = get_archetype(str(chosen_key))
                            if chosen_arch and chosen_arch.key != current_ui.archetype:
                                current_ui.archetype = chosen_arch.key
                                current_ui.theme = chosen_arch.theme
                                current_ui.color_palette = dict(chosen_arch.color_palette)
                                current_ui.component_layout = chosen_arch.layout_wireframe
                                current_ui.states = dict(chosen_arch.state_styling)

                if not auto and has_non_default_answers(current_ui.clarification_questions, answers):
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

        markdown_content = f"""---
id: "spec-{task_id}-ui"
type: "ui-design-spec"
agent: "diba"
task_id: "{task_id}"
domain: "ui"
archetype: "{archetype_name}"
tags:
  - ui
  - ux
  - design
  - diba
{project.frontmatter}created_at: "{timestamp}"
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


# Convenient alias
DibaDesignLead = DibaDesigner

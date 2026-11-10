"""Unit tests for Diba (UI/UX & Product Design Lead) and Curated Design Archetypes."""

import json
from pathlib import Path
import pytest
from pydantic_ai.models.test import TestModel

from contracts import ClarificationOption, ClarificationQuestion, TechnicalSpec, UIDesignSpec, UIFieldSpec, DanaCritique
from agents.diba import DibaDesigner
from agents.dana import DanaQualitySupervisor
from tools.design_system import (
    ARCHETYPES,
    DEFAULT_ARCHETYPE,
    detect_recommended_archetype,
    format_archetype_grill_question,
    format_archetypes_for_prompt,
    get_archetype,
    list_archetypes,
)


def test_design_archetype_catalog():
    archetypes = list_archetypes()
    assert len(archetypes) >= 4
    keys = {a.key for a in archetypes}
    assert "linear_dark" in keys
    assert "bento_dashboard" in keys
    assert "stripe_enterprise" in keys
    assert "split_pane_workspace" in keys

    linear = get_archetype("linear_dark")
    assert linear.name == "Linear Dark Minimalist"
    assert "primary" in linear.color_palette
    assert "background" in linear.color_palette
    assert linear.surface_type == "web_form"


def test_detect_recommended_archetype():
    bento = detect_recommended_archetype("Build a real-time metrics dashboard for server analytics")
    assert bento.key == "bento_dashboard"

    stripe = detect_recommended_archetype("Enterprise customer billing portal and settings table")
    assert stripe.key == "stripe_enterprise"

    linear = detect_recommended_archetype("Fast command bar input tool with minimalist keyboard shortcuts")
    assert linear.key == "linear_dark"

    split = detect_recommended_archetype("Studio workspace editor with a left sidebar navigation")
    assert split.key == "split_pane_workspace"

    # Default fallback
    fallback = detect_recommended_archetype("Random unspecified software project")
    assert fallback.key == DEFAULT_ARCHETYPE.key


def test_format_archetype_grill_question():
    q = format_archetype_grill_question(recommended_key="bento_dashboard")
    assert isinstance(q, ClarificationQuestion)
    assert q.id == "ui_design_archetype"
    assert len(q.options) >= 4
    # Ensure recommended option is marked default
    bento_opt = next(o for o in q.options if o.key == "bento_dashboard")
    assert bento_opt.is_default is True
    assert "[Recommended]" in bento_opt.label


def test_diba_is_ui_task_detection():
    # Prompt keywords
    assert DibaDesigner.is_ui_task("Create a web form for collecting user signups") is True
    assert DibaDesigner.is_ui_task("Build an executive KPI dashboard with Tailwind") is True
    assert DibaDesigner.is_ui_task("Design a responsive page with interactive states") is True
    assert DibaDesigner.is_ui_task("Implement a modal dialog for transaction review") is True

    # Backend-only tasks
    assert DibaDesigner.is_ui_task("Migrate sqlite database tables and run validation") is False
    assert DibaDesigner.is_ui_task("Write a python script to parse csv logs") is False

    # Spec hints
    spec_with_ui = TechnicalSpec(
        task_id="task-1",
        architecture_overview="Overview",
        required_dependencies=[],
        phases=[],
        ui_spec=UIDesignSpec(surface_type="web_form", theme="dark", component_layout="Layout"),
    )
    assert DibaDesigner.is_ui_task("Something neutral", spec=spec_with_ui) is True


@pytest.mark.anyio
async def test_diba_designer_design_ui(tmp_path: Path):
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    output_data = dict(
        surface_type="dashboard",
        theme="bento_dark",
        archetype="bento_dashboard",
        component_layout="Executive Bento Grid with KPI tiles",
        form_fields=[],
        states={
            "empty": "No metrics available",
            "validating": "Validating input",
            "submitting": "Loading data...",
            "success": "Metrics synced",
            "error": "Failed to fetch metrics",
        },
        responsive_breakpoints="Single column on mobile, 3-column bento on desktop",
        clarification_questions=[],
    )
    test_model = TestModel(call_tools=[], custom_output_args=output_data)
    diba = DibaDesigner(vault_path=tmp_path, model_name=test_model, specs_dir=specs_dir)

    ui_spec = await diba.design_ui(
        task_id="task-test-ui",
        prompt_context="Create an executive metrics dashboard with live status cards",
        project_id="test-proj",
    )

    assert isinstance(ui_spec, UIDesignSpec)
    assert ui_spec.archetype == "bento_dashboard"
    # Archetype question was injected
    assert any(q.id == "ui_design_archetype" for q in ui_spec.clarification_questions)

    # Note was persisted
    note_file = specs_dir / "spec-task-test-ui-ui.md"
    assert note_file.exists()
    content = note_file.read_text(encoding="utf-8")
    assert 'agent: "diba"' in content
    assert "spec-task-test-ui-ui" in content
    assert "Design Archetype:" in content


@pytest.mark.anyio
async def test_diba_conduct_ui_review_auto(tmp_path: Path):
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    diba = DibaDesigner(vault_path=tmp_path, model_name=TestModel(), specs_dir=specs_dir)

    initial_ui = UIDesignSpec(
        surface_type="web_form",
        theme="linear_dark",
        archetype="linear_dark",
        component_layout="Initial layout",
        clarification_questions=[
            ClarificationQuestion(
                id="ui_design_archetype",
                category="ui",
                question="Choose archetype",
                options=[
                    ClarificationOption(key="linear_dark", label="Linear", is_default=True),
                    ClarificationOption(key="bento_dashboard", label="Bento", is_default=False),
                ],
            )
        ],
    )

    # In auto mode, default answer is accepted and approval gate proceeds
    final_ui, quit_requested = await diba.conduct_ui_review(
        initial_ui,
        task_id="task-review-test",
        prompt_context="Build a dashboard",
        auto=True,
    )

    assert quit_requested is False
    assert isinstance(final_ui, UIDesignSpec)


@pytest.mark.anyio
async def test_diba_conduct_ui_review_archetype_switch(tmp_path: Path):
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    diba = DibaDesigner(vault_path=tmp_path, model_name=TestModel(), specs_dir=specs_dir)

    initial_ui = UIDesignSpec(
        surface_type="web_form",
        theme="linear_dark",
        archetype="linear_dark",
        component_layout="Initial layout",
        clarification_questions=[
            ClarificationQuestion(
                id="ui_design_archetype",
                category="ui",
                question="Choose archetype",
                options=[
                    ClarificationOption(key="linear_dark", label="Linear", is_default=False),
                    ClarificationOption(key="bento_dashboard", label="Bento", is_default=True),
                ],
            )
        ],
    )

    # Mock user input choosing option 2 (bento)
    user_inputs = iter(["2", "y"])  # 2 selects bento, y approves gate
    def mock_input(prompt: str) -> str:
        return next(user_inputs, "")

    final_ui, quit_requested = await diba.conduct_ui_review(
        initial_ui,
        task_id="task-switch-test",
        prompt_context="Build a dashboard",
        auto=False,
        input_func=mock_input,
    )

    assert quit_requested is False
    # Verified that archetype changed to bento
    assert final_ui.archetype == "bento_dashboard"
    assert final_ui.theme == "bento_dark"
    assert final_ui.color_palette["primary"] == ARCHETYPES["bento_dashboard"].color_palette["primary"]


@pytest.mark.anyio
async def test_diba_conduct_ui_review_does_not_grill_twice_on_non_default(tmp_path: Path):
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    output_ui = dict(
        surface_type="web_form",
        theme="clean_light",
        archetype="stripe_enterprise",
        component_layout="Single card",
        form_fields=[],
        states={},
        responsive_breakpoints="Mobile",
        clarification_questions=[
            ClarificationQuestion(
                id="q1",
                question="Question 1",
                options=[
                    ClarificationOption(key="1", label="Default Option", is_default=True),
                    ClarificationOption(key="2", label="Non-Default Option", is_default=False),
                ],
            )
        ],
    )
    test_model = TestModel(call_tools=[], custom_output_args=output_ui)
    diba = DibaDesigner(vault_path=tmp_path, model_name=test_model, specs_dir=specs_dir)

    initial_ui = UIDesignSpec(
        surface_type="web_form",
        theme="linear_dark",
        archetype="linear_dark",
        component_layout="Initial layout",
        clarification_questions=[
            ClarificationQuestion(
                id="q1",
                question="Question 1",
                options=[
                    ClarificationOption(key="1", label="Default Option", is_default=True),
                    ClarificationOption(key="2", label="Non-Default Option", is_default=False),
                ],
            )
        ],
    )

    # Input "2" (non-default answer) then "y" (approve proposal card)
    # If the bug were present, it would re-grill and ask for a 3rd input, raising StopIteration!
    inputs = iter(["2", "y"])
    def mock_input(prompt: str) -> str:
        return next(inputs)

    final_ui, quit_requested = await diba.conduct_ui_review(
        initial_ui,
        task_id="task-no-double-grill",
        prompt_context="Build a form",
        auto=False,
        input_func=mock_input,
    )

    assert quit_requested is False
    assert isinstance(final_ui, UIDesignSpec)


def test_dana_conduct_intent_comparison_grill(tmp_path: Path):
    dana = DanaQualitySupervisor(vault_path=tmp_path, model_name=TestModel())

    critique = DanaCritique(
        lead="taghi",
        verdict="warn",
        summary="Spec omitted real-time search filtering requested by user.",
        risks_or_gaps=["No debounce search filter in table"],
        actionable_recommendations=["Add instant debounced search input to table"],
        score=65,
    )

    # User picks option 1 (Enforce requirement)
    user_inputs = iter(["1"])
    def mock_input(prompt: str) -> str:
        return next(user_inputs, "")

    steering, quit_req = dana.conduct_intent_comparison_grill(
        stage_name="taghi",
        original_prompt="Build a fast table with instant search",
        critique=critique,
        auto=False,
        input_func=mock_input,
    )

    assert quit_req is False
    assert steering is not None
    assert "Add instant debounced search input" in steering


def test_diba_detection_for_bistro_erp():
    # User's specific prompt that previously failed to awaken Diba
    assert DibaDesigner.is_ui_task("improve the design in bistro-erp") is True
    assert DibaDesigner.is_ui_task("redesign bistro-erp with modern aesthetics") is True
    assert DibaDesigner.is_ui_task("update styling and colors for the erp dashboard") is True


def test_print_model_lineup_card_includes_diba(capsys):
    from tools.ui import print_model_lineup_card
    models = {
        "natasha": "openai:gpt-4o-mini",
        "odin": "openai:gpt-4o-mini",
        "taghi": "openai:o3-mini",
        "diba": "openai:gpt-4o",
        "meti": "openai:gpt-4o",
    }
    print_model_lineup_card(models)
    out = capsys.readouterr().out
    assert "Diba" in out
    assert "Taghi" in out
    assert "Natasha" in out
    assert "Odin" in out
    assert "Meti" in out
    assert "openai:gpt-4o" in out


def test_task_brief_accepts_diba_target_lead():
    from contracts import TaskBrief
    brief = TaskBrief(
        task_id="task-ui-only",
        title="UI Redesign",
        objective="Modernize dashboard design",
        slug="ui-redesign",
        target_lead="diba",
        research_questions=[],
    )
    assert brief.target_lead == "diba"


@pytest.mark.anyio
async def test_taghi_does_not_write_ui_spec(tmp_path: Path):
    from agents.taghi import TaghiArchitect
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    spec_dict = dict(
        task_id="task-arch-only",
        architecture_overview="Clean architecture",
        required_dependencies=[],
        phases=[],
        ui_spec=dict(
            surface_type="web_form",
            theme="dark",
            component_layout="layout",
        ),
    )
    test_model = TestModel(call_tools=[], custom_output_args=spec_dict)
    taghi = TaghiArchitect(vault_path=tmp_path, model_name=test_model, specs_dir=specs_dir)
    spec = await taghi.create_specification(task_id="task-arch-only", research_summary="Research")

    assert spec.task_id == "task-arch-only"
    # Taghi writes spec-task-arch-only.md
    assert (specs_dir / "spec-task-arch-only.md").exists()
    # Taghi must NOT write spec-task-arch-only-ui.md (that is Diba's responsibility)
    assert not (specs_dir / "spec-task-arch-only-ui.md").exists()


@pytest.mark.anyio
async def test_diba_generate_standalone_prototype(tmp_path: Path):
    from contracts import UIPrototypeResult
    ws_dir = tmp_path / "workspace"
    ws_dir.mkdir(parents=True, exist_ok=True)

    diba = DibaDesigner(model_name=TestModel())
    res = await diba.generate_standalone_prototype(
        task_id="task-proto-1",
        prompt_context="Build a billing portal with Stripe card input",
        project_id="test-proto-proj",
        workspace_dir=ws_dir / "test-proto-proj",
    )
    assert isinstance(res, UIPrototypeResult)
    assert res.task_id == "task-proto-1"
    assert res.project_id == "test-proto-proj"
    assert "prototype.html" in res.prototype_path
    assert len(res.state_handlers) == 5
    assert (ws_dir / "test-proto-proj" / "prototype.html").is_file()
    assert (ws_dir / "test-proto-proj" / "form.html").is_file()

    content = (ws_dir / "test-proto-proj" / "prototype.html").read_text()
    assert "mockDatabase" in content
    assert "switchState" in content



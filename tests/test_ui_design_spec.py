"""Automated tests for Dual-Specification Architecture & UI/UX Design System."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from contracts import (
    ClarificationOption,
    ClarificationQuestion,
    ExecutionPhase,
    TechnicalSpec,
    UIDesignSpec,
    UIFieldSpec,
)
from agents.taghi import TaghiArchitect
from agents.meti import MetiImplementer
from tools.ui import print_spec_proposal_card, print_ui_spec_proposal_card


def test_ui_design_spec_contract():
    field1 = UIFieldSpec(
        id="email",
        label="Customer Email",
        input_type="email",
        placeholder="alex@example.com",
        required=True,
        validation_rules="Must be a valid email format",
    )
    field2 = UIFieldSpec(
        id="amount",
        label="Invoice Amount",
        input_type="number",
        placeholder="100.00",
        required=True,
        validation_rules="Must be positive numeric value",
    )

    ui_spec = UIDesignSpec(
        surface_type="web_form",
        theme="modern_dark",
        color_palette={"primary": "#10b981", "background": "#0f172a"},
        component_layout="Header with logo -> Centered input card -> Submit button -> Toast container",
        form_fields=[field1, field2],
        states={
            "empty": "Initial blank form with placeholders",
            "submitting": "Button spinner active, inputs disabled",
            "success": "Green toast notification displayed",
        },
    )

    spec = TechnicalSpec(
        task_id="task-test-ui-101",
        architecture_overview="Full-stack invoicing pipeline with dual backend and UI specs.",
        required_dependencies=["pydantic", "rich"],
        phases=[
            ExecutionPhase(phase_name="1-backend", instructions="Build API", validation_command="pytest tests/"),
            ExecutionPhase(phase_name="2-ui-surface", instructions="Build form.html", validation_command="test -f form.html"),
        ],
        ui_spec=ui_spec,
    )

    assert spec.ui_spec is not None
    assert spec.ui_spec.surface_type == "web_form"
    assert len(spec.ui_spec.form_fields) == 2
    assert spec.ui_spec.form_fields[0].id == "email"
    assert spec.ui_spec.states["submitting"] == "Button spinner active, inputs disabled"


def test_taghi_dual_spec_vault_persistence(tmp_path):
    async def _run():
        from agents.diba import DibaDesigner
        from pydantic_ai.models.test import TestModel

        vault_dir = tmp_path / "vault"
        specs_dir = vault_dir / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        taghi = TaghiArchitect(vault_path=vault_dir, specs_dir=specs_dir, model_name="test")

        mock_spec = TechnicalSpec(
            task_id="task-dual-spec-01",
            architecture_overview="Invoicing backend architecture",
            required_dependencies=["fastapi"],
            phases=[
                ExecutionPhase(phase_name="1-backend", instructions="Write models", validation_command="pytest"),
                ExecutionPhase(phase_name="2-ui", instructions="Write form.html", validation_command="test -f form.html"),
            ],
        )

        # Mock agent run for Taghi
        mock_run = AsyncMock()
        mock_run.return_value = MagicMock(output=mock_spec, usage=lambda: None)
        taghi.agent.run = mock_run

        res = await taghi.create_specification("task-dual-spec-01", "Research: Invoice pipeline")

        # Diba designs and writes the UI specification
        output_ui = dict(
            surface_type="web_form",
            theme="clean_light",
            archetype="linear_dark",
            component_layout="Centered card layout with input fields and submit button",
            form_fields=[
                dict(id="client", label="Client Name", input_type="text", required=True),
            ],
            states={
                "empty": "Empty form",
                "validating": "Highlight missing required fields",
                "submitting": "Spinner active",
                "success": "Success confirmation alert",
                "error": "Error alert banner",
            },
            responsive_breakpoints="Mobile-first",
            clarification_questions=[],
        )
        test_model = TestModel(call_tools=[], custom_output_args=output_ui)
        diba = DibaDesigner(vault_path=vault_dir, specs_dir=specs_dir, model_name=test_model)
        await diba.design_ui("task-dual-spec-01", "Create an invoice form", spec=res)

        # Verify both notes were written to vault
        backend_note = specs_dir / "spec-task-dual-spec-01.md"
        ui_note = specs_dir / "spec-task-dual-spec-01-ui.md"

        assert backend_note.is_file()
        assert ui_note.is_file()

        backend_text = backend_note.read_text(encoding="utf-8")
        assert "Invoicing backend architecture" in backend_text
        assert "spec-task-dual-spec-01" in backend_text

        ui_text = ui_note.read_text(encoding="utf-8")
        assert "# UI/UX Design Specification: task-dual-spec-01" in ui_text
        assert "clean_light" in ui_text
        assert "Client Name" in ui_text
        assert "Success confirmation alert" in ui_text
        assert 'agent: "diba"' in ui_text

    asyncio.run(_run())


def test_ui_spec_proposal_card_rendering():
    ui_spec = UIDesignSpec(
        surface_type="web_form",
        theme="modern_dark",
        color_palette={"primary": "#10b981", "background": "#0f172a"},
        component_layout="Two-column responsive card layout with live summary",
        form_fields=[
            UIFieldSpec(id="name", label="Full Name", input_type="text", required=True),
        ],
    )
    # Ensure it renders without exception
    print_ui_spec_proposal_card(ui_spec)

    spec = TechnicalSpec(
        task_id="task-card-test",
        architecture_overview="System architecture",
        required_dependencies=[],
        phases=[],
        ui_spec=ui_spec,
    )
    print_spec_proposal_card(spec)


def test_taghi_conducts_ui_grill_session(tmp_path):
    async def _run():
        vault_dir = tmp_path / "vault"
        specs_dir = vault_dir / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        taghi = TaghiArchitect(vault_path=vault_dir, specs_dir=specs_dir, model_name="test")

        ui_question = ClarificationQuestion(
            id="theme_choice",
            question="UI Color Theme",
            options=[
                ClarificationOption(key="1", label="Modern Dark Mode", is_default=True),
                ClarificationOption(key="2", label="Clean SaaS Light"),
            ],
        )
        ui_spec = UIDesignSpec(
            surface_type="web_form",
            component_layout="Form layout",
            clarification_questions=[ui_question],
        )
        spec = TechnicalSpec(
            task_id="task-grill-ui",
            architecture_overview="Architecture",
            required_dependencies=[],
            phases=[ExecutionPhase(phase_name="1-test", instructions="Run", validation_command="true")],
            ui_spec=ui_spec,
        )

        # In auto mode, default options are accepted and confirmed
        reviewed_spec, quit_requested = await taghi.conduct_architectural_review(
            spec=spec,
            task_id="task-grill-ui",
            design_context="Design context",
            auto=True,
        )

        assert not quit_requested
        assert reviewed_spec.task_id == "task-grill-ui"

    asyncio.run(_run())


def test_meti_receives_ui_spec_in_prompt(tmp_path):
    async def _run():
        meti = MetiImplementer(
            vault_path=tmp_path / "vault",
            workspace_path=tmp_path / "workspace",
            model_name="test",
            sandbox=MagicMock(execute_code=MagicMock(return_value={"output": "", "exit_code": 0, "timed_out": False})),
        )

        ui_spec = UIDesignSpec(
            surface_type="web_form",
            theme="modern_dark",
            color_palette={"primary": "#3b82f6", "surface": "#1e293b"},
            component_layout="Responsive card layout with live preview",
            form_fields=[
                UIFieldSpec(id="amount", label="Invoice Amount", input_type="number", required=True),
            ],
        )

        captured_prompts = []

        async def mock_run(prompt, **kwargs):
            captured_prompts.append(prompt)
            from contracts import ImplementationResult
            return MagicMock(
                output=ImplementationResult(task_id="task-ui-meti", status="success", summary="Done", executed_phases=["1-backend"]),
                usage=lambda: None,
            )

        meti.agent.run = mock_run

        phases = [
            ExecutionPhase(phase_name="1-backend", instructions="Write models", validation_command="echo 'ok'"),
        ]

        await meti.execute_specification(
            task_id="task-ui-meti",
            spec_overview="Backend overview",
            phases=phases,
            ui_spec=ui_spec,
        )

        assert len(captured_prompts) > 0
        prompt_text = captured_prompts[0]
        assert "UI/UX Design Specification:" in prompt_text
        assert "modern_dark" in prompt_text
        assert "Invoice Amount (number)" in prompt_text
        assert "Tailwind CSS CDN" in prompt_text

    asyncio.run(_run())

from __future__ import annotations

import os
import sys
import argparse
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_ai.models import Model
from tools.chatgpt_auth import get_chatgpt_model
from tools.model_tiers import resolve_pipeline_models
from tools.project_notes import validate_project_id
from tools.task_ledger import TaskLedger, TaskRecord, validate_task_id
from contracts import (
    __version__,
    ExecutionPhase,
    ImplementationCheckpoint,
    ImplementationResult,
    ResearchReport,
    TaskBrief,
    TechnicalSpec,
    UIDesignSpec,
    format_design_context,
)
from agents.natasha import NatashaRouter
from agents.odin import OdinResearcher
from agents.taghi import TaghiArchitect
from agents.meti import MetiImplementer
from tools.ui import (
    print_agent,
    print_brief_summary,
    print_completion,
    print_how_to_run,
    print_model_lineup_card,
    print_phase_table,
    print_spec_summary,
    print_task_header,
    print_token_summary_table,
    print_workspace_tree,
    prompt_alignment_gate,
    prompt_delivery_gate,
    prompt_model_approval_gate,
    prompt_step_gate,
)

load_dotenv()


def slugify_task_prompt(prompt: str, max_words: int = 4, max_chars: int = 32) -> str:
    """Extract a concise, semantic kebab-case slug from a user prompt."""
    stop_words = {
        # Articles & prepositions
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
        "by", "of", "from", "into", "onto", "as", "about", "between", "through",
        # Pronouns & demonstratives
        "i", "me", "my", "we", "us", "our", "you", "your", "he", "she", "it", "they", "them",
        "this", "that", "these", "those", "which", "who", "whom", "whose", "what", "where", "when", "why", "how",
        # Auxiliary & modal verbs
        "be", "is", "am", "are", "was", "were", "been", "being",
        "have", "has", "had", "having", "do", "does", "did", "doing",
        "can", "could", "shall", "should", "will", "would", "may", "might", "must",
        # Contraction stems
        "t", "s", "d", "ll", "ve", "re", "m",
        "don", "doesn", "didn", "isn", "aren", "won",
        # Generic request verbs & filler words
        "build", "create", "make", "write", "implement", "develop", "generate",
        "add", "please", "want", "need", "like", "just", "also", "simple",
        "complete", "tool", "app", "project",
        "get", "gets", "got", "getting", "let", "lets", "using", "uses", "used", "use",
        "some", "any", "all", "each", "every", "other", "another", "such", "than", "then", "so",
    }
    cleaned = re.sub(r"'\w+", "", prompt.lower())
    words = re.findall(r"[a-z0-9]+", cleaned)
    meaningful = [w for w in words if w not in stop_words and (len(w) >= 3 or w.isdigit())]
    selected = meaningful[:max_words] if meaningful else [w for w in words if len(w) >= 2][:max_words]
    slug = "-".join(selected)
    if len(slug) > max_chars:
        trimmed = slug[:max_chars].rsplit("-", 1)[0]
        slug = trimmed if trimmed else slug[:max_chars]
    return slug or "task"


def task_id_for(prompt: str, ledger: TaskLedger | None = None) -> str:
    slug = slugify_task_prompt(prompt)
    base_id = f'task-{slug}-{datetime.now():%Y%m%d}'
    if ledger is None:
        return base_id
    task_id = base_id
    counter = 1
    while True:
        try:
            ledger.load(task_id)
            counter += 1
            task_id = f'{base_id}-{counter}'
        except ValueError:
            return task_id


def fast_track_spec(
    task_id: str,
    objective: str,
    base_image: str | None = None,
    project_id: str | None = None,
) -> TechnicalSpec:
    workspace_dir = project_id or task_id
    command = f'sh /app/workspace/{workspace_dir}/validate-{task_id}.sh'
    image = base_image
    if image is None and any(kw in objective.lower() for kw in ('python', 'pytest', 'pip', 'fastapi', 'flask', 'django', 'pandas', 'numpy')):
        image = 'python:3.11-slim'
    ui_spec = None
    if any(kw in objective.lower() for kw in ('web', 'browser', 'html', 'form', 'ui', 'dashboard', 'frontend', 'app', 'portal', 'screen')):
        ui_spec = UIDesignSpec(
            surface_type='dashboard' if any(kw in objective.lower() for kw in ('dashboard', 'app', 'erp', 'portal')) else 'web_form',
            theme='clean_light',
            color_palette={
                'primary': '#0f766e',
                'background': '#f8fafc',
                'surface': '#ffffff',
                'text': '#0f172a',
                'border': '#e2e8f0',
                'success': '#10b981',
                'error': '#ef4444',
            },
            component_layout='Sticky header with brand title & navigation tabs; main container with rounded-xl bordered cards, clean data tables with status badges, and interactive form modals with focus rings.',
            states={
                'empty': 'Centered empty state with icon, friendly guidance, and primary action button.',
                'validating': 'Inline red helper text and border highlights on invalid field inputs.',
                'submitting': 'Disabled submit button with spinning loader indicator to prevent double-clicks.',
                'success': 'Dismissible green alert banner confirming data saved successfully.',
                'error': 'Dismissible red alert banner displaying actionable error details.',
            },
            responsive_breakpoints='Mobile-first single column below 640px; multi-column responsive grid on tablet and desktop (>=768px).'
        )
    return TechnicalSpec(
        task_id=task_id, architecture_overview=objective, required_dependencies=[],
        base_image=image,
        ui_spec=ui_spec,
        phases=[ExecutionPhase(
            phase_name='1-fast-track',
            instructions=(f'{objective}\n\nCreate your project directory at workspace/{workspace_dir}/ and place all modules there. '
                          f'Create validate-{task_id}.sh in /app/workspace/{workspace_dir}/ with task-specific tests or checks. '
                          'The script must exercise the implemented behavior and exit nonzero on failure. '
                          'A completion message alone is not validation.'),
            validation_command=command,
        )],
    )


async def run_task(
    record: TaskRecord,
    ledger: TaskLedger,
    model_override: str | None = None,
    image_override: str | None = None,
    auto: bool = False,
    step: bool = False,
    tier: str | None = None,
    lead_overrides: dict[str, Any] | None = None,
    research_only: bool = False,
    supervise: str = "off",
) -> ImplementationResult:
    # Reject unreadable stage checkpoints before authentication or external work.
    if record.brief is not None:
        TaskBrief.model_validate(record.brief)
    if record.research is not None:
        ResearchReport.model_validate(record.research)
    if record.specification is not None:
        TechnicalSpec.model_validate(record.specification)
    checkpoint = record.implementation
    if isinstance(checkpoint, dict):
        checkpoint = ImplementationCheckpoint.model_validate(checkpoint)
    implementation_started = checkpoint.is_started()
    workspace_dir = record.project_id or record.task_id
    if implementation_started and not (Path('workspace') / workspace_dir).is_dir():
        raise ValueError('The saved project workspace is missing; restore it before resuming implementation')
    if checkpoint.in_flight_command:
        print_agent('resume', 'Interrupted command outcome is unknown: ' + checkpoint.in_flight_command)
        print_agent('resume', 'Inspect its side effects; the unfinished phase may execute again.')

    # Resolve tiered pipeline models
    pipeline_models = resolve_pipeline_models(
        global_model=model_override,
        tier=tier,
        overrides=lead_overrides,
    )

    # Confirm the per-lead lineup before each active run, including resumed tasks.
    if not auto:
        gate_action, updated_models = prompt_model_approval_gate(
            pipeline_models, tier=tier or "balanced", auto=auto
        )
        if gate_action == "quit":
            print_agent("orchestrator", "Task execution cancelled by user at model approval gate.")
            sys.exit(0)
        if updated_models:
            pipeline_models = updated_models

    model_cache: dict[str, Any] = {}

    async def resolve_agent_model(model_spec: Any) -> Any:
        if isinstance(model_spec, Model) or not isinstance(model_spec, str):
            return model_spec
        if model_spec not in model_cache:
            model_cache[model_spec] = await get_chatgpt_model(model_name=model_spec)
        return model_cache[model_spec]

    dana_instance = None
    if supervise in ("advisory", "autonomous"):
        from agents.dana import DanaQualitySupervisor
        dana_model = await resolve_agent_model(pipeline_models.get("dana", pipeline_models["taghi"]))
        dana_instance = DanaQualitySupervisor(model_name=dana_model)

    project = record.project_id
    task_id = record.task_id
    record.run_number += 1
    record.error = None
    ledger.save(record)

    if record.brief is None:
        record.status = 'PENDING'
        ledger.save(record)
        natasha_model = await resolve_agent_model(pipeline_models["natasha"])
        router = NatashaRouter(model_name=natasha_model)
        brief = await router.coordinate_request(record.prompt, task_id, project_id=project)
        if not auto and sys.stdin.isatty() and getattr(brief, "clarification_questions", None):
            review_fn = getattr(router, "conduct_grill_session", None)
            if asyncio.iscoroutinefunction(review_fn):
                brief, quit_requested = await review_fn(brief, auto=auto, project_id=project)
                if quit_requested:
                    print_agent("orchestrator", "Task execution cancelled by user during Natasha grill.")
                    sys.exit(0)
        record.brief = brief
        if getattr(brief, "token_usage", None):
            brief.token_usage["model"] = str(pipeline_models["natasha"])
            record.token_usage["natasha"] = brief.token_usage
        ledger.save(record)
    brief = TaskBrief.model_validate(record.brief)

    # Dana Supervision of Natasha's Intent Brief
    if dana_instance and not implementation_started:
        dana_critique = await dana_instance.supervise_stage(
            "natasha",
            deliverable=brief,
            prompt_context=record.prompt,
            task_id=task_id,
            project_id=project,
        )
        if getattr(dana_critique, "token_usage", None):
            dana_critique.token_usage["model"] = str(pipeline_models.get("dana", pipeline_models["taghi"]))
            record.token_usage["dana_natasha"] = dana_critique.token_usage
            ledger.save(record)

        if supervise == "advisory" and not auto:
            from tools.ui import prompt_dana_gate
            gate_action, feedback = prompt_dana_gate(dana_critique, auto=auto)
            if gate_action == "quit":
                print_agent("orchestrator", "Task execution cancelled by user at Dana supervision gate.")
                sys.exit(0)
            elif gate_action == "apply" and feedback:
                natasha_model = await resolve_agent_model(pipeline_models["natasha"])
                brief = await NatashaRouter(model_name=natasha_model).realign_intent(brief, feedback, project_id=project)
                record.prompt = f"{record.prompt} (Supervisor steering: {feedback})"
                record.brief = brief
                ledger.save(record)
        elif supervise == "autonomous":
            if dana_critique.verdict in ("warn", "block") and dana_critique.actionable_recommendations:
                rec_summary = "; ".join(dana_critique.actionable_recommendations)
                print_agent("dana", f"[bold yellow]Autonomous Steering:[/bold yellow] Realigning Natasha brief: {rec_summary}")
                natasha_model = await resolve_agent_model(pipeline_models["natasha"])
                brief = await NatashaRouter(model_name=natasha_model).realign_intent(brief, rec_summary, project_id=project)
                record.prompt = f"{record.prompt} (Supervisor steering: {rec_summary})"
                record.brief = brief
                ledger.save(record)

    # Alignment gate: 5-sentence brief and intent confirmation
    if not implementation_started and not auto:
        while True:
            action, feedback, _ = prompt_alignment_gate(brief, auto=auto)
            if action == "quit":
                print_agent("orchestrator", "Task execution cancelled by user.")
                sys.exit(0)
            elif action == "edit" and feedback:
                natasha_model = await resolve_agent_model(pipeline_models["natasha"])
                brief = await NatashaRouter(model_name=natasha_model).realign_intent(brief, feedback, project_id=project)
                record.prompt = f"{record.prompt} (Clarification: {feedback})"
                record.brief = brief
                if getattr(brief, "token_usage", None):
                    brief.token_usage["model"] = str(pipeline_models["natasha"])
                    record.token_usage["natasha"] = brief.token_usage
                ledger.save(record)
            else:
                break

    print_brief_summary(
        brief.target_lead,
        brief.research_questions,
        token_usage=getattr(brief, "token_usage", None),
        model=str(pipeline_models["natasha"]),
    )
    objective = brief.objective
    if brief.research_questions:
        objective += '\n\nScope and questions:\n' + '\n'.join(f'- {item}' for item in brief.research_questions)

    if record.specification is None:
        if step:
            gate_action, gate_feedback = prompt_step_gate(
                brief.target_lead,
                f"Next Lead: {brief.target_lead.upper()} will proceed with "
                f"{'deep research' if brief.target_lead == 'odin' else 'architecture design'}.\n"
                f"Goal: {brief.title}\n"
                f"Objective: {objective[:180]}...",
                auto=auto,
            )
            if gate_action == "quit":
                print_agent("orchestrator", "Task execution cancelled by user.")
                sys.exit(0)
            elif gate_action == "pivot" and gate_feedback:
                brief = await NatashaRouter(model_name=natasha_model).realign_intent(brief, gate_feedback, project_id=project)
                record.prompt = f"{record.prompt} (Clarification: {gate_feedback})"
                record.brief = brief
                record.specification = None
                ledger.save(record)

        if brief.target_lead == 'odin':
            if record.research is None:
                record.status = 'RESEARCHING'
                ledger.save(record)
                odin_model = await resolve_agent_model(pipeline_models["odin"])
                research = await OdinResearcher(model_name=odin_model).conduct_research(task_id, objective, project_id=project)
                record.research = research
                if getattr(research, "token_usage", None):
                    research.token_usage["model"] = str(pipeline_models["odin"])
                    record.token_usage["odin"] = research.token_usage
                ledger.save(record)
            research = ResearchReport.model_validate(record.research)

            # Dana Supervision of Odin's Research Report
            if dana_instance:
                dana_critique = await dana_instance.supervise_stage(
                    "odin",
                    deliverable=research,
                    prompt_context=objective,
                    task_id=task_id,
                    project_id=project,
                )
                if getattr(dana_critique, "token_usage", None):
                    dana_critique.token_usage["model"] = str(pipeline_models.get("dana", pipeline_models["taghi"]))
                    record.token_usage["dana_odin"] = dana_critique.token_usage
                    ledger.save(record)

                if supervise == "advisory" and not auto:
                    from tools.ui import prompt_dana_gate
                    gate_action, feedback = prompt_dana_gate(dana_critique, auto=auto)
                    if gate_action == "quit":
                        print_agent("orchestrator", "Task execution cancelled by user at Dana supervision gate.")
                        sys.exit(0)
                    elif gate_action == "apply" and feedback:
                        objective = f"{objective}\n\nSupervisor Research Recommendations:\n{feedback}"
                elif supervise == "autonomous":
                    if dana_critique.verdict in ("warn", "block") and dana_critique.actionable_recommendations:
                        rec_summary = "; ".join(dana_critique.actionable_recommendations)
                        print_agent("dana", f"[bold yellow]Autonomous Steering:[/bold yellow] Injecting research guidance into design context: {rec_summary}")
                        objective = f"{objective}\n\nSupervisor Research Recommendations:\n{rec_summary}"

            # Early completion for research-only tasks
            is_research_only = (
                research_only
                or any(kw in objective.lower() or kw in record.prompt.lower() for kw in [
                    'just research', 'research-only', 'research only', 'no software implementation', 'just reseach'
                ])
            )
            if is_research_only:
                record.status = 'COMPLETED'
                ledger.save(record)
                print_completion(task_id, True, f"Research report completed successfully.\n\nSummary: {research.summary}")
                print_token_summary_table(record.token_usage, default_model=model_override)
                return ImplementationResult(
                    task_id=task_id,
                    project_id=project,
                    status="success",
                    summary=f"Research complete: {research.summary[:140]}",
                    executed_phases=[],
                )

            design_context = format_design_context(objective, research, alignment_brief=brief.alignment_brief)
        else:
            design_context = format_design_context(objective, None, alignment_brief=brief.alignment_brief)
        if brief.target_lead in ('odin', 'taghi'):
            record.status = 'ARCHITECTING'
            ledger.save(record)
            taghi_model = await resolve_agent_model(pipeline_models["taghi"])
            architect = TaghiArchitect(model_name=taghi_model)
            spec = await architect.create_specification(task_id, design_context, project_id=project)
            if not auto and sys.stdin.isatty():
                review_fn = getattr(architect, "conduct_architectural_review", None)
                if asyncio.iscoroutinefunction(review_fn):
                    spec, quit_requested = await review_fn(
                        spec, task_id, design_context, auto=auto, project_id=project
                    )
                    if quit_requested:
                        print_agent("orchestrator", "Task execution cancelled by user during Taghi architectural review.")
                        sys.exit(0)
            if getattr(spec, "token_usage", None):
                spec.token_usage["model"] = str(pipeline_models["taghi"])
                record.token_usage["taghi"] = spec.token_usage
        else:
            spec = fast_track_spec(task_id, objective, base_image=image_override, project_id=project)
        if image_override:
            spec.base_image = image_override
        spec.project_id = project
        record.specification = spec
        ledger.save(record)

    spec = TechnicalSpec.model_validate(record.specification)

    # Dana Supervision of Taghi's Architectural Specification
    if dana_instance and not implementation_started:
        dana_critique = await dana_instance.supervise_stage(
            "taghi",
            deliverable=spec,
            prompt_context=design_context if 'design_context' in locals() else brief.objective,
            task_id=task_id,
            project_id=project,
        )
        if getattr(dana_critique, "token_usage", None):
            dana_critique.token_usage["model"] = str(pipeline_models.get("dana", pipeline_models["taghi"]))
            record.token_usage["dana_taghi"] = dana_critique.token_usage
            ledger.save(record)

        if supervise == "advisory" and not auto:
            from tools.ui import prompt_dana_gate
            gate_action, feedback = prompt_dana_gate(dana_critique, auto=auto)
            if gate_action == "quit":
                print_agent("orchestrator", "Task execution cancelled by user at Dana supervision gate.")
                sys.exit(0)
            elif gate_action == "apply" and feedback:
                taghi_model = await resolve_agent_model(pipeline_models["taghi"])
                revised_context = f"{format_design_context(brief.objective, None, alignment_brief=brief.alignment_brief)}\n\nSupervisor Architectural Revisions Required:\n{feedback}"
                spec = await TaghiArchitect(model_name=taghi_model).create_specification(
                    task_id, revised_context, project_id=project
                )
                record.specification = spec
                ledger.save(record)
        elif supervise == "autonomous":
            if dana_critique.verdict in ("warn", "block") and dana_critique.actionable_recommendations:
                rec_summary = "; ".join(dana_critique.actionable_recommendations)
                print_agent("dana", f"[bold yellow]Autonomous Steering:[/bold yellow] Requesting Taghi specification revision: {rec_summary}")
                taghi_model = await resolve_agent_model(pipeline_models["taghi"])
                revised_context = f"{format_design_context(brief.objective, None, alignment_brief=brief.alignment_brief)}\n\nSupervisor Architectural Revisions Required:\n{rec_summary}"
                spec = await TaghiArchitect(model_name=taghi_model).create_specification(
                    task_id, revised_context, project_id=project
                )
                record.specification = spec
                ledger.save(record)
    print_spec_summary(
        spec.base_image,
        spec.phases,
        token_usage=getattr(spec, "token_usage", None),
        model=str(pipeline_models["taghi"]),
    )
    print_phase_table(spec.phases, completed_phases=getattr(checkpoint, "validated_phases", []))

    if step:
        gate_action, gate_feedback = prompt_step_gate(
            "meti",
            f"Technical Specification ready with {len(spec.phases)} phases.\n"
            f"Runtime Base Image: {spec.base_image}\n"
            "Ready to execute container implementation?",
            auto=auto,
        )
        if gate_action == "quit":
            print_agent("orchestrator", "Task execution cancelled by user.")
            sys.exit(0)
        elif gate_action == "pivot" and gate_feedback:
            brief = await NatashaRouter(model_name=natasha_model).realign_intent(brief, gate_feedback, project_id=project)
            record.prompt = f"{record.prompt} (Clarification: {gate_feedback})"
            record.brief = brief
            record.specification = None
            record.implementation = ImplementationCheckpoint()
            ledger.save(record)
            # Re-generate specification
            taghi_model = await resolve_agent_model(pipeline_models["taghi"])
            spec = await TaghiArchitect(model_name=taghi_model).create_specification(
                task_id, format_design_context(brief.objective, None, alignment_brief=brief.alignment_brief), project_id=project
            )
            record.specification = spec
            ledger.save(record)

    record.status = 'IMPLEMENTING'
    ledger.save(record)

    def save_implementation(state: ImplementationCheckpoint | dict) -> None:
        record.implementation = state
        ledger.save(record)

    effective_image = image_override or spec.base_image
    meti_model = await resolve_agent_model(pipeline_models["meti"])
    impl_res = await MetiImplementer(model_name=meti_model).execute_specification(
        task_id, spec.architecture_overview, spec.phases,
        required_dependencies=spec.required_dependencies, project_id=project,
        checkpoint=checkpoint, checkpoint_callback=save_implementation, run_number=record.run_number,
        base_image=effective_image,
        ui_spec=getattr(spec, "ui_spec", None),
    )
    if getattr(impl_res, "token_usage", None):
        impl_res.token_usage["model"] = str(pipeline_models["meti"])
        record.token_usage["meti"] = impl_res.token_usage
        ledger.save(record)

    # Dana Supervision of Meti Deliverable
    if dana_instance and impl_res.status == 'success':
        dana_critique = await dana_instance.supervise_stage(
            "meti",
            deliverable=impl_res,
            prompt_context=spec.architecture_overview,
            task_id=task_id,
            project_id=project,
        )
        if getattr(dana_critique, "token_usage", None):
            dana_critique.token_usage["model"] = str(pipeline_models.get("dana", pipeline_models["taghi"]))
            record.token_usage["dana_meti"] = dana_critique.token_usage
            ledger.save(record)

        if supervise == "advisory" and not auto:
            from tools.ui import prompt_dana_gate
            gate_action, feedback = prompt_dana_gate(dana_critique, auto=auto)
            if gate_action == "quit":
                print_agent("orchestrator", "Task execution terminated at Dana delivery review.")
                sys.exit(0)
            elif gate_action == "apply" and feedback:
                impl_res = await MetiImplementer(model_name=meti_model).refine_deliverable(
                    task_id,
                    feedback,
                    spec.phases,
                    project_id=project,
                    base_image=effective_image,
                )
                if getattr(impl_res, "token_usage", None):
                    impl_res.token_usage["model"] = str(pipeline_models["meti"])
                    record.token_usage["meti"] = impl_res.token_usage
                    ledger.save(record)
        elif supervise == "autonomous":
            if dana_critique.verdict in ("warn", "block") and dana_critique.actionable_recommendations:
                rec_summary = "; ".join(dana_critique.actionable_recommendations)
                print_agent("dana", f"[bold yellow]Autonomous Steering:[/bold yellow] Requesting Meti refinement: {rec_summary}")
                impl_res = await MetiImplementer(model_name=meti_model).refine_deliverable(
                    task_id,
                    rec_summary,
                    spec.phases,
                    project_id=project,
                    base_image=effective_image,
                )
                if getattr(impl_res, "token_usage", None):
                    impl_res.token_usage["model"] = str(pipeline_models["meti"])
                    record.token_usage["meti"] = impl_res.token_usage
                    ledger.save(record)

    # Automated deliverable evaluation & scoring
    if impl_res.status == 'success':
        workspace_dir = project or task_id
        workspace_path = Path("workspace") / workspace_dir
        if workspace_path.is_dir():
            from tools.eval_harness import DeliverableEvaluator
            from tools.ui import print_evaluation_scorecard
            evaluator = DeliverableEvaluator(workspace_path, spec=spec, project_id=project, task_id=task_id)
            report = evaluator.evaluate()
            evaluator.save_report(report)
            if not auto:
                print_evaluation_scorecard(report)

    # Post-implementation delivery confirmation gate & refinement loop
    if impl_res.status == 'success' and not auto:
        workspace_dir = project or task_id
        workspace_path = Path("workspace") / workspace_dir
        while True:
            gate_action, gate_feedback = prompt_delivery_gate(
                task_id,
                workspace_path,
                impl_res.summary,
                auto=auto,
            )
            if gate_action == "quit":
                print_agent("orchestrator", "Task execution terminated at delivery gate.")
                sys.exit(0)
            elif gate_action == "refine" and gate_feedback:
                impl_res = await MetiImplementer(model_name=meti_model).refine_deliverable(
                    task_id,
                    gate_feedback,
                    spec.phases,
                    project_id=project,
                    base_image=effective_image,
                )
                if getattr(impl_res, "token_usage", None):
                    impl_res.token_usage["model"] = str(pipeline_models["meti"])
                    record.token_usage["meti"] = impl_res.token_usage
                    ledger.save(record)
            else:
                break

    if project:
        from tools.project_notes import update_project_profile
        try:
            update_project_profile(project, task_id, brief=brief, spec=spec, result=impl_res)
        except Exception:
            pass

    return impl_res


async def main() -> None:
    parser = argparse.ArgumentParser(
        prog='buildrelay',
        description='BuildRelay: plan, build, check, and resume AI development tasks',
    )
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('prompt', nargs='?', help='Task description or prompt')
    parser.add_argument('--config', action='store_true', help='Launch interactive onboarding & configuration wizard')
    parser.add_argument('--session', nargs='?', const='', help='Launch interactive REPL project session')
    parser.add_argument('--verify', nargs='?', const='', help='Execute Tier 2 live verification smoke test for a project')
    parser.add_argument('--preview', nargs='?', const='', help='Launch local web preview server for project input surfaces')
    parser.add_argument('--eval', nargs='?', const='', help='Execute multi-dimensional evaluation and scoring harness for a task or project')
    parser.add_argument('--port', type=int, default=8080, help='Port for local UI preview server (default 8080)')
    parser.add_argument('--project', type=validate_project_id, help='Parent project ID')
    parser.add_argument('--resume', type=validate_task_id, metavar='TASK_ID', help='Resume a saved local task')
    parser.add_argument('--model', help='Model identifier (e.g. openai:gpt-4o, anthropic:claude-3-5-sonnet-latest)')
    parser.add_argument('--tier', choices=['fast', 'balanced', 'powerful'], help='Model tier preset (fast, balanced, powerful)')
    parser.add_argument('--model-natasha', help='Model override for Natasha (Coordinator)')
    parser.add_argument('--model-odin', help='Model override for Odin (Researcher)')
    parser.add_argument('--model-taghi', help='Model override for Taghi (Architect)')
    parser.add_argument('--model-meti', help='Model override for Meti (Implementer)')
    parser.add_argument('--model-dana', help='Model override for Dana (Quality Supervisor)')
    parser.add_argument('--supervise', nargs='?', const='advisory', choices=['advisory', 'autonomous', 'off'], help='Dana Quality Supervisor mode: advisory or autonomous')
    parser.add_argument('--dana', dest='supervise', nargs='?', const='advisory', choices=['advisory', 'autonomous', 'off'], help='Alias for --supervise')
    parser.add_argument('--image', help='Docker base image override (e.g. python:3.11-slim)')
    parser.add_argument('-y', '--yes', '--auto', dest='auto', action='store_true', help='Headless mode; accept defaults without interactive prompts')
    parser.add_argument('--step', action='store_true', help='Interactive step gates between each agent lead')
    parser.add_argument('--research', '--research-only', dest='research_only', action='store_true', help='Complete after research stage; do not execute Taghi or Meti')
    args = parser.parse_args()

    # Direct config command: python main.py config or python main.py --config
    if getattr(args, "config", False) or (args.prompt is not None and args.prompt.strip().lower() == "config"):
        from tools.onboarding import run_onboarding_wizard
        run_onboarding_wizard(is_reconfig=True)
        return

    # Interactive project session: python main.py --session [PROJECT_ID] or python main.py session [PROJECT_ID]
    is_session = False
    session_proj = None
    if getattr(args, "session", None) is not None:
        is_session = True
        session_proj = args.session or args.project or "default-project"
    elif args.prompt and args.prompt.strip().lower().startswith("session"):
        is_session = True
        parts = args.prompt.strip().split()
        session_proj = parts[1] if len(parts) > 1 else (args.project or "default-project")

    if is_session:
        from tools.onboarding import check_credentials_configured, run_onboarding_wizard
        if args.model != "test" and os.environ.get("BUILDRELAY_TESTING") != "1" and not check_credentials_configured():
            if args.auto or not sys.stdin.isatty():
                print_agent('orchestrator', 'Run buildrelay config before starting a session.')
                sys.exit(1)
            if not run_onboarding_wizard():
                sys.exit(1)
        from tools.session import run_project_session
        await run_project_session(
            project_id=session_proj,
            model=args.model,
            tier=args.tier,
            auto=args.auto,
            step=args.step,
        )
        return

    # Live verification runner: python main.py --verify [PROJECT_ID] or python main.py verify [PROJECT_ID]
    is_verify = False
    verify_proj = None
    if getattr(args, "verify", None) is not None:
        is_verify = True
        verify_proj = args.verify or args.project or "default-project"
    elif args.prompt and args.prompt.strip().lower().startswith("verify"):
        is_verify = True
        parts = args.prompt.strip().split()
        verify_proj = parts[1] if len(parts) > 1 else (args.project or "default-project")

    if is_verify:
        from tools.live_verifier import run_live_verification
        result = run_live_verification(verify_proj)
        if not result.get("success"):
            sys.exit(1)
        return

    # Local UI preview server: python main.py --preview [PROJECT_ID] or python main.py preview [PROJECT_ID]
    is_preview = False
    preview_proj = None
    if getattr(args, "preview", None) is not None:
        is_preview = True
        preview_proj = args.preview or args.project or "default-project"
    elif args.prompt and args.prompt.strip().lower().startswith("preview"):
        is_preview = True
        parts = args.prompt.strip().split()
        preview_proj = parts[1] if len(parts) > 1 else (args.project or "default-project")

    if is_preview:
        from tools.ui_preview import start_preview_server
        try:
            start_preview_server(
                project_id=preview_proj,
                port=getattr(args, "port", 8080),
                open_browser=not args.auto and sys.stdin.isatty(),
                run_until_interrupted=True,
            )
        except KeyboardInterrupt:
            pass
        return

    # Deliverable evaluation harness runner: python main.py --eval [TARGET] or python main.py eval [TARGET]
    is_eval = False
    eval_target = None
    if getattr(args, "eval", None) is not None:
        is_eval = True
        eval_target = args.eval or args.project or ""
    elif args.prompt and args.prompt.strip().lower().startswith("eval"):
        is_eval = True
        parts = args.prompt.strip().split()
        eval_target = parts[1] if len(parts) > 1 else (args.project or "")

    if is_eval:
        from tools.eval_harness import DeliverableEvaluator
        from tools.ui import print_evaluation_scorecard
        ws_root = Path("workspace")
        target_dir = None
        if eval_target:
            if (ws_root / eval_target).is_dir():
                target_dir = ws_root / eval_target
            elif Path(eval_target).is_dir():
                target_dir = Path(eval_target)
        if not target_dir and ws_root.is_dir():
            dirs = [d for d in ws_root.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))]
            if dirs:
                dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                target_dir = dirs[0]
        if not target_dir:
            print_agent('orchestrator', 'No project or task workspace found to evaluate.')
            sys.exit(1)

        evaluator = DeliverableEvaluator(target_dir, project_id=args.project)
        report = evaluator.evaluate()
        evaluator.save_report(report)
        print_evaluation_scorecard(report)
        return

    if args.resume and (args.prompt is not None or args.project is not None):
        parser.error('--resume cannot be combined with a prompt or --project; saved values are reused')
    if not args.resume and (args.prompt is None or not args.prompt.strip()):
        parser.error('Provide a non-empty prompt or --resume TASK_ID')

    from tools.onboarding import check_credentials_configured, run_onboarding_wizard

    is_testing = (
        (args.model == "test")
        or os.environ.get("BUILDRELAY_TESTING") == "1"
        or type(get_chatgpt_model).__name__ in ("Mock", "AsyncMock", "MagicMock")
    )
    if not check_credentials_configured() and not is_testing:
        if args.auto or not sys.stdin.isatty():
            print_agent('orchestrator', '[bold red]No AI credentials detected. Run `buildrelay config` to configure credentials.[/bold red]')
            sys.exit(1)
        print_agent('orchestrator', '[bold yellow]No AI credentials detected.[/bold yellow] Launching setup wizard first...')
        configured = run_onboarding_wizard()
        if not configured:
            print_agent('orchestrator', '[bold red]Setup cancelled. Configure credentials before running tasks.[/bold red]')
            sys.exit(1)
    lead_overrides = {
        "natasha": args.model_natasha,
        "odin": args.model_odin,
        "taghi": args.model_taghi,
        "meti": args.model_meti,
        "dana": args.model_dana,
    }
    supervise_mode = getattr(args, "supervise", None)
    if not supervise_mode:
        env_sup = os.environ.get("BUILDRELAY_SUPERVISE", "off").lower()
        if env_sup in ("1", "true", "yes", "advisory"):
            supervise_mode = "advisory"
        elif env_sup == "autonomous":
            supervise_mode = "autonomous"
        else:
            supervise_mode = "off"
    try:
        ledger = TaskLedger()
        task_id = args.resume or task_id_for(args.prompt.strip(), ledger=ledger)
        with ledger.claim(task_id):
            if args.resume:
                record = ledger.load(task_id)
            else:
                record = TaskRecord(task_id=task_id, prompt=args.prompt.strip(), project_id=args.project)
                ledger.create(record)
            print_task_header(task_id, record.prompt, project_id=record.project_id, is_resume=bool(args.resume))
            if record.status == 'COMPLETED':
                print_agent('orchestrator', 'Task is already completed; no stages were run.')
                return
            try:
                result = await run_task(
                    record,
                    ledger,
                    model_override=args.model,
                    image_override=args.image,
                    auto=args.auto,
                    step=args.step,
                    tier=args.tier,
                    lead_overrides=lead_overrides,
                    research_only=args.research_only,
                    supervise=supervise_mode,
                )
            except (Exception, KeyboardInterrupt, asyncio.CancelledError) as error:
                record.status = 'FAILED'
                record.error = f'{type(error).__name__}: {error}'
                ledger.save(record)
                raise
            record.result = result
            record.status = 'COMPLETED' if result.status == 'success' else 'FAILED'
            record.error = None if result.status == 'success' else result.summary
            ledger.save(record)
            print_completion(task_id, result.status == 'success', result.summary)
            if record.token_usage:
                print_token_summary_table(record.token_usage, default_model=args.model)
            if result.status == 'success':
                workspace_dir = record.project_id or record.task_id
                workspace_path = Path("workspace") / workspace_dir
                print_workspace_tree(workspace_path)
                print_how_to_run(workspace_path)
            if result.status != 'success':
                sys.exit(1)
            if (
                result.status == 'success'
                and not args.research_only
                and not args.auto
                and sys.stdin.isatty()
                and not is_testing
            ):
                await run_iteration_loop(
                    record=record,
                    ledger=ledger,
                    args=args,
                    lead_overrides=lead_overrides,
                )
    except Exception as error:
        print_agent('orchestrator', f'[bold red]{error}[/bold red]')
        print_agent('orchestrator', f'To retry a saved task: python main.py --resume {task_id}')
        sys.exit(1)


async def run_iteration_loop(
    record: TaskRecord,
    ledger: TaskLedger,
    args: Any,
    lead_overrides: dict[str, Any],
    input_func: Callable[[str], str] | None = None,
) -> None:
    """
    Continuous feature iteration loop allowing users to iteratively add features,
    refactor code, run verification, or launch a REPL session without leaving the process.
    """
    from tools.ui import prompt_iteration_gate
    current_project = record.project_id or record.task_id

    while True:
        action, payload = prompt_iteration_gate(
            project_id=current_project,
            task_id=record.task_id,
            auto=getattr(args, "auto", False),
            input_func=input_func,
        )
        if action in ("exit", None):
            break
        elif action == "none":
            continue
        elif action == "session":
            from tools.session import run_project_session
            await run_project_session(
                project_id=current_project,
                model=getattr(args, "model", None),
                tier=getattr(args, "tier", None),
                auto=getattr(args, "auto", False),
                step=getattr(args, "step", False),
                input_func=input_func,
            )
            break
        elif action == "verify":
            from tools.live_verifier import run_live_verification
            run_live_verification(current_project)
            continue
        elif action == "preview":
            from tools.ui_preview import start_preview_server
            try:
                start_preview_server(
                    project_id=current_project,
                    port=getattr(args, "port", 8080),
                    open_browser=not getattr(args, "auto", False) and (input_func is None and sys.stdin.isatty()),
                    run_until_interrupted=True,
                )
            except (KeyboardInterrupt, Exception):
                pass
            continue
        elif action in ("feature", "refactor"):
            if not payload or not payload.strip():
                continue
            next_prompt = payload.strip()
            if action == "refactor":
                next_prompt = f"Refactor and optimize: {next_prompt}"

            next_task_id = task_id_for(next_prompt, ledger=ledger)
            with ledger.claim(next_task_id):
                record = TaskRecord(
                    task_id=next_task_id,
                    prompt=next_prompt,
                    project_id=current_project,
                )
                ledger.create(record)
                print_task_header(next_task_id, record.prompt, project_id=current_project, is_resume=False)
                try:
                    result = await run_task(
                        record,
                        ledger,
                        model_override=getattr(args, "model", None),
                        image_override=getattr(args, "image", None),
                        auto=getattr(args, "auto", False),
                        step=getattr(args, "step", False),
                        tier=getattr(args, "tier", None),
                        lead_overrides=lead_overrides,
                        research_only=getattr(args, "research_only", False),
                        supervise=getattr(args, "supervise", "off") or "off",
                    )
                except (Exception, KeyboardInterrupt, asyncio.CancelledError) as error:
                    record.status = "FAILED"
                    record.error = f"{type(error).__name__}: {error}"
                    ledger.save(record)
                    raise
                record.result = result
                record.status = "COMPLETED" if result.status == "success" else "FAILED"
                record.error = None if result.status == "success" else result.summary
                ledger.save(record)
                print_completion(next_task_id, result.status == "success", result.summary)
                if record.token_usage:
                    print_token_summary_table(record.token_usage, default_model=getattr(args, "model", None))
                if result.status == "success":
                    workspace_path = Path("workspace") / current_project
                    print_workspace_tree(workspace_path)
                    print_how_to_run(workspace_path)
                else:
                    print_agent("orchestrator", f"[bold red]Iteration task {next_task_id} failed.[/bold red]")


def cli_entrypoint() -> None:
    """Console script entrypoint for `buildrelay` command."""
    asyncio.run(main())


if __name__ == '__main__':
    asyncio.run(main())

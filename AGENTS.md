# Agent Guidelines

You are an autonomous development agent operating in a restricted workspace.

Independently plan, implement, test, and debug tasks.

Execute commands and modify files within the authorized workspace without requesting routine approvals.

Never access, modify, or delete files outside the workspace.

Never request unsandboxed execution.

Do not access credentials, secrets, or unrelated repositories.

Do not install global dependencies or modify system configuration.

Do not use network access unless explicitly authorized.

Maintain a Git history and report completed changes, tests, and unresolved issues.

Communication style: When reporting back to the user, keep all messages concise, directly to the point, and as short as possible. Focus strictly on facts and actions; do not worry about formal grammar, filler sentences, or sophisticated wording.

If a task requires permissions outside these boundaries, stop and explain the limitation.

Your objective is maximum autonomy within strict security boundaries.

# BuildRelay Project Guidelines 

## Architecture & Conventions
- **Sequential 4-lead flow with on-demand specialization**: Natasha (Routing & Alignment) → Odin (Research, on-demand) → Diba (Early Prototype & UI/UX Design, on-demand) → Taghi (Architecture & Review) → Meti (Phased Docker Execution).
- **Interactive Grill-Me Alignment**:
  - `tools/grill.py`: Unified multi-choice and open-ended interview engine with quick keyboard shortcuts (`[Enter]` for default, `[1, 2...]` to pick, `[c]` for custom text, `[a]` to accept all remaining, `[q]` to quit). Numbers `[1]`, `[2]` are clearly indexed.
  - Natasha conducts an intent/scope grill interview (up to 10 plain-English questions covering entry points, schemas, triggers, edge cases) before final routing.
  - Taghi conducts an architectural grill interview using plain-English concepts (zero technical jargon; translating storage durability, accidental double-clicks, and error handling into practical business choices).
  - Diba conducts a dedicated UI/UX Design & Ergonomics grill interview (`ui_spec` covering visual archetypes, Tailwind palettes, layout hierarchy, validation feedback, and 5 discrete states).
- **Early Prototype & Diba UI/UX Lead (`agents/diba.py`)**:
  - Early-Stage Interactive Prototyping: Diba generates a standalone, working Zero-to-One interactive HTML prototype (`prototype.html` and `form.html`) with an in-memory mock engine before Taghi architects backend specifications.
  - Prototype Approval Gate (`tools/ui.py`): Explicit numbered gate (`[1]` Refine, `[2]` Approve, `[3]` Skip, `[q]` Abort) allowing human feedback cycles with Diba. Background preview server remains active across refinement iterations.
  - Curated Design Archetypes (`tools/design_system.py`): Studio-grade visual blueprints ('Linear Dark Minimalist', 'Executive Bento Dashboard', 'Stripe Enterprise Clean', 'Split-Pane Studio Workspace') that prevent ugly blank-canvas HTML generation.
  - Dual-Specification Output: Diba persists `vault/specs/<task_id>-ui.md` with explicit Tailwind hex tokens, component wireframes, input validation rules, and 5 interactive states (`empty`, `validating`, `submitting`, `success`, `error`).
- **Concise Executive Handoffs & Clean Viewport**:
  - All interactive gates (`prompt_alignment_gate`, `prompt_step_gate`, `prompt_prototype_gate`, `prompt_spec_approval_gate`, `prompt_dana_gate`) cleanly suspend the Cockpit Live TUI using `cockpit.pause()` before rendering cards, keeping the handoff document fully visible in the active viewport without pushing content offscreen.
  - Taghi's proposal card displays a concise ASCII workflow diagram (e.g. `[User UI/Form] ➔ [API / Server Logic] ➔ [Data Storage] ➔ [Deterministic Tests]`) and brief summary, linking to deep markdown specifications in `vault/specs/<task_id>-spec.md`.
  - Python `readline` support and isolated `> ` prompt lines enable smooth multi-line wrapping and backward line deletion without ANSI offset glitches.
- **Dual-Specification Architecture & UI/UX Standards**:
  - Taghi persists backend technical specifications in `vault/specs/<task_id>-spec.md` (models, APIs, sanitizers, and validation phases), while Diba persists studio-grade UI/UX specifications in `vault/specs/<task_id>-ui.md` (archetypes, Tailwind hex tokens, component wireframes, input validation rules, and 5 interactive states).
  - Phased Execution Ordering: Meti executes and verifies backend core logic and Tier 1 unit tests first in Docker, and only implements frontend UI/UX surfaces after backend logic passes.
- **Shared Contracts**: All stage inputs, outputs, attempts, and checkpoints live in `contracts/`. Do not introduce circular dependencies between agents. `TechnicalSpec` includes `ui_spec` (`UIDesignSpec`), `input_interface_spec`, and `clarification_questions`.
- **Two-Tier Verification Architecture**:
  - `Tier 1 (Automated Docker Sandbox)`: Meti validates all execution phases inside Docker using offline deterministic unit tests and mock service adapters (e.g. mock `SpreadsheetApp`, mock REST responses) with 0 external network dependencies.
  - `Tier 2 (Guided Live Verification)`: Taghi mandates `live_verification_guide`, and Meti builds a dedicated live smoke script (e.g. `scripts/verify_live.py` or Apps Script `testDirectSync()`) plus an interactive checklist in `README.md` for real-environment verification.
- **Research-Only Flow**: Tasks with `--research` / `--research-only` or explicit research prompts complete cleanly after Odin without invoking Taghi or Meti.
- **Project REPL & Workspace Memory**:
  - `buildrelay session <project_id>` (`tools/session.py`): Continuous conversational project REPL supporting iterative commands (`/profile`, `/env`, `/verify`, `/preview`, `/test`, `/exit`).
  - Living `PROJECT_PROFILE.md` memory schema in `workspace/<project_id>/` recording active schemas, input surfaces, rules, and task history. Injected into agent prompts.
  - Dedicated project workspace `.env` (mode `0600`, gitignored) for project-specific tokens, spreadsheet IDs, and webhook secrets.
- **Continuous Feature Iteration Pipeline**:
  - `prompt_iteration_gate` (`tools/ui.py`) & `run_iteration_loop` (`main.py`): Post-delivery gate allowing users to seamlessly add sequential feature milestones (`[1]`), refactor code (`[2]`), launch the project REPL session (`[3]`), or run live verification/preview (`[4]`).
  - Iteration tasks inherit project identity and inject living memory from `PROJECT_PROFILE.md` into Natasha's and Taghi's agent prompts (`[INCREMENTAL FEATURE EVOLUTION]` and `[INCREMENTAL ARCHITECTURE SPECIFICATION]`), preserving existing schemas, file structures, and verified interfaces.
- **Dana Quality Supervisor Agent**:
  - `agents/dana.py` (`DanaQualitySupervisor`): Principal Quality Supervisor evaluating intermediate deliverables across Natasha, Odin, Taghi, Diba, and Meti.
  - Contract: `DanaCritique` (`contracts/`) providing structured `verdict` ('approve', 'suggest', 'warn', 'block'), `score` (0-100), `strengths`, `risks_or_gaps`, and `actionable_recommendations`.
  - Intent Comparison Grilling: `conduct_intent_comparison_grill` actively detects discrepancies between the user's initial prompt and the lead's deliverable, launching interactive comparison questions to empower the user to enforce requirements before execution.
  - Operating Modes:
    - `Advisory Mode` (`--supervise advisory` / `--dana`): Presents Rich critique card and gate (`prompt_dana_gate`), allowing developers to inspect suggestions, apply steering to the lead, skip, or abort.
    - `Autonomous Mode` (`--supervise autonomous`): Detects warnings or blocking gaps and autonomously steers leads to revise specifications and code without human intervention.
  - Persistence: Saves structured audit notes under `vault/supervision/<task_id>-<stage>.md`.
- **Verification Runner & UI Preview**:
  - `buildrelay verify <project_id>` (`tools/live_verifier.py`): Tier 2 live verification smoke test runner executing host scripts with project credentials.
  - `buildrelay preview <project_id>` (`tools/ui_preview.py`): Local web preview server serving generated input forms and web entries.
- **Automated Deliverable Evaluation Harness**:
  - `buildrelay eval <project_id|task_id>` (`tools/eval_harness.py`): Multi-dimensional evaluation engine scoring deliverables across 5 dimensions: Test Integrity & Coverage (0-20), Security & Sanitization (0-20), UI Surface & Usability (0-20), Tier 2 Live Verification Readiness (0-20), and Architectural Conformance (0-20).
  - Terminal Scorecard (`print_evaluation_scorecard` in `tools/ui.py`): Renders structured score (0-100), verdict ('exceptional', 'pass', 'marginal', 'fail'), dimension breakdown table, and actionable recommendations.
  - REPL Command: `/eval` inside `buildrelay session <project_id>`.
  - Persistence: Saves markdown evaluation reports under `vault/evaluations/eval-<task_id>.md`.
- **Meti Architecture**:
  - `agents/meti.py`: Implementation coordinator and Docker tool binding.
  - `agents/execution_policy.py`: Phase validation ordering, retry budgets (3 attempts per phase per run), recovery prompts, and ground-truth result finalization.
  - `agents/review_renderer.py`: Pure Markdown code-review report rendering.
- **Ledger & Persistence**: Stored locally in SQLite at `.state/tasks.db`. Checkpoints are validated with `ImplementationCheckpoint.validate_plan_consistency`.
- **Workspaces**: Generated code lives in `workspace/<project_id>/` (or `workspace/<task_id>/`).
- **Dependency Injection**: Agents accept explicit collaborator parameters (`graph_manager`, `sandbox`, artifact directories). Constructors defer Docker client connections and directory creation until operations need them.
- **Security & Vault Isolation**: Docker containers execute without host environment variables passed and only mount the task workspace. Model-callable vault note tools use `tools/vault_infra.py` safe writers. Application-generated stage artifacts also use direct writes to configured directories; do not assume every artifact write passes through the shared writer.
- **Terminal UI & Diagnostics**: Console visuals use `rich` via `tools/ui.py` for role-based badges (Natasha, Odin, Taghi, Meti), panels, and phase tables. Diagnostic tool calls are subdued, and Graphify subprocess stderr is suppressed unless `BUILDRELAY_DEBUG=1` is set.
- **Split-Pane Terminal Cockpit & Live Telemetry Engine (`tools/cockpit.py`)**:
  - Live TUI dashboard with 4 panes: Header HUD (live elapsed timer, token usage, cost, model), Workflow Sidebar (pipeline progression stepper, phased roadmap, living memory), Container Telemetry (real-time streaming Docker logs), and Interactive Command Dock (action status, hotkeys `[P] Preview [V] Verify [D] Dana [L] Logs [Q] Exit`).
  - Background Heartbeat Ticker: Daemon thread (`_ticker_loop`) running at 0.5s intervals updating dynamic elapsed timer and rotating Braille activity spinner (`● RUNNING ⠋`) during async LLM calls.
  - Re-entrant pause reference counting (`cockpit.pause()`) and prompt sanitation: `termios.tcflush(sys.stdin, termios.TCIFLUSH)` discards queued keystrokes before gate/grill prompts, and explicit `\033[0m` ANSI reset prevents BCE orange bar terminal artifacts.
- **Meti Multi-Phase Implementation Loop (`agents/meti.py`)**:
  - Automatically advances across turns through all roadmap phases until all declared phases pass sandbox validation.
  - Telemetry updates dynamically across phases, reflecting phase statuses in real time.

## Model Configuration & Research
- Explicit per-lead models are selected through `tools/model_tiers.py` and discovered via `tools/model_catalog.py`; interactive onboarding lives in `tools/onboarding.py`.
- Setup saves `BUILDRELAY_PROVIDER`, `BUILDRELAY_MODEL`, `BUILDRELAY_MODEL_MODE=selected`, and explicit assignments (`MODEL_NATASHA`, `MODEL_ODIN`, `MODEL_TAGHI`, `MODEL_DIBA`, `MODEL_METI`).
- Web Browser Login connects directly via `login_with_chatgpt_browser` (ChatGPT Codex) or `login_with_claude_browser` (Claude Pro/Max subscription / `claude setup-token`) with zero API charges, while API connections query provider catalogs.
- Natasha and Odin use web search snippets from `tools/web_search.py`; queries prioritize Tavily API (`TAVILY_API_KEY` in `.env`) with automated fallback to DuckDuckGo HTML scraping. Odin can query PyPI/npm and records search-result URLs.
- Odin has three search calls per research invocation. Registry lookups and Natasha searches are outside that budget.
- URL checks do not resolve DNS or revalidate redirects. Page fetching is a helper, not a registered agent tool. Registry connectivity failures do not establish successful verification.
- Token costs are estimates from bundled rates; SDK cache settings do not guarantee provider caching.

## Developer Knowledge Graph & Context Retrieval
- **Local External Knowledge Graph**: The codebase AST graph for AP-V2 lives at `../build-relay-graph/graphify-out/` (specifically `../build-relay-graph/graphify-out/graph.json`), completely decoupled from git and independent of BuildRelay's internal task vault (`vault/`).
- **Visual Artifacts**: Interactive architecture visualization lives at `../build-relay-graph/graphify-out/graph.html`.
- **Pre-Task Retrieval Directive**:
  - Before modifying, refactoring, or researching codebase components, development agents (such as Antigravity) must consult the graph for context rather than conducting blind file scans or grep searches.
  - **Inspect any symbol, function, or class**:
    `.venv/bin/python -m graphify explain "<Symbol>" --graph ../build-relay-graph/graphify-out/graph.json`
  - **Trace call paths and relationships between components**:
    `.venv/bin/python -m graphify path "<SymbolA>" "<SymbolB>" --graph ../build-relay-graph/graphify-out/graph.json`
  - **Incremental Sync / Refresh**: After completing major changes, refresh the external graph:
    `.venv/bin/python -m graphify extract . --code-only --no-cluster --out ../build-relay-graph`

## Testing & Verification
- Run tests using `.venv/bin/pytest` or `.venv/bin/python scripts/validate.py`.
- Preserve the 3-attempt validation retry budget per phase.
- Deterministic unit tests mock external services (Docker, Graphify, model calls).
- Opt-in integration smoke checks verify real Docker and Graphify via `BUILDRELAY_INTEGRATION=1 pytest -m integration`.

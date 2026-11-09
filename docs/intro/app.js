/**
 * BuildRelay Interactive Architecture & Thought Stream
 * Continuous loop animation engine with SVG bezier interpolation.
 * Showcases: Logging Handling, Graphify & Obsidian Vault, Directory/Project/Task Lifecycle.
 */

const STAGES = [
    {
        step: 0,
        name: "0. Inception",
        phase: "Step 0: Project, Task & State Scaffolding",
        agent: "CLI Runner",
        leadPill: "⚡ Command Dispatch & Mutex",
        color: "#ea580c",
        pathFraction: 0.0,
        desc: "The developer invokes BuildRelay via CLI. The framework creates the target project directory (<code>workspace/lead-gateway/</code>), acquires an exclusive mutex lock (<code>.state/task-lead-gateway.lock</code>), initializes the SQLite ledger (<code>.state/tasks.db</code>), and begins streaming stdio to <code>.state/task.log</code>.",
        metrics: [
            "Project: workspace/lead-gateway/",
            "State Ledger: .state/tasks.db (Locked)",
            "Active Lock: .state/task-lead-gateway.lock",
            "Streaming Log: .state/task.log",
            "Living Memory: PROJECT_PROFILE.md"
        ],
        danaCritique: {
            verdict: "OBSERVING",
            note: "Atomic lock acquired. Project directory scaffolded. Monitoring prompt ingestion with zero race conditions."
        },
        files: [
            {
                dir: ".state/",
                items: [
                    { name: "tasks.db", tag: "new", type: "db", desc: "SQLite State Ledger & Checkpoint Database" },
                    { name: "task-lead-gateway.lock", tag: "new", type: "lock", desc: "Atomic Concurrency Mutex Lock (PID 51240)" },
                    { name: "task.log", tag: "new", type: "log", desc: "Real-Time Streaming Subprocess & Stdio Log" }
                ]
            },
            {
                dir: "workspace/lead-gateway/",
                items: [
                    { name: "PROJECT_PROFILE.md", tag: "new", type: "memory", desc: "Living Project Memory & Active Schemas Schema" }
                ]
            }
        ],
        artifacts: {
            "tasks.db": `-- SQLite State Ledger: .state/tasks.db
-- Schema definition for task lifecycle tracking
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    route TEXT DEFAULT 'PENDING',
    status TEXT DEFAULT 'RUNNING',
    current_lead TEXT DEFAULT 'natasha',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Newly Scaffolded Task Record:
INSERT INTO tasks (task_id, project_id, prompt, route, status, current_lead)
VALUES (
    'task-lead-gateway-20261109',
    'lead-gateway',
    'Build a Customer Inquiry and Lead Qualification Gateway in Python with web form and CSV batch import...',
    'PENDING',
    'RUNNING',
    'natasha'
);`,

            "task-lead-gateway.lock": `# Atomic Concurrency Mutex Lock: .state/task-lead-gateway.lock
# Prevents overlapping runs or race conditions on the project workspace
PID: 51240
HOST: dev-station-mac
PROJECT_ID: lead-gateway
TASK_ID: task-lead-gateway-20261109
TIMESTAMP: 2026-11-09T10:30:00.124Z
STATUS: EXCLUSIVE_LOCK_ACQUIRED
REVERSIBLE_ON_EXIT: true`,

            "task.log": `[2026-11-09 10:30:00.102] [SYSTEM] BuildRelay v0.2.0 starting...
[2026-11-09 10:30:00.115] [SYSTEM] Bound workspace directory: /workspace/lead-gateway
[2026-11-09 10:30:00.120] [MUTEX] Acquiring atomic lock: .state/task-lead-gateway.lock (PID: 51240)
[2026-11-09 10:30:00.124] [MUTEX] Lock acquired successfully.
[2026-11-09 10:30:00.130] [LEDGER] Initializing SQLite ledger: .state/tasks.db
[2026-11-09 10:30:00.142] [LEDGER] Inserted task_id='task-lead-gateway-20261109', route='PENDING', status='RUNNING'
[2026-11-09 10:30:00.150] [MEMORY] Scaffolded living project profile: workspace/lead-gateway/PROJECT_PROFILE.md
[2026-11-09 10:30:00.160] [PROVIDER] Model catalog initialized: Google Gemini 1.5 Pro (Tier: Balanced)
[2026-11-09 10:30:00.170] [ROUTING] Handing off user prompt to Natasha (Routing & Alignment)...`,

            "PROJECT_PROFILE.md": `---
project_id: lead-gateway
created_at: 2026-11-09T10:30:00Z
updated_at: 2026-11-09T10:30:00Z
active_tasks:
  - task-lead-gateway-20261109
status: active
---

# Living Project Profile: lead-gateway

> This file is maintained continuously by BuildRelay across agent turns.
> It serves as the long-term context memory for iterative development.

## 1. Project Purpose & Scope
High-assurance lead qualification and customer inquiry ingestion gateway with dual entry surfaces (web form + batch CLI), strict formula injection defense, and tier-based routing.

## 2. Active Schemas
*(Pending Natasha scope alignment and Taghi architectural specification)*

## 3. Verified Input Surfaces
*(Pending Meti Docker sandbox implementation)*

## 4. Verification Checklist
- **Tier 1 (Automated Docker)**: \`pytest tests/\`
- **Tier 2 (Guided Live)**: \`python scripts/verify_live.py\``
        },
        consoleLog: `🚀 BuildRelay v0.2.0 (macOS / Darwin)
────────────────────────────────────────────────────────────
▶ [INIT] Project Workspace: workspace/lead-gateway/ (created)
▶ [INIT] Concurrency Lock:  .state/task-lead-gateway.lock (PID: 51240)
▶ [INIT] SQLite Ledger:     .state/tasks.db (exclusive lock)
▶ [INIT] Living Memory:     workspace/lead-gateway/PROJECT_PROFILE.md
▶ [INIT] Logging Handler:   .state/task.log (streaming stdio)
▶ [ROUTING] Dispatching prompt to Natasha (Routing & Alignment)...`
    },

    {
        step: 1,
        name: "1. Natasha",
        phase: "Step 1: Scope Alignment & Obsidian Brief",
        agent: "Natasha",
        leadPill: "🎯 Natasha · Coordinator",
        color: "#0284c7",
        pathFraction: 0.205,
        desc: "Natasha initiates a Grill-Me interview with quick keyboard shortcuts (<code>[1, 2...]</code>, <code>[Enter]</code>). She clarifies inbound entry mechanisms, formula injection triggers, and budget tiers, synthesizing an Obsidian task brief with wikilinks in <code>vault/tasks/</code>.",
        metrics: [
            "Grill Questions: 3 Asked / 3 Answered",
            "Target Route: ARCHITECTURE (Taghi & Diba)",
            "Obsidian Vault: vault/tasks/task-lead-gateway-brief.md",
            "Wikilinks: [[PROJECT_PROFILE]], [[spec-lead-gateway]]",
            "State Ledger: Updated -> ARCHITECTURE"
        ],
        danaCritique: {
            verdict: "APPROVED",
            note: "Audit Gate 1: Intent brief matches user prompt with zero scope hallucinations. Wikilinks verified."
        },
        files: [
            {
                dir: ".state/",
                items: [
                    { name: "tasks.db", tag: "mod", type: "db", desc: "Updated route -> ARCHITECTURE" },
                    { name: "task.log", tag: "mod", type: "log", desc: "Appended Grill-Me Q&A session & routing decision" }
                ]
            },
            {
                dir: "vault/tasks/",
                items: [
                    { name: "task-lead-gateway-brief.md", tag: "new", type: "obsidian", desc: "Obsidian Intent Brief with Frontmatter & Wikilinks" }
                ]
            }
        ],
        artifacts: {
            "task-lead-gateway-brief.md": `---
title: Task Brief — Customer Inquiry & Lead Qualification Gateway
task_id: task-lead-gateway-20261109
project: lead-gateway
lead: natasha
route: ARCHITECTURE
status: aligned
tags:
  - buildrelay
  - scope-brief
  - route/architecture
wikilinks:
  - "[[workspace/lead-gateway/PROJECT_PROFILE|Project Profile]]"
  - "[[vault/specs/spec-lead-gateway|Taghi Backend Architecture]]"
  - "[[vault/specs/spec-lead-gateway-ui|Diba UI Specification]]"
---

# Task Brief: Customer Inquiry & Lead Qualification Gateway

> **Task ID:** \`task-lead-gateway-20261109\`  
> **Lead:** Natasha (Routing & Alignment)  
> **Route Decision:** ARCHITECTURE (Requires Taghi backend models & Diba UI design)  
> **Related Memory:** [[workspace/lead-gateway/PROJECT_PROFILE|lead-gateway profile]]

## 1. Intent Alignment Brief
The user requires a secure lead qualification gateway with dual input mechanisms:
1. Inbound prospects submit inquiries via a responsive Tailwind CSS web form (\`form.html\`).
2. Operations staff bulk-ingest leads using a batch command-line script (\`scripts/import_leads.py\`).

## 2. Confirmed Invariants & Guardrails
- **Validation**: Strict RFC email regex and international phone formatting.
- **Formula Injection Defense**: Spreadsheet trigger characters (\`=\`, \`+\`, \`-\`, \`@\`, \`|\`, \`%\`) must be prefixed with a single quote (\`'\`) before writing to tabular sinks.
- **Budget Tiers**:
  - Enterprise: Budget >= $50,000 or Company Size > 250
  - Mid-Market: Budget $10,000 - $49,999 or Company Size 50 - 250
  - SMB: Budget < $10,000
- **Two-Tier Verification**: Offline unit tests with mock CRM adapters (Docker Tier 1), plus real-environment webhook smoke script (Tier 2).`,

            "tasks.db": `-- SQLite Ledger Update: .state/tasks.db
-- Natasha records routing decision and updates task state
UPDATE tasks SET 
    route = 'ARCHITECTURE',
    status = 'ROUTED_TO_TAGHI',
    current_lead = 'taghi',
    updated_at = CURRENT_TIMESTAMP
WHERE task_id = 'task-lead-gateway-20261109';

-- Verify update:
SELECT task_id, route, status, current_lead FROM tasks 
WHERE task_id = 'task-lead-gateway-20261109';
-- Output: task-lead-gateway-20261109 | ARCHITECTURE | ROUTED_TO_TAGHI | taghi`,

            "task.log": `[2026-11-09 10:30:02.410] [NATASHA] Initiating Scope & Intent Alignment Grill
[2026-11-09 10:30:02.415] [GRILL] Q1: Primary Input Surfaces -> Options: [1] Web Form + Batch CSV CLI, [2] Web Form only, [3] REST API Webhook only
[2026-11-09 10:30:04.180] [GRILL] User selected: [1] (Web Form + Batch CSV CLI)
[2026-11-09 10:30:04.200] [GRILL] Q2: Formula Injection Defense -> Options: [1] Quote prefix ('=), [2] Strip triggers, [3] Reject
[2026-11-09 10:30:05.510] [GRILL] User selected: [1] (Quote prefix triggers)
[2026-11-09 10:30:05.530] [GRILL] Q3: Budget Tier Thresholds -> User accepted defaults ($50k Enterprise / $10k Mid-Market)
[2026-11-09 10:30:05.890] [NATASHA] Synthesizing Obsidian intent brief: vault/tasks/task-lead-gateway-brief.md
[2026-11-09 10:30:06.012] [NATASHA] Wikilinks injected: [[PROJECT_PROFILE]], [[spec-lead-gateway]], [[spec-lead-gateway-ui]]
[2026-11-09 10:30:06.050] [LEDGER] .state/tasks.db updated: route='ARCHITECTURE', status='ROUTED_TO_TAGHI'
[2026-11-09 10:30:06.070] [ROUTING] Handing off to Odin (Deep Research) & Taghi (Architecture)...`
        },
        consoleLog: `╭──────────────────────── 🧭 Intent & Scope Interview ─────────────────────────╮
│  🎯 NATASHA (Routing & Alignment)                                            │
│  Q1: Primary Input Entry Surfaces:                                           │
│    [1] Web Form (Tailwind CSS, validation) + Batch CSV Import CLI (Default)  │
│    [2] Web Form only                                                         │
│    [3] REST API Webhook only                                                 │
│  Selection: [1]                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
↳ Natasha persisted brief: vault/tasks/task-lead-gateway-brief.md
↳ Wikilinks: [[PROJECT_PROFILE]] [[spec-lead-gateway]]
↳ Route confirmed: ARCHITECTURE → Awakening Odin & Taghi...`
    },

    {
        step: 2,
        name: "2. Odin",
        phase: "Step 2: Graphify AST Traversal & Web Intelligence",
        agent: "Odin",
        leadPill: "🔮 Odin · Researcher",
        color: "#7c3aed",
        pathFraction: 0.410,
        desc: "Odin scans the codebase using Graphify AST indexing (<code>.state/graphify/stat-index.json</code>) to locate reusable sanitization patterns. He runs external queries via Tavily for spreadsheet formula injection standards and checks PyPI for mock adapter libraries.",
        metrics: [
            "Graphify AST: 52 Modules Indexed",
            "Obsidian Vault: vault/research/research-lead-gateway.md",
            "Wikilinks: [[task-lead-gateway-brief]], [[tools/vault_infra]]",
            "External Search: Tavily API (RFC 4180 + Injection)",
            "PyPI Metadata: pytest, requests verified"
        ],
        danaCritique: {
            verdict: "APPROVED",
            note: "Audit Gate 2: Graphify AST index populated. Retrieved RFC formula sanitizers and package schemas verified."
        },
        files: [
            {
                dir: ".state/graphify/",
                items: [
                    { name: "stat-index.json", tag: "new", type: "graphify", desc: "Graphify Codebase AST Graph & Symbol Index" }
                ]
            },
            {
                dir: "vault/research/",
                items: [
                    { name: "research-lead-gateway.md", tag: "new", type: "obsidian", desc: "Obsidian Research Note with Citations & Graphify Links" }
                ]
            },
            {
                dir: ".state/",
                items: [
                    { name: "task.log", tag: "mod", type: "log", desc: "Graphify AST indexer & Tavily API search logs" }
                ]
            }
        ],
        artifacts: {
            "stat-index.json": `{
  "graphify_version": "2.1.0",
  "project_root": "workspace/lead-gateway/",
  "ast_summary": {
    "modules_indexed": 52,
    "symbols_discovered": 118,
    "classes_extracted": 24,
    "functions_extracted": 94
  },
  "reusable_patterns": [
    {
      "symbol": "tools/vault_infra.py:safe_write_markdown",
      "purpose": "Atomic markdown writer with symlink protection and directory auto-creation",
      "ast_signature": "def safe_write_markdown(path: Path, content: str) -> None"
    },
    {
      "symbol": "tests/test_eval_harness.py:MockCRMSink",
      "purpose": "Zero-dependency mock CRM dispatch adapter for deterministic offline unit testing",
      "ast_signature": "class MockCRMSink: def record_lead(self, lead: dict) -> bool"
    }
  ],
  "obsidian_wikilink_graph": {
    "vault/tasks/task-lead-gateway-brief.md": [
      "workspace/lead-gateway/PROJECT_PROFILE.md",
      "vault/specs/spec-lead-gateway.md"
    ]
  }
}`,

            "research-lead-gateway.md": `---
title: Technical Research — Lead Qualification Gateway
task_id: task-lead-gateway-20261109
lead: odin
status: completed
tags:
  - buildrelay
  - research
  - graphify
  - formula-injection
wikilinks:
  - "[[vault/tasks/task-lead-gateway-brief|Task Brief]]"
  - "[[tools/vault_infra|Vault Infrastructure]]"
  - "[[vault/specs/spec-lead-gateway|Taghi Spec]]"
---

# Technical Research Brief: Lead Qualification Gateway

> **Task ID:** \`task-lead-gateway-20261109\`  
> **Lead:** Odin (Technical Researcher)  
> **Source Brief:** [[vault/tasks/task-lead-gateway-brief|task-lead-gateway-brief.md]]

## 1. Graphify AST Traversal & Codebase Reuse
Traversed local AST via \`.state/graphify/stat-index.json\`:
- Existing pattern found: \`tools/vault_infra.py\` provides safe string sanitizers and atomic writes.
- Existing mock adapter found in \`tests/test_eval_harness.py\` (\`MockCRMSink\`).
- Recommended: reuse the mock pattern to ensure Tier 1 Docker tests run offline with 0 network flakiness.

## 2. Spreadsheet Formula Injection Defense
- **Vulnerability**: Spreadsheet applications (Excel, Google Sheets, LibreOffice) evaluate cells starting with \`=\`, \`+\`, \`-\`, \`@\`, \`|\`, or \`%\` as formula expressions.
- **Mitigation Standard**: Prefix untrusted user strings with a single quote (\`'\`) before writing to CSV.
- **RFC Compatibility**: Complies with RFC 4180 CSV standard.

## 3. Package Registry Findings (PyPI)
- \`pytest\`: Standard offline unit test runner (zero external dependencies in \`python:3.11-slim\`).
- Runtime design: 100% Python standard library (\`csv\`, \`re\`, \`urllib.request\`, \`json\`, \`dataclasses\`).`,

            "task.log": `[2026-11-09 10:30:06.110] [ODIN] Scanning workspace AST using Graphify...
[2026-11-09 10:30:06.320] [GRAPHIFY] Indexed 52 modules, 118 symbols, 24 classes
[2026-11-09 10:30:06.340] [GRAPHIFY] Cached AST index to .state/graphify/stat-index.json
[2026-11-09 10:30:06.350] [GRAPHIFY] Found reusable symbols: tools/vault_infra.py:safe_write_markdown, MockCRMSink
[2026-11-09 10:30:06.500] [ODIN] Web search: 'spreadsheet formula injection mitigation python csv' (Tavily API)
[2026-11-09 10:30:07.120] [ODIN] HTTP 200: Tavily search returned 4 authoritative RFC security articles
[2026-11-09 10:30:07.150] [ODIN] Querying PyPI for pytest compatibility in python:3.11-slim
[2026-11-09 10:30:07.380] [ODIN] PyPI verified: pytest >= 7.4.0
[2026-11-09 10:30:07.450] [ODIN] Persisted research note: vault/research/research-lead-gateway.md
[2026-11-09 10:30:07.460] [ODIN] Research complete. Handoff to Taghi (Architecture) & Diba (UI/UX)...`
        },
        consoleLog: `[ODIN] Querying local Graphify knowledge graph... (52 modules, 118 symbols)
[ODIN] AST index cached: .state/graphify/stat-index.json
[ODIN] Web search: 'spreadsheet formula injection mitigation python csv' (Tavily API)
[ODIN] Verified RFC email regex and formula prefix defense standards.
[ODIN] Persisted Obsidian research: vault/research/research-lead-gateway.md
↳ Handoff to Taghi (Architecture) & Diba (UI/UX Product Design)...`
    },

    {
        step: 3,
        name: "3. Taghi & Diba",
        phase: "Step 3: Dual Technical & UI Specification",
        agent: "Taghi & Diba",
        leadPill: "📐 Taghi & Diba · Architects",
        color: "#d97706",
        pathFraction: 0.590,
        desc: "Taghi defines backend schemas, models, and a 4-phase Docker roadmap in <code>vault/specs/spec-lead-gateway.md</code>. Diba designs studio-grade Tailwind UI tokens ('Linear Dark Minimalist') and 5 interactive component states in <code>vault/specs/spec-lead-gateway-ui.md</code>. The living memory and SQLite ledger are updated.",
        metrics: [
            "Backend Spec: vault/specs/spec-lead-gateway.md",
            "UI Design Spec: vault/specs/spec-lead-gateway-ui.md",
            "Living Memory: PROJECT_PROFILE.md (Updated)",
            "Wikilinks: [[PROJECT_PROFILE]], [[spec-lead-gateway-ui]]",
            "Gate: [Y/enter] Architecture Approved"
        ],
        danaCritique: {
            verdict: "APPROVED",
            note: "Audit Gate 3: Dual-Spec verified: backend models strictly map to Diba's 5 interactive UI states."
        },
        files: [
            {
                dir: "vault/specs/",
                items: [
                    { name: "spec-lead-gateway.md", tag: "new", type: "spec", desc: "Taghi Backend Technical Architecture & Validation Phases" },
                    { name: "spec-lead-gateway-ui.md", tag: "new", type: "spec", desc: "Diba Studio-Grade UI Design Spec (Tailwind & 5 States)" }
                ]
            },
            {
                dir: "workspace/lead-gateway/",
                items: [
                    { name: "PROJECT_PROFILE.md", tag: "mod", type: "memory", desc: "Living Project Memory updated with verified schemas" }
                ]
            },
            {
                dir: ".state/",
                items: [
                    { name: "tasks.db", tag: "mod", type: "db", desc: "Status updated -> APPROVED_FOR_EXECUTION" },
                    { name: "task.log", tag: "mod", type: "log", desc: "Architecture proposal & developer approval record" }
                ]
            }
        ],
        artifacts: {
            "spec-lead-gateway.md": `---
title: Technical Specification — Lead Qualification Gateway
task_id: task-lead-gateway-20261109
project: lead-gateway
lead: taghi
status: approved
tags:
  - buildrelay
  - technical-spec
  - docker-phases
wikilinks:
  - "[[workspace/lead-gateway/PROJECT_PROFILE|Project Profile]]"
  - "[[vault/specs/spec-lead-gateway-ui|Diba UI Spec]]"
  - "[[vault/research/research-lead-gateway|Odin Research]]"
---

# Technical Specification: Lead Qualification Gateway

> **Author:** Taghi (Lead Architect)  
> **UI Partner:** [[vault/specs/spec-lead-gateway-ui|Diba UI Specification]]  
> **Status:** APPROVED BY DEVELOPER  

## 1. Phased Docker Execution Roadmap
1. **Phase 1: Ingestion & Validation Core**
   - Command: \`pytest tests/test_gateway.py\`
   - Deliverables: \`src/lead_gateway/validator.py\`, \`qualifier.py\`
2. **Phase 2: Batch CSV Import Utility & Sanitization**
   - Command: \`python scripts/import_leads.py --help\`
   - Deliverables: \`scripts/import_leads.py\`
3. **Phase 3: Responsive Tailwind Input Form**
   - Deliverables: \`form.html\` (Tailwind CSS, 5 interactive states)
4. **Phase 4: Tier 2 Live Verification Smoke Script**
   - Command: \`python scripts/verify_live.py\`
   - Deliverables: \`scripts/verify_live.py\`, \`README.md\`

## 2. Security Invariants
- Zero secrets hardcoded. Credentials loaded exclusively from \`.env\`.
- All CSV cell exports wrapped with \`sanitize_cell()\` (single quote prefix for \`=\`, \`+\`, \`-\`, \`@\`, \`|\`, \`%\`).`,

            "spec-lead-gateway-ui.md": `---
title: UI/UX Design Specification — Lead Gateway Web Form
task_id: task-lead-gateway-20261109
project: lead-gateway
lead: diba
archetype: "Linear Dark Minimalist"
tags:
  - buildrelay
  - ui-spec
  - tailwind
wikilinks:
  - "[[vault/specs/spec-lead-gateway|Taghi Backend Architecture]]"
  - "[[workspace/lead-gateway/PROJECT_PROFILE|Project Profile]]"
---

# UI/UX Design Specification: Lead Form

> **Author:** Diba (Product & UI Lead)  
> **Archetype:** 'Linear Dark Minimalist'  
> **Companion:** [[vault/specs/spec-lead-gateway|Taghi Technical Specification]]  

## 1. Studio-Grade Visual Design Tokens
- Canvas: Slate 900 (\`#0f172a\`), Panel: Slate 800 (\`#1e293b\`)
- Border: Slate 700 (\`#334155\`), Accent: Indigo 600 (\`#4f46e5\`), Ring: Indigo 500
- Typography: Inter font, 14px base, uppercase 12px tracking-wider field labels

## 2. The Five Interactive Component States
1. \`empty\`: Pristine form with placeholders and subtle focus rings.
2. \`validating\`: Real-time client email regex and budget range check.
3. \`submitting\`: Button loading spinner with disabled input elements.
4. \`success\`: Emerald confirmation banner (\`alert-banner\`) with inquiry ID.
5. \`error\`: Amber/Red inline validation error toasts.`,

            "PROJECT_PROFILE.md": `---
project_id: lead-gateway
created_at: 2026-11-09T10:30:00Z
updated_at: 2026-11-09T10:30:15Z
status: in_architecture
---

# Living Project Profile: lead-gateway

## 1. Active Schemas
- **LeadRecord**: \`name: str\`, \`email: str\`, \`phone: str\`, \`budget: float\`, \`company_size: int\`, \`tier: str\`
- **Budget Tiers**:
  - Enterprise: >= $50,000 or Size > 250
  - Mid-Market: $10,000 - $49,999 or Size 50 - 250
  - SMB: < $10,000

## 2. Planned Entry Surfaces
- **Web Form**: \`form.html\` (Tailwind CSS, 5 interactive states)
- **Batch CLI**: \`scripts/import_leads.py\` (CSV processing with sanitization)

## 3. Verification Commands
- **Tier 1 (Docker Sandbox)**: \`pytest tests/test_gateway.py\`
- **Tier 2 (Guided Live)**: \`python scripts/verify_live.py\``,

            "tasks.db": `-- SQLite Ledger Update: .state/tasks.db
UPDATE tasks SET 
    status = 'APPROVED_FOR_EXECUTION',
    current_lead = 'meti',
    updated_at = CURRENT_TIMESTAMP
WHERE task_id = 'task-lead-gateway-20261109';`,

            "task.log": `[2026-11-09 10:30:07.500] [TAGHI] Generating backend technical spec: vault/specs/spec-lead-gateway.md
[2026-11-09 10:30:07.820] [DIBA] Generating UI/UX design spec: vault/specs/spec-lead-gateway-ui.md (Linear Dark Minimalist)
[2026-11-09 10:30:08.100] [MEMORY] Updating living profile: workspace/lead-gateway/PROJECT_PROFILE.md
[2026-11-09 10:30:08.150] [GATE] Presenting Architecture Approval Gate to developer...
[2026-11-09 10:30:10.420] [GATE] Developer action: [Y/enter] APPROVED
[2026-11-09 10:30:10.440] [LEDGER] .state/tasks.db updated: status='APPROVED_FOR_EXECUTION', current_lead='meti'
[2026-11-09 10:30:10.450] [ROUTING] Awakening Meti for containerized Docker execution...`
        },
        consoleLog: `╭─────────────────── 📐 Taghi Architectural Design Proposal ───────────────────╮
│  Architecture Overview: Modular Python pipeline for lead qualification       │
│  UI Archetype:          Linear Dark Minimalist (Diba)                        │
│  Execution Phases:      1. Core  2. CSV Batch  3. Web UI  4. Live Smoke      │
│  Base Docker Image:     python:3.11-slim                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
👉 Architecture Approval Action: [Y/enter] Approve Architecture & Begin Coding
↳ Developer approved. Meti awakened for containerized execution.`
    },

    {
        step: 4,
        name: "4. Meti",
        phase: "Step 4: Phased Docker Sandbox Execution",
        agent: "Meti",
        leadPill: "🔨 Meti · Implementer",
        color: "#059669",
        pathFraction: 0.795,
        desc: "Meti spawns an isolated Docker container (<code>python:3.11-slim</code>) mounting only <code>workspace/lead-gateway/</code>. He writes core modules, batch CSV tools, Tailwind form.html, and executes unit tests across all 4 phases within a strict 3-attempt validation budget.",
        metrics: [
            "Container: python:3.11-slim (Isolated)",
            "Phases Executed: 4 / 4 PASSED",
            "Unit Tests: 6 Passed, 0 Leaks",
            "Deliverable Code: workspace/lead-gateway/",
            "Code Review: vault/code-reviews/review-lead-gateway.md"
        ],
        danaCritique: {
            verdict: "APPROVED",
            note: "Audit Gate 4: Docker sandbox verified: 6/6 unit tests passed with 0 mock leaks. Code review logged."
        },
        files: [
            {
                dir: "workspace/lead-gateway/",
                items: [
                    { name: "form.html", tag: "new", type: "code", desc: "Tailwind CSS Responsive Web Input Form (5 States)" },
                    { name: "src/lead_gateway/validator.py", tag: "new", type: "code", desc: "RFC Email & Formula Sanitization Logic" },
                    { name: "src/lead_gateway/qualifier.py", tag: "new", type: "code", desc: "Budget Tiering Engine & Mock CRM Sinks" },
                    { name: "tests/test_gateway.py", tag: "new", type: "code", desc: "Offline Deterministic Unit Tests" },
                    { name: "scripts/import_leads.py", tag: "new", type: "code", desc: "Batch CSV Lead Ingestion CLI Utility" },
                    { name: "scripts/verify_live.py", tag: "new", type: "code", desc: "Tier 2 Guided Live Verification Smoke Test" },
                    { name: ".env.example", tag: "new", type: "config", desc: "Environment Configuration Template" },
                    { name: "README.md", tag: "new", type: "doc", desc: "Run Commands & Live Verification Checklist" }
                ]
            },
            {
                dir: "vault/code-reviews/",
                items: [
                    { name: "review-lead-gateway.md", tag: "new", type: "obsidian", desc: "Obsidian Docker Sandbox Execution & Checkpoint Report" }
                ]
            },
            {
                dir: ".state/",
                items: [
                    { name: "task.log", tag: "mod", type: "log", desc: "Docker subprocess logs & pytest stdout stream" }
                ]
            }
        ],
        artifacts: {
            "src/lead_gateway/validator.py": `import re
from typing import Any

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\\+?[0-9\\s\\-()]{7,20}$")

def sanitize_cell(value: Any) -> str:
    """Sanitize spreadsheet formula injection triggers (=, +, -, @, |, %)."""
    s = str(value)
    if s.startswith(('=', '+', '-', '@', '|', '%', '\\t', '\\r')):
        return "'" + str(s)
    return s

def validate_lead(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("name", "")).strip()
    if not name:
        raise ValueError("Lead 'name' is required.")
    email = str(data.get("email", "")).strip()
    if not EMAIL_REGEX.match(email):
        raise ValueError(f"Invalid email address: {email}")
    return {
        "name": sanitize_cell(name),
        "email": sanitize_cell(email),
        "budget": float(data.get("budget", 0)),
        "company_size": int(data.get("company_size", 1))
    }`,

            "tests/test_gateway.py": `import pytest
from unittest.mock import MagicMock
from lead_gateway.validator import sanitize_cell, validate_lead
from lead_gateway.qualifier import qualify_lead, MockCRMSink

def test_sanitize_cell():
    assert sanitize_cell("=1+1") == "'=1+1"
    assert sanitize_cell("@SUM") == "'@SUM"
    assert sanitize_cell("-100") == "'-100"
    assert sanitize_cell("Alice Smith") == "Alice Smith"

def test_validate_lead_valid():
    lead = validate_lead({"name": "=Evil Corp", "email": "admin@evil.com", "budget": "60000"})
    assert lead["name"] == "'=Evil Corp"
    assert lead["budget"] == 60000.0

def test_validate_lead_invalid_email():
    with pytest.raises(ValueError, match="Invalid email"):
        validate_lead({"name": "Bob", "email": "not-an-email"})

def test_qualify_lead_enterprise():
    mock_sink = MockCRMSink()
    res = qualify_lead({"budget": 60000, "company_size": 300}, sink=mock_sink)
    assert res["tier"] == "Enterprise"
    assert res["dispatched"] is True`,

            "form.html": `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Customer Inquiry Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white min-h-screen flex items-center justify-center p-4">
    <div class="max-w-xl w-full bg-slate-800 rounded-xl p-8 border border-slate-700 shadow-2xl">
        <h1 class="text-2xl font-bold mb-2">Lead Qualification Gateway</h1>
        <p class="text-slate-400 text-sm mb-6">Linear Dark Minimalist UI · High-contrast validation</p>
        <div id="alert-banner" class="hidden mb-4 p-3 rounded text-sm font-medium"></div>
        <form class="space-y-4" onsubmit="return submitForm(event)">
            <div>
                <label class="block text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Full Name</label>
                <input type="text" id="name" required placeholder="Jane Doe" class="w-full p-2.5 bg-slate-900 rounded border border-slate-700 text-white focus:ring-2 focus:ring-indigo-500">
            </div>
            <div>
                <label class="block text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Work Email</label>
                <input type="email" id="email" required placeholder="jane@company.com" class="w-full p-2.5 bg-slate-900 rounded border border-slate-700 text-white focus:ring-2 focus:ring-indigo-500">
            </div>
            <button type="submit" id="btn-submit" class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded font-bold transition">Submit Inquiry</button>
        </form>
    </div>
</body>
</html>`,

            "review-lead-gateway.md": `---
title: Meti Code Review & Container Checkpoint
task_id: task-lead-gateway-20261109
lead: meti
container: python:3.11-slim
status: verified
tags:
  - buildrelay
  - code-review
  - docker-verification
wikilinks:
  - "[[vault/specs/spec-lead-gateway|Taghi Spec]]"
  - "[[vault/specs/spec-lead-gateway-ui|Diba UI Spec]]"
---

# Code Review: Lead Qualification Gateway

> **Author:** Meti (Implementer)  
> **Container:** \`python:3.11-slim\`  
> **Status:** ALL 4 PHASES PASSED  

## Phase Execution Summary
- **Phase 1 (Core Validator)**: \`pytest tests/test_gateway.py\` → PASSED (6/6 tests in 0.42s)
- **Phase 2 (CSV CLI)**: \`python scripts/import_leads.py --help\` → PASSED (Exit code 0)
- **Phase 3 (Web UI)**: \`form.html\` verified against Diba's 5 interactive states.
- **Phase 4 (Live Smoke)**: \`python scripts/verify_live.py\` prepared with \`.env.example\`.`,

            "task.log": `[2026-11-09 10:30:10.500] [METI] Spawning Docker sandbox: image='python:3.11-slim'
[2026-11-09 10:30:10.510] [DOCKER] Mounting /workspace/lead-gateway to /workspace inside container
[2026-11-09 10:30:11.200] [DOCKER] Container c8f219b online with 0 host network access
[2026-11-09 10:30:11.250] [METI] Implementing src/lead_gateway/validator.py and qualifier.py...
[2026-11-09 10:30:11.890] [METI] Executing Phase 1: pytest tests/test_gateway.py
[2026-11-09 10:30:12.350] [DOCKER] pytest stdout: 6 passed in 0.42s
[2026-11-09 10:30:12.360] [METI] Phase 1 PASSED on Attempt 1.
[2026-11-09 10:30:12.400] [METI] Implementing Phase 2: scripts/import_leads.py...
[2026-11-09 10:30:12.750] [DOCKER] Executing: python scripts/import_leads.py --help → Exit Code: 0
[2026-11-09 10:30:12.760] [METI] Phase 2 PASSED on Attempt 1.
[2026-11-09 10:30:12.800] [METI] Implementing Phase 3: form.html (Diba UI spec)...
[2026-11-09 10:30:13.100] [METI] Phase 3 PASSED: 5 states verified.
[2026-11-09 10:30:13.150] [METI] Implementing Phase 4: scripts/verify_live.py & README.md...
[2026-11-09 10:30:13.400] [METI] Phase 4 PASSED.
[2026-11-09 10:30:13.450] [METI] Persisting code review: vault/code-reviews/review-lead-gateway.md
[2026-11-09 10:30:13.500] [DOCKER] Stopping container c8f219b... done.`
        },
        consoleLog: `🔨 METI (Phased Docker Execution)
Executing verified pipeline phases in isolated container python:3.11-slim:
  [Phase 1] pytest tests/test_gateway.py          → ✅ PASSED (6 passed in 0.42s)
  [Phase 2] python scripts/import_leads.py --help → ✅ PASSED (Exit Code: 0)
  [Phase 3] verify form.html validation syntax   → ✅ PASSED (Tailwind CDN)
  [Phase 4] scripts/verify_live.py smoke test     → ✅ PASSED
↳ Persisted Obsidian code review: vault/code-reviews/review-lead-gateway.md`
    },

    {
        step: 5,
        name: "5. Deliverable",
        phase: "Step 5: Verified Deliverable & Scorecard Gate",
        agent: "Dana & Delivery",
        leadPill: "✨ Verified Deliverable",
        color: "#ea580c",
        pathFraction: 1.0,
        desc: "Dana Quality Supervisor runs <code>tools/eval_harness.py</code>, awarding a 100/100 EXCEPTIONAL quantitative score across 5 engineering dimensions. The delivery gate presents milestone choices ([1] Iterate, [3] Project REPL), the SQLite ledger marks COMPLETED, and the atomic mutex lock is safely released.",
        metrics: [
            "Overall Score: 100 / 100 (EXCEPTIONAL)",
            "Test Integrity: 20/20 · Security: 20/20",
            "UI Surface: 20/20 · Live Verify: 20/20",
            "Task Ledger Status: COMPLETED",
            "Lock Status: RELEASED"
        ],
        danaCritique: {
            verdict: "100/100 EXCEPTIONAL",
            note: "Delivery Scorecard Verified: All 5 dimensions passed with Exceptional verdict. Concurrency lock released."
        },
        files: [
            {
                dir: "vault/evaluations/",
                items: [
                    { name: "eval-lead-gateway.md", tag: "new", type: "eval", desc: "5-Dimension Quantitative Scorecard (100/100)" }
                ]
            },
            {
                dir: "vault/supervision/",
                items: [
                    { name: "supervision-lead-gateway.md", tag: "new", type: "audit", desc: "Dana Quality Supervisor Audit Note with Wikilinks" }
                ]
            },
            {
                dir: ".state/",
                items: [
                    { name: "tasks.db", tag: "mod", type: "db", desc: "Task Ledger Status updated -> COMPLETED" },
                    { name: "task-lead-gateway.lock", tag: "del", type: "lock", desc: "Atomic Concurrency Mutex Lock Released" },
                    { name: "task.log", tag: "mod", type: "log", desc: "Final evaluation logs & delivery completion summary" }
                ]
            }
        ],
        artifacts: {
            "eval-lead-gateway.md": `---
title: Deliverable Evaluation Report — lead-gateway
task_id: task-lead-gateway-20261109
evaluator: tools/eval_harness.py
verdict: EXCEPTIONAL
overall_score: 100
tags:
  - buildrelay
  - evaluation
  - scorecard
wikilinks:
  - "[[vault/code-reviews/review-lead-gateway|Meti Review]]"
  - "[[workspace/lead-gateway/PROJECT_PROFILE|Project Profile]]"
---

# Deliverable Evaluation Report: lead-gateway

> **Evaluator:** \`tools/eval_harness.py\`  
> **Overall Score:** 100 / 100  
> **Verdict:** EXCEPTIONAL  

## Dimension Scorecard
| Dimension | Score | Status | Findings |
| :--- | :---: | :---: | :--- |
| 1. Test Integrity & Coverage | 20 / 20 | EXCELLENT | 6 non-trivial assertions, pytest.raises edge cases, mock adapters |
| 2. Security & Sanitization | 20 / 20 | EXCELLENT | Cell prefix sanitization (=, +, -, @), .env in .gitignore |
| 3. UI Surface & Usability | 20 / 20 | EXCELLENT | Responsive Tailwind CSS form, client validation, alert feedback |
| 4. Tier 2 Live Verification | 20 / 20 | EXCELLENT | scripts/verify_live.py decoupled with .env, numbered README checklist |
| 5. Architecture & Hygiene | 20 / 20 | EXCELLENT | Clean separation of concerns, living PROJECT_PROFILE.md memory |`,

            "supervision-lead-gateway.md": `---
title: Dana Quality Supervisor Audit Note
task_id: task-lead-gateway-20261109
supervisor: dana
verdict: APPROVED
score: 100
tags:
  - buildrelay
  - supervision
  - dana-critique
wikilinks:
  - "[[vault/evaluations/eval-lead-gateway|Evaluation Report]]"
  - "[[vault/specs/spec-lead-gateway|Taghi Spec]]"
---

# Dana Quality Supervisor Audit Note

- **Supervised Lead:** Meti (Final Delivery)
- **Verdict:** APPROVED
- **Score:** 100 / 100
- **Assessment:** Deliverable meets all architectural contracts, contains comprehensive offline mock coverage, and adheres to strict formula injection sanitization.`,

            "tasks.db": `-- Final Task State in .state/tasks.db
UPDATE tasks SET 
    status = 'COMPLETED',
    updated_at = CURRENT_TIMESTAMP
WHERE task_id = 'task-lead-gateway-20261109';

SELECT task_id, status, route, updated_at FROM tasks 
WHERE task_id = 'task-lead-gateway-20261109';

/* Result Query Output:
task_id                     | status    | route        | updated_at
task-lead-gateway-20261109  | COMPLETED | ARCHITECTURE | 2026-11-09 10:30:45
*/`,

            "task-lead-gateway.lock": `# Atomic Concurrency Mutex Lock: .state/task-lead-gateway.lock
# STATUS: RELEASED AT 2026-11-09T10:30:45Z
# File safely unlinked to permit subsequent project sessions or feature iterations.`,

            "task.log": `[2026-11-09 10:30:13.600] [DANA] Running deliverable evaluation harness (tools/eval_harness.py)...
[2026-11-09 10:30:13.910] [EVAL] Dimension 1 (Test Integrity): 20/20
[2026-11-09 10:30:13.920] [EVAL] Dimension 2 (Security & Sanitization): 20/20
[2026-11-09 10:30:13.930] [EVAL] Dimension 3 (UI Surface & Usability): 20/20
[2026-11-09 10:30:13.940] [EVAL] Dimension 4 (Tier 2 Live Verification): 20/20
[2026-11-09 10:30:13.950] [EVAL] Dimension 5 (Architecture & Hygiene): 20/20
[2026-11-09 10:30:13.960] [EVAL] Total Score: 100/100 (Verdict: EXCEPTIONAL)
[2026-11-09 10:30:14.020] [LEDGER] Updating .state/tasks.db: status='COMPLETED'
[2026-11-09 10:30:14.050] [MUTEX] Releasing concurrency lock: .state/task-lead-gateway.lock
[2026-11-09 10:30:14.060] [MUTEX] Lock released cleanly.
[2026-11-09 10:30:14.100] [DELIVERY] Delivery gate presented. Task completed in 14.0 seconds.`
        },
        consoleLog: `╭──────────────────── 🏁 Delivery Gate — Milestone Ready ─────────────────────╮
│  Task ID:          task-lead-gateway-20261109                               │
│  Result:           🌟 EXCEPTIONAL (100 / 100)                                │
│  Web Entry:        form.html (Tailwind CSS, Client Validation)               │
│  Batch CLI:        scripts/import_leads.py                                   │
│  Tier 1 Tests:     tests/test_gateway.py (Passed in Docker)                  │
│  Tier 2 Smoke:     scripts/verify_live.py (Env decoupled)                    │
╰──────────────────────────────────────────────────────────────────────────────╯
👉 Delivery Action:
   [Y/enter] Accept Deliverable & Release Lock
   [1] Add Next Feature Milestone
   [3] Open Interactive Project REPL (buildrelay session lead-gateway)
↳ Task complete. All stage artifacts archived in vault/. Mutex lock released.`
    }
];

// Global Application Loop State
let currentStepIndex = 0;
let selectedFile = "tasks.db";
let customFileSelected = false;

// Loop Timing Cadence
const STEP_DWELL_MS = 3800; // Time spent focused on each step
const RETURN_DWELL_MS = 1400; // Return loop speed
let stepStartTime = performance.now();
let isReturnLooping = false;

// DOM Elements
const stepChips = document.querySelectorAll(".step-chip");
const scrubberFill = document.getElementById("scrubber-progress-fill");
const headerTimerFill = document.getElementById("header-timer-fill");
const headerCycleStatus = document.getElementById("header-cycle-status");

// SVG Canvas Elements
const streamPath = document.getElementById("pipeline-stream-active");
const returnPath = document.getElementById("pipeline-stream-loop");
const travelingOrb = document.getElementById("traveling-orb");
const travelingOrbSpark = document.getElementById("traveling-orb-spark");
const agentNodes = document.querySelectorAll(".agent-node-group");

// Explainer Card Elements
const stageLeadPill = document.getElementById("stage-lead-pill");
const stagePhaseName = document.getElementById("stage-phase-name");
const stageExplanation = document.getElementById("stage-explanation");
const stageMetricRibbon = document.getElementById("stage-metric-ribbon");
const danaAuditVerdict = document.getElementById("dana-audit-verdict");
const danaAuditNote = document.getElementById("dana-audit-note");

// Product System Elements
const reactiveTreeScroll = document.getElementById("reactive-tree-scroll");
const chamberFilename = document.getElementById("chamber-filename");
const chamberBadge = document.getElementById("chamber-badge");
const chamberFileGlyph = document.getElementById("chamber-file-glyph");
const chamberCodePreview = document.getElementById("chamber-code-preview");
const liveConsoleStream = document.getElementById("live-console-stream");

// View Toggle Elements
const viewTreeBtn = document.getElementById("view-tree-btn");
const viewLogBtn = document.getElementById("view-log-btn");
const treeViewPanel = document.getElementById("tree-view-panel");
const logViewPanel = document.getElementById("log-view-panel");

// Path Geometry Calculations
let pathTotalLength = 0;
let returnPathTotalLength = 0;

if (streamPath && streamPath.getTotalLength) {
    pathTotalLength = streamPath.getTotalLength();
}
if (returnPath && returnPath.getTotalLength) {
    returnPathTotalLength = returnPath.getTotalLength();
}

/**
 * Continuous RequestAnimationFrame Loop
 */
function animationTick(now) {
    const elapsedInStep = now - stepStartTime;
    const dwell = isReturnLooping ? RETURN_DWELL_MS : STEP_DWELL_MS;
    const stepProgress = Math.min(1, elapsedInStep / dwell);

    if (!isReturnLooping) {
        // Forward progression along main stream path
        const currentFraction = STAGES[currentStepIndex].pathFraction;
        const nextFraction = currentStepIndex < 5 ? STAGES[currentStepIndex + 1].pathFraction : 1.0;
        const currentInterp = currentFraction + (nextFraction - currentFraction) * stepProgress;
        
        // Move traveling orb along the bezier path
        if (streamPath && pathTotalLength > 0) {
            const point = streamPath.getPointAtLength(currentInterp * pathTotalLength);
            setOrbPosition(point.x, point.y, STAGES[currentStepIndex].color);
        }

        // Update progress bars
        const overallProgressPercent = ((currentStepIndex + stepProgress) / 6) * 100;
        scrubberFill.style.width = `${overallProgressPercent}%`;
        headerTimerFill.style.width = `${(stepProgress) * 100}%`;

        // Check for stage advancement
        if (elapsedInStep >= dwell) {
            if (currentStepIndex < 5) {
                activateStage(currentStepIndex + 1);
            } else {
                // Begin return loop
                isReturnLooping = true;
                stepStartTime = now;
                headerCycleStatus.textContent = "Recycling Loop ↺";
            }
        }
    } else {
        // Orb traveling smoothly along return cosmic arc back to top
        if (returnPath && returnPathTotalLength > 0) {
            const point = returnPath.getPointAtLength(stepProgress * returnPathTotalLength);
            setOrbPosition(point.x, point.y, "#6366f1");
        }
        headerTimerFill.style.width = `${(1 - stepProgress) * 100}%`;

        if (elapsedInStep >= dwell) {
            isReturnLooping = false;
            headerCycleStatus.textContent = "Continuous Loop Active";
            activateStage(0);
        }
    }

    requestAnimationFrame(animationTick);
}

function setOrbPosition(x, y, color) {
    if (travelingOrb) {
        travelingOrb.setAttribute("cx", x);
        travelingOrb.setAttribute("cy", y);
        travelingOrb.style.fill = color;
    }
    if (travelingOrbSpark) {
        travelingOrbSpark.setAttribute("cx", x);
        travelingOrbSpark.setAttribute("cy", y);
    }
}

/**
 * Stage Activator
 */
function activateStage(stepIndex, isUserManualJump = false) {
    currentStepIndex = Math.max(0, Math.min(5, stepIndex));
    const stage = STAGES[currentStepIndex];
    stepStartTime = performance.now();
    isReturnLooping = false;

    // 1. Update Chips
    stepChips.forEach((chip, idx) => {
        chip.classList.toggle("active", idx === currentStepIndex);
    });

    // 2. Update SVG Nodes
    agentNodes.forEach((node, idx) => {
        node.classList.toggle("active", idx === currentStepIndex);
    });

    // 3. Update Stage Detail Card
    stageLeadPill.textContent = stage.leadPill;
    stageLeadPill.style.color = stage.color;
    stageLeadPill.style.borderColor = `${stage.color}40`;
    stageLeadPill.style.backgroundColor = `${stage.color}12`;
    
    stagePhaseName.textContent = stage.phase;
    stageExplanation.innerHTML = stage.desc;

    stageMetricRibbon.innerHTML = stage.metrics
        .map(m => `<span class="metric-chip">${m}</span>`)
        .join("");

    // Update Dana Supervisory Audit Banner
    if (stage.danaCritique && danaAuditVerdict && danaAuditNote) {
        danaAuditVerdict.textContent = stage.danaCritique.verdict;
        danaAuditNote.textContent = stage.danaCritique.note;
        if (stage.danaCritique.verdict.includes("100")) {
            danaAuditVerdict.style.backgroundColor = "#ea580c";
        } else if (stage.danaCritique.verdict === "OBSERVING") {
            danaAuditVerdict.style.backgroundColor = "#64748b";
        } else {
            danaAuditVerdict.style.backgroundColor = "#4f46e5";
        }
    }

    // 4. Update Product Tree
    renderReactiveTree(stage);

    // 5. Update Live Console Stream
    liveConsoleStream.textContent = stage.consoleLog;

    // 6. Instantly snap orb position if manual jump
    if (isUserManualJump && streamPath && pathTotalLength > 0) {
        const point = streamPath.getPointAtLength(stage.pathFraction * pathTotalLength);
        setOrbPosition(point.x, point.y, stage.color);
        scrubberFill.style.width = `${(currentStepIndex / 6) * 100}%`;
        headerTimerFill.style.width = "0%";
    }
}

/**
 * Render reactive directory tree for the active step
 */
function renderReactiveTree(stage) {
    reactiveTreeScroll.innerHTML = "";
    let primaryFile = null;

    stage.files.forEach(folder => {
        const folderBlock = document.createElement("div");
        folderBlock.className = "tree-folder-block";

        const folderTitle = document.createElement("div");
        folderTitle.className = "folder-title";
        folderTitle.innerHTML = `<span>📂</span> <span>${folder.dir}</span>`;
        folderBlock.appendChild(folderTitle);

        folder.items.forEach(file => {
            const fileRow = document.createElement("div");
            fileRow.className = "tree-node-file";
            
            if (file.name === selectedFile) {
                fileRow.classList.add("selected");
            }

            if (!primaryFile && (file.tag === "new" || file.tag === "mod")) {
                primaryFile = file.name;
            }

            let glyph = "📄";
            if (file.type === "db") glyph = "🗄️";
            if (file.type === "lock") glyph = "🔒";
            if (file.type === "log") glyph = "📜";
            if (file.type === "spec") glyph = "📐";
            if (file.type === "code") glyph = "💻";
            if (file.type === "eval") glyph = "📊";
            if (file.type === "memory") glyph = "🧠";
            if (file.type === "graphify") glyph = "🕸️";
            if (file.type === "obsidian") glyph = "📓";
            if (file.type === "audit") glyph = "⚖️";
            if (file.type === "config") glyph = "⚙️";

            let tagHtml = "";
            if (file.tag === "new") {
                tagHtml = `<span class="file-status-badge badge-new">+ Created</span>`;
            } else if (file.tag === "mod") {
                tagHtml = `<span class="file-status-badge badge-mod">● Updated</span>`;
            } else if (file.tag === "del") {
                tagHtml = `<span class="file-status-badge" style="background:#fef2f2;color:#ef4444">Released</span>`;
            }

            fileRow.innerHTML = `
                <div class="file-info-group">
                    <span>${glyph}</span>
                    <span>${file.name}</span>
                </div>
                ${tagHtml}
            `;

            fileRow.addEventListener("click", () => {
                customFileSelected = true;
                selectFileInChamber(file.name, glyph, file.desc);
            });

            folderBlock.appendChild(fileRow);
        });

        reactiveTreeScroll.appendChild(folderBlock);
    });

    // Auto-display primary file unless user clicked a specific one
    if (!customFileSelected && primaryFile && stage.artifacts[primaryFile]) {
        selectFileInChamber(primaryFile, "📄", "Newly Generated Artifact");
    } else if (stage.artifacts[selectedFile]) {
        renderChamberPreview(selectedFile);
    } else {
        const fallback = Object.keys(stage.artifacts)[0];
        if (fallback) {
            selectFileInChamber(fallback, "📄", "Active Step Deliverable");
        }
    }
}

/**
 * Select file to inspect in the chamber
 */
function selectFileInChamber(filename, glyph = "📄", badge = "Artifact") {
    selectedFile = filename;
    document.querySelectorAll(".tree-node-file").forEach(el => {
        el.classList.toggle("selected", el.textContent.includes(filename));
    });

    chamberFilename.textContent = filename;
    chamberFileGlyph.textContent = glyph;
    chamberBadge.textContent = badge;
    renderChamberPreview(filename);
}

/**
 * Render artifact code/markdown in the chamber
 */
function renderChamberPreview(filename) {
    const stage = STAGES[currentStepIndex];
    const code = stage.artifacts[filename] || `// ${filename} is maintained in workspace.\n// Active in Step ${currentStepIndex}.`;
    chamberCodePreview.textContent = code;
}

/**
 * User Click Listeners for direct seeking
 */
stepChips.forEach(chip => {
    chip.addEventListener("click", () => {
        const step = parseInt(chip.dataset.step, 10);
        activateStage(step, true);
    });
});

agentNodes.forEach(node => {
    node.addEventListener("click", () => {
        const step = parseInt(node.dataset.step, 10);
        activateStage(step, true);
    });
});

// View Toggle between Tree & Log
viewTreeBtn.addEventListener("click", () => {
    viewTreeBtn.classList.add("active");
    viewLogBtn.classList.remove("active");
    treeViewPanel.classList.remove("hidden");
    logViewPanel.classList.add("hidden");
});

viewLogBtn.addEventListener("click", () => {
    viewLogBtn.classList.add("active");
    viewTreeBtn.classList.remove("active");
    logViewPanel.classList.remove("hidden");
    treeViewPanel.classList.add("hidden");
});

// Start the continuous loop on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    activateStage(0);
    requestAnimationFrame(animationTick);
});

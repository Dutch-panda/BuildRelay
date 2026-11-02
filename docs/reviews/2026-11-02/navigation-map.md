# Navigation and generation map

## Before

- GET STARTED: introduction, quickstart, terminal example.
- USE BUILDRELAY: workflow, configuration, execution, projects, sessions/verify/preview, resume.
- INSPECT & VERIFY: quality, architecture, testing, limitations, troubleshooting.

Original source ownership: README sections supplied 12 technical guides; introduction and example templates were embedded in the builder. See source-map-before.json.

## After

### GET STARTED

- `docs/content/index.md` → `docs/index.html` — Introduction
- `docs/content/task-fit.md` → `docs/task-fit.html` — Task fit
- `docs/content/quickstart.md` → `docs/quickstart.html` — Quick start

### WORK ON A PROJECT

- `docs/content/workflow.md` → `docs/workflow.html` — Workflow & alignment
- `docs/content/projects.md` → `docs/projects.html` — Projects & memory
- `docs/content/resume.md` → `docs/resume.html` — Resume a task
- `docs/content/project-tools.md` → `docs/project-tools.html` — Sessions, verify & preview

### REFERENCE

- `docs/content/configuration.md` → `docs/configuration.html` — Models & configuration
- `docs/content/commands.md` → `docs/commands.html` — Command boundaries
- `docs/content/execution.md` → `docs/execution.html` — Execution & web research
- `docs/content/troubleshooting.md` → `docs/troubleshooting.html` — Troubleshooting

### INSPECT THE EVIDENCE

- `docs/content/example.md` → `docs/example.html` — Historical terminal capture
- `docs/content/showcase.md` → `docs/showcase.html` — Showcase (pending)
- `docs/content/quality.md` → `docs/quality.html` — Supervision & evaluation
- `docs/content/testing.md` → `docs/testing.html` — Testing & integration

### UNDERSTAND THE DESIGN

- `docs/content/architecture.md` → `docs/architecture.html` — Architecture
- `docs/content/design.md` → `docs/design.html` — Design rationale (proposed)
- `docs/content/limitations.md` → `docs/limitations.html` — Limits & security

All original 14 HTML paths and preflight IDs are retained. New pages: task-fit, commands, design, showcase. Canonical sources and ownership exceptions are described in docs/content/README.md. The generator writes 18 HTML files and README's marked version span only.

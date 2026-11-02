# Changed files and rationale

## Entry point / metadata

- README.md: short product guide, first-run path, task-fit/boundaries, evidence labels, maintained references and legacy anchors.
- LICENSE and pyproject.toml: owner-selected MIT and package metadata; existing version unchanged.

## Maintained guides / generated output

- docs/content/*.md: full extracted reference, introduction/historical example sources, canonical command table, task-fit, proposed rationale and blocked showcase.
- scripts/build_docs.py: shared 18-page navigation/mapping, metadata/version, relative/source links, unique heading IDs, deterministic output.
- docs/*.html: regenerated site; original 14 URLs preserved and four guides added.
- docs/site.css and docs/site.js: copy controls with actual success/error feedback, keyboard scrolling/focus, native menu focus retention and image enlargement links.

## Tests / review

- tests/test_documentation.py: isolated build, version/license, assets/links, old anchors, unique headings, SVG XML and deterministic outputs.
- docs/reviews/2026-11-02/*: before/after outlines, navigation/source maps, claims matrix, contrast calculations, QA blockers and final review.

## Explicit implementation inventory

- `LICENSE`
- `README.md`
- `pyproject.toml`
- `scripts/build_docs.py`
- `tests/test_documentation.py`
- `docs/site.css`
- `docs/site.js`
- `docs/content/README.md`
- `docs/content/architecture.md`
- `docs/content/commands.md`
- `docs/content/configuration.md`
- `docs/content/design.md`
- `docs/content/example.md`
- `docs/content/execution.md`
- `docs/content/index.md`
- `docs/content/limitations.md`
- `docs/content/project-tools.md`
- `docs/content/projects.md`
- `docs/content/quality.md`
- `docs/content/quickstart.md`
- `docs/content/resume.md`
- `docs/content/showcase.md`
- `docs/content/task-fit.md`
- `docs/content/testing.md`
- `docs/content/troubleshooting.md`
- `docs/content/workflow.md`
- `docs/architecture.html`
- `docs/commands.html`
- `docs/configuration.html`
- `docs/design.html`
- `docs/example.html`
- `docs/execution.html`
- `docs/index.html`
- `docs/limitations.html`
- `docs/project-tools.html`
- `docs/projects.html`
- `docs/quality.html`
- `docs/quickstart.html`
- `docs/resume.html`
- `docs/showcase.html`
- `docs/task-fit.html`
- `docs/testing.html`
- `docs/troubleshooting.html`
- `docs/workflow.html`

Unrelated dirty `.gitignore` and `vault/Untitled.base` were preserved. Runtime agent/CLI/provider code, diagrams and brand assets were not changed by this reapplication. Earlier unverified benchmark material remains separate and must not be published as authentic model-run evidence without provenance review.

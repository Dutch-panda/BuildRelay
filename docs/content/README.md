# Documentation source ownership

The README is the concise repository entry point; `docs/content/*.md` is the maintained manual. Shared `GROUPS` metadata in `scripts/build_docs.py` defines titles, navigation and source-to-page mapping. Do not edit generated HTML as the only fix.

```bash
python scripts/build_docs.py
```

The existing Rich dependency supplies markdown-it-py. No framework/service or runtime dependency is added. `pyproject.toml` supplies version metadata; the builder updates only README's marked version span. Other README content stays hand-maintained.

## Source-to-page and navigation map

Each basename maps `docs/content/<name>.md` → `docs/<name>.html`:

- GET STARTED: `index`, `task-fit`, `quickstart`.
- WORK ON A PROJECT: `workflow`, `projects`, `resume`, `project-tools`.
- REFERENCE: `configuration`, `commands`, `execution`, `troubleshooting`.
- INSPECT THE EVIDENCE: `example`, `showcase`, `quality`, `testing`.
- UNDERSTAND THE DESIGN: `architecture`, `design`, `limitations`.

The builder writes these 18 HTML pages and README's marked version only. All original 14 page URLs remain; onward anchors preserve moved sections. Source Markdown links work in a clone/GitHub; guide links map to HTML on Pages, repository-code links to GitHub, and assets remain relative to `/BuildRelay/`.

`example.md` includes the unchanged public transcript through `{{TERMINAL_TRANSCRIPT}}`. It does not rerun or relabel that historical output. `docs/site.css` and `docs/site.js` are hand-maintained UI sources; SVGs under `docs/diagrams/` and `docs/brand/` remain editable assets. `docs/brand/README.md` is a separate brand reference. Reviews under `docs/reviews/` record verification/decisions, not app evidence.

The generator performs no deployment, model calls, credential reads or live verification. Run the documentation regression tests and rebuild twice to check determinism.

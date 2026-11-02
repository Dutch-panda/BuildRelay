# BuildRelay documentation implementation review

Status: **reapplied locally, ready for review; evidence and rendered QA incomplete**. Owner explicitly requested reapplication after an external reset and selected MIT. Date: 2 November 2026. Baseline: `cffdc70` on `main`. Package/runtime version remains **0.2.0**. Repository identity follows the local package, README, CLI and existing Pages URLs; no remote settings were queried or changed.

The linked audit `../website/buildrelay-review/REPORT.md` is outside this authorized repository and was not accessed. The supplied handoff was treated as the audit snapshot, revalidated against HEAD. The later benchmark implementation discussed elsewhere in this conversation is not in this HEAD; it is not described as an installed CLI feature.

## Delivered content and source ownership

The README now follows: purpose/category → reader/task fit → one setup/task path → inspect outputs → resume/iterate → critical boundaries → maintained references → maintenance/reuse. Full technical sections were extracted before shortening it. Detailed configuration, agent roles, flags, diagnostics, diagrams, testing and brand references retain maintained Markdown destinations. Original additional task examples were kept in configuration reference.

`docs/content/*.md` is the full manual. The introduction and historical example also have source files instead of embedded narrative alone. Shared `GROUPS` metadata in the builder defines titles/navigation/page mapping. The generator owns canonical/source links, heading IDs, package-derived version and the marked README version span. It generates 18 HTML pages without executing examples or publishing. All original 14 URLs/IDs remain, through content or onward links where sections moved.

- [Before outline](before-outline.md), [after outline](after-outline.md)
- [Before/after navigation and current source map](navigation-map.md)
- [Original section-to-page mapping](source-map-before.json), [original anchors](anchors-before.json)
- [Maintained source ownership](../../content/README.md)
- [Claim–evidence matrix](claim-evidence.md)
- [QA evidence and browser failures](QA.md), [calculated contrast pairs](contrast.json)
- [Changed files and rationale](changed-files.md)

## Ticket disposition

| Ticket | Result | Remaining boundary |
| --- | --- | --- |
| BR-00 | Complete: baseline/dirty state, source ownership and generated outputs recorded | External audit not accessed; repository scope preserved |
| BR-01 | Complete: existing 0.2.0 drives documentation metadata; fixed test-count assertions removed; historical provenance explicit | No release, account verification or clean-environment install |
| BR-02 | Complete: concise README and full maintained references, preserving useful content | Editorial review remains possible |
| BR-03 | Complete: shared generation/navigation, stable URLs/legacy anchors, no new framework | Future edits must use sources, then regenerate |
| BR-04 | Documentation complete: wizard path, bounded CSV prompt, costs, artifacts, acceptance inspection and stop/failure guidance | Paid/live tutorial validation pending separate authorization |
| BR-05 | Complete: canonical commands traced to implementation, supported flag syntax used | Runtime `/test` banner and positional alias defects separately recorded |
| BR-06 | Complete: claims calibrated and action-point network/credential/host boundaries added | Runtime limitations remain; no security/quality certification |
| BR-07 | BLOCKED: prepared honest showcase outline; historical CLI capture retained separately | Need sanitized real Flask evidence, provenance and owner approval |
| BR-08 | Task-fit guidance complete; source-based rationale labeled proposed | Owner must review attributed rationale |
| BR-09 | Complete local MIT text, package metadata and links after explicit owner choice | Third-party rights/notices not independently audited; remote settings unchanged |
| BR-10 | Source UX polish implemented | Headless launch/driver failures prevent rendered/interaction acceptance |
| BR-11 | Static/build/offline regressions passed | Rendered browser/base-path/assistive-technology and live checks remain unverified |

## Verification actually performed

- `.venv/bin/python scripts/build_docs.py`: builds **18 pages**, version **0.2.0**. Isolated regression verifies deterministic rebuild and equality with current generated output.
- `.venv/bin/pytest tests/test_documentation.py tests/test_cli_version.py -q`: **8 passed** during reapplication. Covers metadata/license agreement, old URLs/anchors, relative Markdown/HTML links/assets, unique IDs, one primary heading/active nav item, SVG XML and determinism.
- `BUILDRELAY_INTEGRATION=0 .venv/bin/pytest -k 'not test_start_preview_server_lifecycle'`: **300 passed, 8 skipped, 1 deselected, 1 warning, 8 subtests passed in 10.47s**. Eight integration checks were explicitly disabled, not passed. The preview lifecycle test was deselected because local port binding was restricted in this environment.
- `.venv/bin/python main.py --version`: exit 0, `buildrelay 0.2.0`.
- `.venv/bin/python main.py --help`: checked earlier in this same task; flags match this HEAD. No task/model invocation occurred.
- `node --check docs/site.js`: passed.
- Scoped `git diff --check -- README.md LICENSE pyproject.toml scripts/build_docs.py docs tests/test_documentation.py`: passed. Whole-worktree check reports existing unrelated `.gitignore:53: new blank line at EOF.` That file was preserved.
- `.venv/bin/python main.py session documentation-parser-check`: deliberately verified the positional alias mismatch. Exit **2**: `buildrelay: error: unrecognized arguments: documentation-parser-check`. Argparse rejected it before session/model dispatch; canonical guides now use supported flags instead.

Dependency warning: `.venv/lib/python3.14/site-packages/google/genai/types.py:42`, `DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17`.

No dependency installation, wheel publication, clean-environment setup, Docker integration or live model tutorial was run. License packaging was checked as metadata, not by publishing a wheel. Suggested prompts are not represented as observations.

## Rendered QA is still blocked

Headless attempts before the external reset are recorded in QA.md; the owner asked to reapply that implementation, and the known environment failures were not repeatedly retried. Browser access host was unavailable; native Firefox access was not approved. Local Playwright was absent; alternate imports returned `The requested module './index.js' does not provide an export named 'default'`, and CommonJS returned `Cannot find module 'playwright'`. Installed Firefox 158.0.1 headless mode exited **134** with only `*** You are running in headless mode.` Cause not established; no screenshot was produced. No package/browser download or unsandboxed retry occurred.

Therefore there are no passed screenshot/DOM/interaction results at **320, 390, 768 or 1440 px**, no actual clipboard/keyboard/no-JS trial, no production-like HTTP base-path browser test, and no screen-reader coverage. Source controls and relative URLs are checked, not full WCAG compliance. Solid-color contrast measurements are in contrast.json; they do not cover all gradients/states/images.

## Evidence and owner decisions

MIT was explicitly selected by the owner, then reapplication authorized. LICENSE uses the standard text and `Copyright (c) 2026 Ehsan`; no name expansion or company ownership was invented. `pyproject.toml` declares MIT and the license file. No version bump/release was made. Dependencies/assets retain their own notices; a full rights audit was not performed.

The owner said supporting benchmark details were still being prepared. Earlier concurrent 100/93/47 scores and illustrated terminal cards were not accepted as authentic performance evidence. A draft/snapshot was preserved in ignored `LinkedIn post/documentation-review-preserved/`; no such results are linked as observed model evidence by these sources. The published-example source remains the dated CLI/offline-test transcript. Its version and commit are “not recorded,” not guessed.

To finish the Flask form-to-PDF showcase, supply an existing shareable original request, chosen plan, actual human decisions/failure/refinement notes, genuine sanitized form/PDF screenshots and outputs, real check commands/statuses, and recorded date/version/commit/model/environment where known. Owner review is needed before publishing. It should be identified as an independent portfolio showcase, not a client deployment. Unknowns stay explicit; token/cost figures are optional with scope/provenance.

Proposed repository description, **not applied remotely**: “Experimental local AI development workflow with typed plans, Docker phase checks, resumable tasks and inspectable project records.” Proposed homepage remains `https://dutch-panda.github.io/BuildRelay/`. Support is through sanitized reproducible issues; no team or SLA was invented.

## Separately scoped runtime findings

1. `/test` banner says container unit tests, but dispatch uses host `os.system` and may directly invoke a generated live script.
2. That direct `/test` live-script path does not use `/verify`'s project environment merge or subprocess timeout.
3. CLI comments/examples imply unquoted `session ID`/`verify ID`/`preview ID`/`eval ID`, but a single positional prompt is defined. Use `--session`, `--verify`, `--preview`, `--eval`; runtime alias handling was not changed here.
4. Preview is a file server over the project directory, not authenticated hosting or automated UI verification. Review sensitive contents.
5. Registry connectivity/error semantics can imply package availability without registry evidence. Candid caveat retained; code not changed.
6. Enabled Docker networking, credentials inside mounted project files, and different tasks sharing one project directory remain operational boundaries.

## Preserved work and completion boundary

At reapplication preflight the unrelated dirty paths were `.gitignore`, untracked `vault/Untitled.base`, plus the previously restored CSS font-size lines. `.gitignore` and vault content were not modified. No runtime agent/provider/execution-policy/CLI files were edited. Documentation UI/generation/tests and owner-authorized license metadata are the only implementation changes.

Nothing was staged, committed, pushed, released or deployed. No credentials were read or paid/live workflows run. The unblocked documentation implementation is ready for review; the overall project is **not declared complete** while owner evidence/attribution and rendered-browser acceptance are pending.

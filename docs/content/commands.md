## Command boundaries

The canonical project-command reference follows actual dispatch in `main.py`, `tools/session.py`, `tools/live_verifier.py` and `tools/ui_preview.py`. Run from the repository root. **Review generated scripts before host execution:** external calls can transmit data, incur charges and change real resources.

| Command | Purpose / equivalent | Execution location | Credentials / network | Writes and caveats |
| --- | --- | --- | --- | --- |
| `python main.py config` | Select connection and models | Host | May sign in/query endpoints | Writes local configuration and selected credential file; permissions are not encryption |
| `python main.py "TASK" --project ID` | New task | Host orchestration; phase commands in Docker | Models, optional search/downloads | Writes ledger, vault and workspace; review code and tests |
| `python main.py --resume TASK_ID` | Reuse saved stages | Host; possibly Docker | Only executing stages need model access | Saves new run state; interrupted work may repeat |
| `buildrelay --session ID` | REPL; `python main.py --session ID` | Host | Setup may be needed; task prompts call models | Creates/loads project workspace and memory |
| `/profile` | Display `PROJECT_PROFILE.md` | Host | No inference/network needed to display | Recorded context is not guaranteed correct |
| `/env` | Inspect masked settings; optionally save `NAME=value` | Host | Values may be credentials | Reads/writes project `.env`; partial masking reveals characters. Do not record real values |
| `/verify` | `buildrelay --verify ID` / `python main.py --verify ID` | **Host** | Inherited host environment plus project settings; potentially live services | Runs generated Python/Node/shell smoke scripts; 60-second subprocess timeout. Apps Script returns manual guidance, not proof of a cloud pass |
| `/preview` | `buildrelay --preview ID` / `python main.py --preview ID` | Host local HTTP server | No inference required; HTML can load external assets | Serves workspace files. Not authenticated hosting or browser behavior testing. Review sensitive contents and stop when finished |
| `/test` | No dedicated CLI equivalent | **Host, not Docker** | Depends on selected command; potentially live | Chooses `npm test` if `package.json` exists; else directly runs `scripts/verify_live.py` if present; else host pytest fallback. Does not use `/verify` environment merge/timeout handling |
| `/eval` | `buildrelay --eval ID` / `python main.py --eval ID` | Host static inspection | No model/live verification by the evaluator | Writes `vault/evaluations/`; heuristic scores are not actual coverage/security/usability measurements |
| `/exit`, `/quit`, `quit`, Ctrl+D | Leave REPL | Host | None | Local files remain; `/exit` is not a standalone CLI command |

### The `/test` banner discrepancy

The session banner currently describes `/test` as container tests. Actual dispatch calls `os.system` on the host. This documentation describes the implementation; fixing the runtime/banner is a separate change. Treat `/test` as generated host execution, potentially live.

### Preview limits

The preview server uses `SimpleHTTPRequestHandler` rooted at the workspace and binds to loopback. It helps view HTML; it does not validate form submissions, responsive layout, accessibility or integrations. Do not assume sensitive files/dotfiles are hidden by application access control. Use sanitized workspaces for demonstrations.

### Prefer the flag forms in this checkout

`main.py` defines one positional prompt argument. Use `--session ID`, `--verify ID`, `--preview ID` and `--eval ID`. Unquoted multi-token forms such as `buildrelay session my-project` are rejected by argparse before dispatch, despite examples in some runtime comments/banners. A quoted command string is a different parser input; this guide standardizes on the explicit supported flags. Correcting the aliases is a separate implementation change.

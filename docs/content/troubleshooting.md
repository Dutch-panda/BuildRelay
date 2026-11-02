## Troubleshooting

- **Docker connection fails:** start Docker and confirm `docker info` succeeds in the same terminal. The CLI uses the Docker SDK's environment configuration.
- **Authentication fails:** verify that direct API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`) are present in `.env` or system environment, or complete the ChatGPT OAuth flow in your browser on first run. If using OAuth, verify that the authorization callback finishes and the credentials file is readable (defaulting to `.env.chatgpt-auth.json` or configured via `CHATGPT_AUTH_FILE`).
- **Graph extraction fails:** inspect the logged Graphify error. Extraction runs as `python -m graphify extract <vault>` using the CLI's Python interpreter, with `GRAPHIFY_OUT` pointing to `vault/.graphify`. Each extraction has a 300-second timeout. Saved Markdown remains available if extraction fails.
- **Dependencies disappear between commands:** install them inside the mounted task directory. Each command starts a new container.
- **Implementation reports failure:** inspect `vault/code-reviews/review-<task_id>.md` and terminal output. A phase is recorded only when its exact validation command exits successfully with the expected phase name.
- **Unknown task ID on resume:** run from the same repository root and use the permanent ID printed by the CLI. Confirm the original `.state/tasks.db` is present; older tasks created before the ledger cannot be resumed automatically.
- **Saved workspace is missing:** restore `workspace/<project_id>/` (or `workspace/<task_id>/`) from the same backup as the ledger. A checkpoint records progress, not a copy of generated source files.
- **Task is already running:** another CLI process holds the task lock. Let it finish or stop that process; a leftover `.lock` file alone does not mean the lock is held. Do not delete lock files to bypass a running task.
- **Interrupted command outcome is unknown:** inspect the existing files, running containers, and external side effects before resuming. Commands may have partially completed and can run again.
- **Invalid checkpoint:** preserve the original ledger and restore a consistent backup if available. Do not edit phase completion flags to force a resume; start a new task if the checkpoint cannot be recovered.
- **A linked note is missing:** research and specification notes exist only when their stages run. New briefs use permanent task IDs; older artifacts may still contain unresolved temporary brief links.

## Resume a task

The CLI creates a permanent task ID before routing and prints it for later use. Each run is saved in a local SQLite ledger at `.state/tasks.db`. If a workflow fails or is interrupted, resume it from the same repository root:

```bash
python main.py --resume task-build-csv-validator-20261024
```

Replace the example ID with the one printed by your run. Resume reuses the saved prompt, project ID, stage outputs, and workspace. Do not supply a new prompt or `--project` together with `--resume`.

The ledger tracks `PENDING`, `RESEARCHING`, `ARCHITECTING`, `IMPLEMENTING`, `COMPLETED`, and `FAILED`. Completed routing, research, and specification outputs are reused. During implementation, validated phases are skipped and prior validation history is retained. A resumed task that proceeds to execution starts a new numbered run with a fresh three-attempt budget for unfinished phases. A completed task returns without calling a model or rerunning agents.

Command checkpoints are saved before execution and after results are recorded. If interruption happens between those points, the CLI reports the command's outcome as unknown. Inspect the workspace and any external side effects before resuming; a container may still be running after an abrupt process exit. An unfinished command or stage may execute again. Resume does **not** guarantee exactly-once execution or restore the entire model conversation; Meti receives the saved plan, validation history, and interrupted-command information in a fresh conversation.

Back up `.state/`, the corresponding task workspace, and `vault/` together when no workflow is running. Git does not back up the ignored ledger, workspaces, or generated notes. The ledger stores prompts, structured stage outputs, and validation logs locally; it does not replace the generated workspace or vault files. A missing workspace after implementation has begun causes resume to fail rather than silently discard saved work. Only tasks created with the ledger can be resumed; older vault artifacts are not imported automatically. Local per-task locks prevent concurrent CLI runs of the same task and release when the process exits. Unknown IDs and unreadable checkpoints fail explicitly.

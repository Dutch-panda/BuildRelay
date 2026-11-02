## Current limitations

The current version is declared in [pyproject.toml](../../pyproject.toml) and rendered in the website header. This is an experimental tool. These details matter when interpreting its output:

- **Web research:** search snippets and registry metadata are available; full-page fetching is not wired into the agents. URL validation has DNS/redirect gaps, and an offline registry lookup can be misreported as verified.
- **Estimates and caching:** model availability, prices, and caching behavior depend on the provider. Bundled cost estimates are not billing guarantees.
- **Shared workspaces:** locks are per task, not per project; avoid simultaneous tasks modifying the same project directory.
- **Optional stage links:** specification and review frontmatter can link to skipped stages; a wikilink does not guarantee its target exists.
- **Container isolation:** network access is enabled, the task directory is writable, and the runner does not configure CPU or memory limits.
- **Validation scope:** phase completion reflects command exit codes. It does not independently establish test quality or provide a separate human code review.

<div align="center">

<sub>Built with Python · Pydantic AI · Docker · Markdown · Graphify</sub>

</div>


## Security and isolation boundaries

BuildRelay uses Docker workspace mounts and constrained host-side tools. These are isolation boundaries, not a guarantee against hostile generated code:

- **Credential Boundaries:** The Docker runner does not pass host environment variables explicitly. The task/project workspace is mounted, however, so a project `.env` inside it is readable by container code. File mode `0600` is not encryption or isolation from a process with sufficient access. Keep unrelated provider credentials outside generated workspaces.
- **Workspace Containment:** Docker containers mount strictly the target task or project workspace (`workspace/<task_id>/` or `workspace/<project_id>/`) to `/app/workspace/<task_id>/`. The runner does not mount the repository root or repository-level `.env`, `.git/` and `.state/`; a project `.env` inside the workspace remains accessible. Path traversal via task IDs is blocked by strict regex validation (`^[A-Za-z0-9][A-Za-z0-9_-]*$`) and filesystem root containment checks.
- **Agent Tool Boundaries:** Host-level agents (Natasha, Odin, Taghi) use vault graph queries and constrained Markdown note writers; Natasha and Odin also have external search tools, and Odin has registry lookup. They have no terminal, shell, or arbitrary filesystem access.
- **Vault Artifact Writing:** Model-callable note tools use `safe_write_markdown` to constrain their destinations. Application-generated briefs, research, specifications, and reviews also use direct file writes to configured artifact directories; the shared safe writer does not mediate every artifact write.
- **Execution Boundaries:** Meti phase commands run inside Docker. Tier 2 `buildrelay verify` explicitly executes generated smoke scripts on the host with project credentials; review those scripts before invoking verification. Host verification is not sandboxed like Docker phase execution.
- **Credential Storage Security:** `.env` and `.env.*` (including `.env.chatgpt-auth.json`) are ignored by Git. The interactive onboarding wizard (`tools/onboarding.py`) and OAuth credential flows enforce atomic file writes with strict `0o600` permissions (readable and writable only by the owner). The runner does not mount the repository-level credential files. Project-local `.env` files live inside the mounted workspace and need separate care.

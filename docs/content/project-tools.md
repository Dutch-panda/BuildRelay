## Project REPL, Live Verification, and UI Preview

**Read [command boundaries](commands.md) first.** `/test` executes host commands and may invoke a generated live script. `/verify` runs on the host with its environment and project credentials; real services may change. Preview serves project files, not an authenticated production app.

### Start a project session

```bash
buildrelay --session my-project
```

Loads/creates the project workspace and recorded profile. New task prompts use normal orchestration and may require setup. `/profile` displays recorded context; `/env` can inspect/update project settings and only partially masks values. Never record real credentials.

### Verify only after reviewing the generated script

```bash
buildrelay --verify my-project
```

Generated **host** Python/Node/shell execution can use credentials and contact services. Apps Script produces manual instructions, not a cloud test result.

### Preview a sanitized UI workspace

```bash
buildrelay --preview my-project
```

Use the printed loopback address, inspect what is served and stop the server when finished. File serving is not UI behavior testing. See [command boundaries](commands.md) for canonical dispatch and caveats.

### Split-Pane Terminal Cockpit

Launch the interactive split-pane terminal cockpit to inspect project health, telemetry logs, and workflow status:

```bash
buildrelay cockpit my-project
```

Inside an active REPL session (`buildrelay --session my-project`), type `/cockpit` to launch the dashboard at any time.

The Cockpit features:
- **Header Bar HUD:** Live elapsed timer, token metrics, model tier, and preview state.
- **Workflow Sidebar:** Pipeline progression stepper (`Natasha ➔ Taghi ➔ Diba ➔ Meti`), phase validation roadmap, and living memory schemas.
- **Container Telemetry Buffer:** Real-time scrolling stdout/stderr logs from Docker execution.
- **Interactive Command Dock:** Quick action shortcuts (`[P] Preview`, `[V] Verify`, `[D] Dana`, `[L] Logs`, `[Q] Exit`) and embedded gate alerts.

<details><summary>Earlier guide links</summary>

<p id="1-interactive-project-repl-session-buildrelay-session"><a href="#start-a-project-session">Continue to the maintained section →</a></p>
<p id="2-live-verification-runner-buildrelay-verify"><a href="#verify-only-after-reviewing-the-generated-script">Continue to the maintained section →</a></p>
<p id="3-local-ui--input-preview-buildrelay-preview"><a href="#preview-a-sanitized-ui-workspace">Continue to the maintained section →</a></p>

</details>

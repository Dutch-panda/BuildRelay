## Quick start

For developers comfortable with Python and Docker who want a small, inspectable generated project. This is a suggested tutorial, **not a recorded successful model run**. End-to-end validation with an account is pending.

### 1. Install from the repository

You need Python 3.11+, Git and Docker installed and running. A remote model needs an eligible account/API connection; provider availability, quotas, subscriptions and charges apply. A local model requires a compatible endpoint and sufficient local resources. Obsidian is optional.

```bash
git clone https://github.com/Dutch-panda/BuildRelay.git
cd BuildRelay
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
docker info
```

On Windows, replace activation with `.venv\Scripts\Activate.ps1` in PowerShell. If Docker cannot connect, start Docker and rerun `docker info` before continuing.

Inspect the CLI without calling a model:

```bash
python main.py --help
```

### 2. Configure one connection

The wizard selects a connection and explicit models for the leads, then writes local configuration. Sign-in, catalog discovery and connectivity checks may contact providers. Setup completion does not guarantee later execution or quota. Never paste credentials into issue reports or recordings.

```bash
python main.py config
```

Use models supported by your connection. See [configuration and precedence](configuration.md) for manual options, discovery limits and overrides; those are not required reading before this first path.

### 3. Request one bounded task

Review the request, selected models, plan and checks before allowing generated execution. Prompts and retrieved context may be sent to providers. Docker networking remains enabled; images and dependencies may be downloaded. Keep unrelated credentials out of the workspace: its files, including a project `.env`, are readable by container code.

```bash
python main.py "Build a small Python CSV validator with a CLI. Require name and amount columns, report invalid amounts, and include valid and invalid fixtures, automated tests, and README run instructions." --project csv-demo --image python:3.11-slim --step
```

Answer alignment questions and inspect the specification if that route is selected. `--step` adds handoff confirmations. Simpler tasks can skip research/design; a detailed plan is not proof of correctness. The prompt above is an instruction example, not observed output.

### 4. Inspect the result

- Generated source, fixtures and instructions should appear in `workspace/csv-demo/`.
- Stage notes live under `vault/`; implementation reports are in `vault/code-reviews/`. The ledger is `.state/tasks.db`.
- Inspect the generated README and phase command/exit-code history. A zero exit code does not establish test completeness or safety.
- For this task, check acceptance of valid input and rejection of missing columns/invalid amounts. Inspect whether automated checks exercise both cases. Review the test command before executing it in the intended sandbox; do not blindly run generated scripts on the host.

No expected success output or score is supplied because a shareable end-to-end tutorial run has not been verified. The [historical terminal capture](example.md) demonstrates only CLI help and offline platform tests.

### Stop or continue

Press Ctrl+C to request interruption. Saved ledger/workspace data remains, but an in-flight command can have unknown effects and a container can still be running. Inspect before [resuming](resume.md): resume is not exactly-once execution or a workspace backup.

After delivery, stop, add a feature, or enter a [project session](project-tools.md). Read [command boundaries](commands.md) before `/test`, `/verify` or preview: they do not share Meti's Docker trust boundary.

<details><summary>Earlier guide links</summary>

<p id="1-prepare-the-environment"><a href="#1-install-from-the-repository">Continue to the maintained section →</a></p>
<p id="2-configure-credentials--providers"><a href="configuration.md#connection-and-model-reference">Continue to the maintained section →</a></p>
<p id="interactive-setup-wizard-recommended"><a href="configuration.md#interactive-setup-wizard-recommended">Continue to the maintained section →</a></p>
<p id="manual-configuration-via-env-alternative"><a href="configuration.md#manual-configuration-via-env-alternative">Continue to the maintained section →</a></p>
<p id="explicit-provider-and-model-selection-issue-26"><a href="configuration.md#explicit-provider-and-model-selection">Continue to the maintained section →</a></p>
<p id="3-give-the-team-a-task"><a href="#3-request-one-bounded-task">Continue to the maintained section →</a></p>

</details>

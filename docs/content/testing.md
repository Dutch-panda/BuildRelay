## Testing


Install the test extra and run the local validation command from the repository root:

```bash
python -m pip install -e '.[test]'
python scripts/validate.py
```

The script runs the platform tests in `tests/` (see CI for current results); extra pytest arguments can be appended, for example `python scripts/validate.py -k validation`. Test discovery excludes generated workspaces. The suite uses Pydantic AI `TestModel` for structured outputs and `FunctionModel` for scripted tool calls, blocks real model requests, replaces Docker and graph extraction, and writes artifacts in temporary directories. It covers routing contracts, project links, explicit dependency injection, graph retrieval, source resolution and report references, phase validation, bounded recovery, container isolation invariants, Docker failure feedback, ledger persistence, resume behavior, onboarding, model tiers, token estimates, alignment gates, and mocked web search; it does not assess live model routing quality.

#### Opt-in Integration Smoke Checks (Real Docker & Graphify)

While unit tests run with fully mocked external services for speed and offline determinism, BuildRelay also includes opt-in integration smoke checks that run against a live Docker daemon and the real Graphify CLI:

```bash
# Run real Graphify smoke checks
BUILDRELAY_INTEGRATION=1 pytest -m graphify

# Run real Docker smoke checks (requires Docker daemon running)
BUILDRELAY_INTEGRATION=1 pytest -m docker

# Run all integration smoke checks
BUILDRELAY_INTEGRATION=1 pytest -m integration
```

These integration checks verify:
- **Real Docker Lifecycle:** Container startup, stdout/stderr logging, two-way workspace volume persistence, command exit codes, and timeout termination with force cleanup.
- **Host Security Isolation:** Real container execution verifying that host environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) are completely absent inside the running container.
- **Real Graphify Extraction:** Subprocess invocation of `python -m graphify extract`, AST knowledge graph generation, `graph.json` serialization, and node traversal queries.

If Docker or Graphify is unavailable in the environment, the tests skip gracefully without false test failures. CI runs both the isolated unit test suite and the integration smoke checks on Ubuntu runners.

The [Platform tests workflow](../../.github/workflows/tests.yml) runs the same validation command on pushes and pull requests using Ubuntu with Python 3.11, 3.12, 3.13, and 3.14. Open [CI results](https://github.com/Dutch-panda/BuildRelay/actions/workflows/tests.yml) to inspect runs. To start a manual run, select **Run workflow**, choose a branch, and confirm. Results and failure logs appear on the commit or pull request; unit tests need no model credentials or Docker daemon; opt-in Docker checks require running infrastructure. Skips are not passes. Requiring passing checks before merging is a separate repository setting.

An end-to-end run still requires model access and Docker and writes local artifacts; review generated output before using it.

Documentation has two roles:

- The README is the entry point; docs/content Markdown maintains the operational reference.
- `vault/` and `workspace/` contain local run artifacts and examples. Historical reports describe individual runs, not guaranteed platform capabilities. They are not the public platform manual.

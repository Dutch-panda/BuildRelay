## Connection and model reference

Model IDs below are historical examples, not account-availability guarantees. Discover through your connection when possible; browser-login fallback suggestions remain unverified.



BuildRelay provides an interactive setup wizard to configure your preferred LLM provider, models; setup time and availability depend on your connection.

#### Interactive Setup Wizard (Recommended)

Run the configuration wizard directly at any time:

```bash
python main.py config
# Or using the console script:
buildrelay config
# Or via CLI flag:
python main.py --config
```

If you launch BuildRelay on a fresh machine without credentials, the CLI automatically detects the zero-config state and prompts:
```
⚡ BuildRelay — No AI credentials detected. Launching interactive setup wizard...
```

The wizard guides you through:
1. **Provider Selection:**
   - **ChatGPT Web Auth (Codex / Browser Subscription):** Connects to your ChatGPT Plus/Team subscription without entering an API key; provider access and usage limits still apply. Browser model discovery is unavailable; any suggested names are unverified and must be supported by your account.
   - **OpenAI API:** Direct API key for GPT-4o, GPT-4o-mini, o3-mini, o1.
   - **Anthropic Claude:** Direct API key for Claude 3.7 Sonnet, Claude 3.5 Haiku.
   - **Google Gemini:** Direct API key for Gemini 2.0 Flash, Gemini 2.5 Pro.
   - **Local LLM (Ollama / LocalAI):** Locally hosted models (compute/resource costs still apply) (e.g. `llama3.3`, `qwen2.5-coder` at `http://localhost:11434/v1`).
   - **Custom / OpenRouter Gateway:** OpenRouter or custom OpenAI-compatible proxies.
2. **Masked Input & Validation:**
   - Inputs are masked for security (`password=True`).
   - A short, synchronous reachability check runs for supported providers before saving. Connectivity failures can be treated as skipped checks; setup completion does not prove model access.
3. **Per-Lead Model Selection:**
   - Choose Natasha, Odin, Taghi, and Meti models from numbered choices. Enter reuses the previous choice; `/text` filters the list, `m` enters an unverified custom ID, and `q` cancels.
4. **Saved Assignments:**
   - Each interactive run displays the saved lineup. Keep it or change an individual lead, then optionally save the new assignments. Changes remain run-only unless saving is explicitly requested.
5. **Safe Atomic Persistence:**
   - Saved directly to `.env` preserving existing comments and settings.
   - Enforces strict `0600` file permissions (owner read/write only).

#### Manual Configuration via `.env` (Alternative)

If you prefer editing `.env` directly:

**Option A: ChatGPT Web Auth (Codex Subscription — No API Key Required)**
```dotenv
BUILDRELAY_PROVIDER=chatgpt_oauth
BUILDRELAY_MODEL_MODE=selected
BUILDRELAY_MODEL=openai:YOUR_ACCOUNT_MODEL_ID
USE_CHATGPT_OAUTH=1
CHATGPT_AUTH_FILE=.env.chatgpt-auth.json
```

**Option B: Standard Direct API Keys**
```dotenv
BUILDRELAY_PROVIDER=openai
BUILDRELAY_MODEL_MODE=selected
BUILDRELAY_MODEL=openai:YOUR_ACCOUNT_MODEL_ID
OPENAI_API_KEY=sk-...
USE_CHATGPT_OAUTH=0

# Or Anthropic:
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-7-sonnet

# Or Gemini:
# GEMINI_API_KEY=AIza...
# GEMINI_MODEL=gemini-2.0-flash

# Optional per-lead overrides:
# MODEL_NATASHA=openai:YOUR_ROUTER_MODEL_ID
# MODEL_ODIN=openai:YOUR_RESEARCH_MODEL_ID
# MODEL_TAGHI=openai:YOUR_DESIGN_MODEL_ID
# MODEL_METI=openai:YOUR_CODING_MODEL_ID
```

Replace placeholder model IDs with choices from your connection. Use the wizard to configure another provider; an explicit connection does not silently switch authentication for cross-provider overrides.

You can also override models at runtime using `--model` (e.g., `--model anthropic:claude-3-7-sonnet`) or per-lead flags (`--model-taghi`, `--model-meti`).

### Explicit provider and model selection

First-time interactive runs open setup before using any lead. Choose browser authentication or an API/local connection, authenticate, and select a model. API catalogs are queried using that connection; discovery failures and browser-login suggestions are explicitly unverified. Catalog presence does not guarantee tool/structured-output support or account quota.

Setup saves `BUILDRELAY_PROVIDER`, `BUILDRELAY_MODEL`, and `BUILDRELAY_MODEL_MODE=selected`. Setup saves explicit `MODEL_NATASHA`, `MODEL_ODIN`, `MODEL_TAGHI`, and `MODEL_METI` assignments. Each lead is selected with a numbered picker; Enter reuses the previous choice. Tiers are not offered in setup or the run-time picker. A changed run-time lineup is saved only after explicit confirmation. The picker retains cached catalogs, saved lead choices, and separately labeled unverified fallback suggestions. Native model IDs containing colons, such as local `model:tag`, are supported. Reconfiguration replaces previous lead choices; old credentials can remain stored without changing the active connection. Cross-provider overrides require reconfiguration instead of silently switching authentication. Browser login failure leaves setup incomplete. No live account access is established by the offline tests.


## Tiered model routing and token optimization

Normal setup uses explicit per-lead choices, with no tier selection. The legacy `--tier` CLI option remains for compatibility; explicit saved lead assignments take precedence over its presets. Context compression remains independent of model selection:

- **Model Tiers (`--tier`):**
  - **Fast (`--tier fast`):** Routes lightweight, fast models across all leads (`gpt-4o-mini`, `claude-3-5-haiku`, `gemini-2.0-flash`). Ideal for quick scripts, prototyping, and high speed.
  - **Balanced (`--tier balanced` — default):** Pairs fast models for routing (Natasha) and graph search (Odin) with high-reasoning models for architecture (Taghi: `o3-mini`) and implementation (Meti: `gpt-4o` / `claude-3-7-sonnet`).
  - **Powerful (`--tier powerful`):** Assigns top-tier frontier models across all design and execution phases.
- **Lead-Specific Overrides:**
  - Override individual leads via CLI flags: `--model-natasha`, `--model-odin`, `--model-taghi`, `--model-meti`.
  - In selected-model mode, precedence is explicit per-lead CLI choice, global `--model`, saved lead choice, then the saved default model. Legacy `--tier` behavior is retained separately.
- **Model Lineup Approval Gate:**
  - On launch, BuildRelay renders a 2-column model lineup card displaying the active model for each lead, cost tier label, caching status, and estimated budget.
  - Interactive users can press **`[Enter]`** to confirm, **`[c]`** to choose a lead and change its model from a numbered picker (with optional saving), or **`[q]`** to abort. Auto/headless runs (`-y`/`--auto`) accept automatically.
- **Prompt Prefix Caching:**
  - Agents use reusable instructions and pass cache settings; those settings do not establish provider cache behavior.
  - Agents pass `model_settings={"cache": True}`. Actual caching depends on the provider, model, and SDK support; BuildRelay does not guarantee a cache hit or measured latency or cost savings.
  - Cached tokens are detected and discounted in token summary badges and ledger reports.
- **Context Pruning & Compression:**
  - **Markdown Sanitization:** `prune_markdown` strips verbose YAML frontmatter, empty sections, and backlink blocks.
  - **Semantic Graph Pruning:** `prune_graph_context` scores and ranks vault nodes by keyword overlap, passing only the top 3–5 relevant snippets to Odin rather than raw graph dumps.
  - **Docker Log Slicing:** `prune_docker_log` automatically detects failure tracebacks and assertion errors in long build logs, slicing around the error signature to reduce log text supplied during retry loops.



## Token usage and cost analytics

BuildRelay records provider-reported prompt/completion usage through PydanticAI metrics. These may be incomplete and are not an independent billing audit:

- **Cost Estimation Engine:** Estimates USD costs using a bundled model-rate table (OpenAI, Anthropic, Gemini). Rates and cache discounts are approximations, not provider billing records.
- **Local & Test Models:** Displays `$0.00 (Local)` for Ollama/vLLM and test runs.
- **Inline Badges:** Natasha brief panels and Taghi specification cards display token tallies as each stage finishes (e.g. `Tokens Used: 1,550 (~$0.006)`).
- **Obsidian Vault Reports:** Meti's review notes under `vault/code-reviews/` record full token metrics and costs.
- **Completion Table:** At workflow completion, a styled Rich table summarizes prompt, completion, total tokens, and estimated cost per lead with grand totals.

## Additional task command examples


```bash
python main.py "Build a compound interest calculator" --project my-awesome-app
```

For a standalone task, omit the project:

```bash
python main.py "Create a small CSV validation utility with tests"
```

To specify or override the Docker sandbox image:

```bash
python main.py "Build a Python utility" --image python:3.11-slim
```

Run commands from the repository root so `./vault` and `./workspace` resolve correctly. Inspect the CLI without starting a workflow:

```bash
python main.py --help
```

The first sandbox command pulls the selected container image (defaulting to `node:18-bullseye-slim` or the configured `DEFAULT_SANDBOX_IMAGE` / `--image`) if it is missing locally. Generated files live in `workspace/<project_id>/` (or `workspace/<task_id>/` for standalone tasks); implementation summaries and phase results are saved under `vault/code-reviews/`. A returned failed implementation makes the CLI exit with status `1`.


# README before migration

Baseline: cffdc70, main.

```text
# BuildRelay
### An AI development team that plans, builds, and checks your code.
## How the workflow runs
## Quick start
### 1. Prepare the environment
### 2. Configure credentials & providers
#### Interactive Setup Wizard (Recommended)
# Or using the console script:
# Or via CLI flag:
#### Manual Configuration via `.env` (Alternative)
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
### Explicit provider and model selection (issue #26)
### 3. Give the team a task
## Interactive alignment and execution modes
## Quality supervision and evaluation
### Dana quality supervision
### Deliverable evaluation
## Token usage and cost analytics
## Tiered model routing and token optimization
## Web and documentation search with guardrails
## Dynamic progress and project delivery
## Project REPL, Live Verification, and UI Preview
### 1. Interactive Project REPL Session (`buildrelay session`)
# Or:
### 2. Live Verification Runner (`buildrelay verify`)
# Or:
### 3. Local UI & Input Preview (`buildrelay preview`)
# Or:
## Resume a task
## Keep related tasks connected
### Interactive Project REPL Session
# Launch interactive REPL session
# Or using the console script:
### Project Memory on Disk (`PROJECT_PROFILE.md` & Local `.env`)
### Research source references
## What stays on disk
## Execution and validation
### Recovery and attempt history
## Brand assets
## Component connections
## Repository map
## Troubleshooting
## Security and isolation boundaries
## Development and documentation
### Website documentation
### Testing
#### Opt-in Integration Smoke Checks (Real Docker & Graphify)
# Run real Graphify smoke checks
# Run real Docker smoke checks (requires Docker daemon running)
# Run all integration smoke checks
## Current limitations
```

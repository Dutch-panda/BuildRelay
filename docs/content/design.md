## Design decision: an inspectable local workflow

Status: implementor's source-based explanation, **pending Ehsan's review**. This is not an approved quotation of Ehsan's rationale.

- **Context:** requests can span clarification, research, architecture, implementation and checks; interruption leaves useful intermediate work.
- **Alternatives:** one coding session with manual records; fully parallel agents; or selected sequential roles with checkpoints.
- **Current approach:** typed handoffs, routed sequential stages, SQLite checkpoints, Markdown records, Docker phase execution, optional model supervision and human approval gates.
- **Reasoning inferred from source:** explicit stage boundaries make progress and recovery inspectable; routing avoids requiring every stage for simple tasks.
- **Consequence:** artifacts/persistence add maintenance, and multiple stages can add latency, token usage and interaction overhead. Host live verification has a different trust boundary.
- **Observed evidence:** deterministic tests exercise routing, phase order and checkpoint consistency. The historical terminal capture shows offline tests, not live task quality or productivity advantages.
- **Unresolved trade-off:** representative real trials are needed to establish when the extra stages justify their resource cost. No superiority claim against other tools/frameworks is made.

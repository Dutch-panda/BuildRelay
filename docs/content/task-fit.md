## Task fit

BuildRelay is an experimental local developer tool for someone able to review requirements, generated code and test evidence. These suggestions follow its design, not measured success rates.

### Useful for

- Bounded utilities with explicit input/output contracts and deterministic checks.
- Small development or integration prototypes with inspectable plans and phase history.
- Iterative work on one local project, using recorded context and human approval points.
- Studying routed multi-role workflows, persistence and recovery behavior.

### Consider a simpler approach when

- You need a tiny known edit; Docker setup and several model calls may add more work than they save.
- You require production deployment, compliance assurance or independent security/UX verification.
- Required credentials/services cannot be used in the sandbox. Mock checks and host smoke scripts establish different evidence.
- You cannot review generated code or accept provider data handling and usage costs.

### Routing, persistence and human judgment

Routing selects an entry point, after which stages run sequentially rather than as four parallel agents. Research-led builds continue to design and implementation; direct builds skip earlier stages; research-only stops after research. Dana supervision is optional model critique, not a guaranteed independent file-by-file review.

Checkpoints and project memory carry recorded context. They do not prevent schema drift, restore lost files or provide exactly-once execution. Approval gates provide an opportunity for human judgment; headless mode accepts defaults instead.

See [workflow](workflow.md), [limits](limitations.md), and the [proposed design rationale](design.md).

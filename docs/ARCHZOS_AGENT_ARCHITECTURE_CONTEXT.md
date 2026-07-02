# ArchzOS Agent Architecture Context

`reasoning-cliff` is the reasoning-capability boundary mapping harness in the
archzOS OSS suite.

## Why this repo exists

Agent systems need a measurable routing boundary for when direct model reasoning
is reliable versus when tool execution should be mandatory.

## Operational fit

In long-horizon agent workflows, failed high-complexity reasoning can create
cascading task regressions. This harness maps model-specific collapse thresholds
and token-starvation boundaries so orchestration layers can route safely.

## Routing implication

If a model/puzzle cell is consistently `GENUINE_COLLAPSE` at uncapped budgets,
the orchestration policy should route to tools instead of repeated free-form
reasoning attempts.

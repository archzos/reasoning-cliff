# Controversy Note

## The Debate This Harness Addresses

### Original claim (Shojaee et al., 2506.06941)
- Accuracy collapse at higher complexity
- Decreasing reasoning effort beyond the cliff
- Algorithm provision does not prevent collapse

### Methodological critique (Lawsen/Opus, 2506.09250v2)
- High-N Hanoi often exceeds configured output-token budgets
- Evaluators can conflate truncation with reasoning failure
- River Crossing with `boat_capacity=3` and `n>5` is unsolvable and must not be scored as model failure

### Replication nuance (Rethinking, 2507.01231)
- Stepwise prompting shifts the cliff right by removing enumeration burden
- Genuine collapse can still persist at higher complexity

## Controls Implemented In This Harness

1. Token control:
- `DEFAULT`, `DOUBLE`, `UNCAPPED` budget runs per cell

2. Failure-type separation:
- `CLEAN`
- `TOKEN_STARVED`
- `INTENTIONAL_TRUNCATION`
- `GENUINE_COLLAPSE`

3. River Crossing solvability pre-flight:
- Hard exclusion of unsolvable cells from scored suite

## Claims this harness can support

- At uncapped output, model still fails at complexity `N` (genuine collapse evidence)
- Failures disappear or shrink with higher output budgets (token-starvation evidence)
- Relative shift in collapse threshold under `STANDARD` vs `STEPWISE` conditions

### Concrete examples of valid claims

- "For `hanoi`, `gpt-4o` at `n=8` is `TOKEN_STARVED` because DEFAULT failed and UNCAPPED passed."
- "For `hanoi`, `claude-sonnet-4-6` at `n=9` is `GENUINE_COLLAPSE` because all budget levels failed."
- "For `hanoi`, `STEPWISE` shifted threshold from `n=8` to `n=9` relative to `STANDARD`."

## Claims this harness cannot support

- Strong claims about fundamental cognition
- Cost/latency guarantees for production deployment
- Claims about models not run in this harness

### Concrete examples of invalid claims

- "All LRMs cannot reason" (too broad and not supported by this harness scope).
- "Model X is always unsafe for production" (this harness is not a safety benchmark).
- "Model Y is better globally" without specifying puzzle family, condition, and budget.

## Failure-type semantics (exactly as implemented)

Per `(model, puzzle, complexity, condition)` cell:

- `CLEAN`: at least one DEFAULT-budget trial is correct
- `INTENTIONAL_TRUNCATION`: model signals early stop/truncation intent in output
- `TOKEN_STARVED`: DEFAULT fails, UNCAPPED has at least one correct trial
- `GENUINE_COLLAPSE`: DEFAULT fails and UNCAPPED also fails

These are mutually exclusive labels in analysis slices and must not be merged
into a single "failure" bucket.

## Example row-level interpretation

Example cell: `(gpt-4o, hanoi, n=10, TOKEN_CONTROLLED)`

- DEFAULT trials: all incorrect, truncated
- DOUBLE trials: mixed
- UNCAPPED trials: at least one correct

Classification: `TOKEN_STARVED` (not `GENUINE_COLLAPSE`), because higher budget
changed outcome.

Example cell: `(claude-sonnet-4-6, hanoi, n=10, STEPWISE)`

- DEFAULT trials: all incorrect
- UNCAPPED trials: all incorrect
- No intentional truncation phrases detected

Classification: `GENUINE_COLLAPSE`.

## Chart interpretation guidance

- Collapse curve:
  - If UNCAPPED stays above DEFAULT, budget confound is active.
  - If UNCAPPED also drops, genuine collapse remains.
- Effort curve:
  - Falling effort at higher complexity supports "effort contraction."
  - Flat/increasing effort is also valid evidence and should be reported directly.
- Budget comparison:
  - Dominant `TOKEN_STARVED` bars indicate budget-limited failures.
  - Dominant `GENUINE_COLLAPSE` bars indicate failures that persist despite budget.

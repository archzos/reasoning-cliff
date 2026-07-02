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

## Claims this harness cannot support

- Strong claims about fundamental cognition
- Cost/latency guarantees for production deployment
- Claims about models not run in this harness

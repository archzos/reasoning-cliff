# Puzzle Specs

## Tower of Hanoi

- Complexity parameter: `n` disks
- Ground truth move count: `2^n - 1`
- Verifier:
1. Simulate peg states.
2. Reject illegal moves (empty source or larger-on-smaller).
3. Accept only if final state is solved and move count equals `2^n - 1`.
4. Record index of first illegal move when failure occurs.

## River Crossing (Missionaries-Cannibals)

- Complexity parameter: number of actor pairs `n_pairs`
- v1 hard constraint: `boat_capacity=3`, only solvable instances (`n_pairs <= 5`)
- Verifier:
1. Enforce boat load constraints.
2. Enforce bank safety constraints after each crossing.
3. Reject unsolvable instances before evaluation.

## Blocksworld

- Included as Day 2 stretch placeholder.
- Out of scope for v1 baseline; no benchmark claims are made in this repo version.

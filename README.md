# reasoning-cliff

[![CI](https://github.com/archzos/reasoning-cliff/actions/workflows/ci.yml/badge.svg)](https://github.com/archzos/reasoning-cliff/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

AI "reasoning" models collapse beyond a complexity threshold — and paradoxically
think LESS as problems get harder. Apple ML Research (Shojaee et al., 2506.06941)
called it "the illusion of thinking." Three subsequent papers showed the original
experiments had confounds: token limits, impossible puzzle instances, and evaluation
frameworks that couldn't tell "ran out of space" from "genuinely failed to reason."

reasoning-cliff is a reproducible harness that runs the same experiments with all
three confounds controlled: multiple token budgets, solvability-verified puzzle
instances, and a four-way failure classifier. The cliff is real — it just sits
further right than the original paper found, and it's smaller. Here's the map.

## What it provides

- Deterministic puzzle generators and verifiers (Hanoi, River Crossing)
- Multi-budget token control (`DEFAULT`, `DOUBLE`, `UNCAPPED`)
- Four-way failure typing (`CLEAN`, `TOKEN_STARVED`, `INTENTIONAL_TRUNCATION`, `GENUINE_COLLAPSE`)
- DuckDB experiment persistence
- Publication-style matplotlib charts for collapse and effort curves
- CLI for estimate/run/plot/demo workflows

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Quick start

```bash
reasoning-cliff estimate --config config/experiment_config.json --models claude-sonnet-4-6,gpt-4o
reasoning-cliff run --config config/experiment_config.json --models claude-sonnet-4-6,gpt-4o --puzzles hanoi,river_crossing --complexity-range 2:8 --token-budgets DEFAULT,DOUBLE,UNCAPPED --trials 3 --output-db report/results.duckdb
reasoning-cliff plot --db report/results.duckdb --output-dir outputs/figures
```

## Methodology note

This repository explicitly addresses the Shojaee/Lawsen/Rethinking dispute by:
- Running controlled token-budget sweeps for each `(model, puzzle, complexity)` cell.
- Excluding mathematically unsolvable River Crossing instances from evaluation.
- Separating token-starved failures from genuine collapse failures.

See [docs/CONTROVERSY_NOTE.md](./docs/CONTROVERSY_NOTE.md).

## Open source and governance

- License: [MIT](./LICENSE)
- Contribution guide: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Security policy: [SECURITY.md](./SECURITY.md)
- Architecture context: [docs/ARCHZOS_AGENT_ARCHITECTURE_CONTEXT.md](./docs/ARCHZOS_AGENT_ARCHITECTURE_CONTEXT.md)
- Puzzle specs: [docs/PUZZLE_SPECS.md](./docs/PUZZLE_SPECS.md)
- Controversy handling: [docs/CONTROVERSY_NOTE.md](./docs/CONTROVERSY_NOTE.md)

Not affiliated with Apple, Apple ML Research, or any replication authors.

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reasoning_cliff.runner import run_experiments


if __name__ == "__main__":
    rows = run_experiments(
        config_path="config/experiment_config.json",
        output_db="report/results.duckdb",
        models=["claude-sonnet-4-6", "gpt-4o"],
        puzzles=["river_crossing"],
        n_values=[1, 2, 3, 4, 5],
        token_budgets=["DEFAULT", "DOUBLE", "UNCAPPED"],
        trials=3,
        conditions=["STANDARD", "TOKEN_CONTROLLED"],
    )
    print(f"Inserted rows: {rows}")

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reasoning_cliff.runner import run_experiments


if __name__ == "__main__":
    rows = run_experiments(
        config_path="config/experiment_config.json",
        output_db="report/results.duckdb",
        models=["claude-sonnet-4-6"],
        puzzles=["hanoi"],
        n_values=[2, 3, 4, 5, 6, 7, 8],
        token_budgets=["DEFAULT", "DOUBLE", "UNCAPPED"],
        trials=3,
        conditions=["STANDARD", "TOKEN_CONTROLLED", "STEPWISE", "FUNCTION", "GIVEN_ALGORITHM"],
    )
    print(f"Inserted rows: {rows}")

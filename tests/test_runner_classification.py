from __future__ import annotations

from pathlib import Path

import duckdb

from reasoning_cliff import runner


class BudgetSensitiveAdapter:
    def generate(self, prompt: str, max_tokens: int, thinking_budget: int | None = None):
        # For n=2 hanoi: valid solution is 3 moves. Fail at low budget, pass at high budget.
        if max_tokens <= 8192:
            return runner.MockAdapterResponse(
                text="(0,1)",
                output_tokens=5,
                thinking_tokens=3,
                truncated=True,
                stop_reason="max_tokens",
                latency_ms=1.0,
            )
        return runner.MockAdapterResponse(
            text="(0,1)\n(0,2)\n(1,2)",
            output_tokens=12,
            thinking_tokens=8,
            truncated=False,
            stop_reason="stop",
            latency_ms=1.0,
        )


def test_run_experiments_classifies_token_starved(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "results.duckdb"

    monkeypatch.setattr(runner, "_build_adapter", lambda *args, **kwargs: BudgetSensitiveAdapter())

    inserted = runner.run_experiments(
        config_path="config/experiment_config.json",
        output_db=str(db_path),
        models=["claude-sonnet-4-6"],
        puzzles=["hanoi"],
        n_values=[2],
        token_budgets=["DEFAULT", "UNCAPPED"],
        trials=1,
        conditions=["TOKEN_CONTROLLED"],
        dry_run=False,
        allow_live_adapters=False,
    )
    assert inserted == 2

    conn = duckdb.connect(str(db_path), read_only=True)
    rows = conn.execute(
        "SELECT token_budget, correct, failure_type FROM experiments ORDER BY token_budget"
    ).fetchall()
    conn.close()

    assert rows[0][0] == "DEFAULT"
    assert rows[0][1] is False
    assert rows[0][2] == "token_starved"
    assert rows[1][0] == "UNCAPPED"
    assert rows[1][1] is True

"""DuckDB persistence layer."""

from __future__ import annotations

import duckdb
from pathlib import Path

from reasoning_cliff.models import TrialResult

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    puzzle_type TEXT,
    n INTEGER,
    condition TEXT,
    token_budget TEXT,
    model TEXT,
    trial_index INTEGER,
    correct BOOLEAN,
    failure_type TEXT,
    moves_output INTEGER,
    moves_required INTEGER,
    first_error_move INTEGER,
    output_tokens INTEGER,
    thinking_tokens INTEGER,
    truncated BOOLEAN,
    stop_reason TEXT,
    truncation_detected BOOLEAN,
    latency_ms DOUBLE,
    raw_response TEXT
)
"""


def initialize_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path)
    conn.execute(SCHEMA_SQL)
    conn.close()


def insert_trial(db_path: str, result: TrialResult) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path)
    conn.execute(SCHEMA_SQL)
    conn.execute(
        """
        INSERT INTO experiments (
            experiment_id, puzzle_type, n, condition, token_budget, model, trial_index,
            correct, failure_type, moves_output, moves_required, first_error_move,
            output_tokens, thinking_tokens, truncated, stop_reason,
            truncation_detected, latency_ms, raw_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            result.experiment_id,
            result.puzzle_type,
            result.complexity,
            result.condition.value,
            result.token_budget.value,
            result.model,
            result.trial_index,
            result.correct,
            result.failure_type.value,
            result.moves_output,
            result.moves_required,
            result.first_error_move,
            result.output_tokens,
            result.thinking_tokens,
            result.truncated,
            result.stop_reason,
            result.truncation_detected,
            result.latency_ms,
            result.raw_response,
        ],
    )
    conn.close()


def fetch_dataframe(db_path: str, query: str):
    conn = duckdb.connect(db_path, read_only=True)
    df = conn.execute(query).df()
    conn.close()
    return df

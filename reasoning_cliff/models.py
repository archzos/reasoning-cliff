"""Core dataclasses and enums for reasoning-cliff."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TokenBudget(str, Enum):
    DEFAULT = "DEFAULT"
    DOUBLE = "DOUBLE"
    UNCAPPED = "UNCAPPED"


class ExperimentCondition(str, Enum):
    STANDARD = "STANDARD"
    TOKEN_CONTROLLED = "TOKEN_CONTROLLED"
    STEPWISE = "STEPWISE"
    FUNCTION = "FUNCTION"
    GIVEN_ALGORITHM = "GIVEN_ALGORITHM"


class FailureType(str, Enum):
    CLEAN = "clean"
    TOKEN_STARVED = "token_starved"
    INTENTIONAL_TRUNCATION = "intentional_truncation"
    GENUINE_COLLAPSE = "genuine_collapse"


@dataclass(slots=True)
class PuzzleInstance:
    puzzle_type: str
    complexity: int
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VerifierResult:
    correct: bool
    first_error_move_index: int | None
    move_count: int
    optimal_move_count: int | None = None
    notes: str = ""


@dataclass(slots=True)
class TrialResult:
    experiment_id: str
    puzzle_type: str
    model: str
    condition: ExperimentCondition
    token_budget: TokenBudget
    trial_index: int
    complexity: int
    correct: bool
    failure_type: FailureType
    output_tokens: int
    thinking_tokens: int | None
    truncated: bool
    truncation_detected: bool
    stop_reason: str | None
    raw_response: str
    moves_output: int
    moves_required: int | None
    first_error_move: int | None
    latency_ms: float


@dataclass(slots=True)
class ComplexityCell:
    puzzle_type: str
    model: str
    complexity: int
    condition: ExperimentCondition
    token_budget: TokenBudget
    trials: list[TrialResult] = field(default_factory=list)


@dataclass(slots=True)
class ExperimentReport:
    run_id: str
    cells: list[ComplexityCell]
    summary: dict[str, Any]

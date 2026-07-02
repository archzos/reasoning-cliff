from __future__ import annotations

from reasoning_cliff.metrics import accuracy, classify_failure, classify_failure_for_cell, effort_score
from reasoning_cliff.models import ExperimentCondition, FailureType, TokenBudget, TrialResult


def test_effort_score_prefers_thinking_tokens():
    assert effort_score(output_tokens=100, thinking_tokens=80, final_answer_tokens=10) == 80


def test_effort_score_fallback_to_output_minus_answer():
    assert effort_score(output_tokens=100, thinking_tokens=None, final_answer_tokens=25) == 75


def test_classify_failure_clean():
    f = classify_failure({"DEFAULT": True, "DOUBLE": True, "UNCAPPED": True}, truncation_detected=False)
    assert f == FailureType.CLEAN


def test_classify_failure_intentional_truncation():
    f = classify_failure({"DEFAULT": False, "DOUBLE": False, "UNCAPPED": False}, truncation_detected=True)
    assert f == FailureType.INTENTIONAL_TRUNCATION


def test_classify_failure_token_starved():
    f = classify_failure({"DEFAULT": False, "DOUBLE": False, "UNCAPPED": True}, truncation_detected=False)
    assert f == FailureType.TOKEN_STARVED


def test_classify_failure_genuine_collapse():
    f = classify_failure({"DEFAULT": False, "DOUBLE": False, "UNCAPPED": False}, truncation_detected=False)
    assert f == FailureType.GENUINE_COLLAPSE


def test_classify_failure_for_cell_token_starved():
    base = {
        "experiment_id": "e1",
        "puzzle_type": "hanoi",
        "model": "gpt-4o",
        "condition": ExperimentCondition.TOKEN_CONTROLLED,
        "trial_index": 0,
        "complexity": 8,
        "output_tokens": 100,
        "thinking_tokens": None,
        "truncated": False,
        "truncation_detected": False,
        "stop_reason": "stop",
        "raw_response": "",
        "moves_output": 0,
        "moves_required": 255,
        "first_error_move": 0,
        "latency_ms": 1.0,
    }
    trials = [
        TrialResult(**base, token_budget=TokenBudget.DEFAULT, correct=False, failure_type=FailureType.GENUINE_COLLAPSE),
        TrialResult(**base, token_budget=TokenBudget.UNCAPPED, correct=True, failure_type=FailureType.CLEAN),
    ]
    assert classify_failure_for_cell(trials) == FailureType.TOKEN_STARVED

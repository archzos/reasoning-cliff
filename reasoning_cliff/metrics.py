"""Metrics and failure classification."""

from __future__ import annotations

from collections import defaultdict

from reasoning_cliff.models import FailureType, TrialResult


def accuracy(results: list[TrialResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for result in results if result.correct) / len(results)


def effort_score(output_tokens: int, thinking_tokens: int | None, final_answer_tokens: int = 0) -> int:
    if thinking_tokens is not None:
        return max(0, thinking_tokens)
    return max(0, output_tokens - final_answer_tokens)


def classify_failure(results_by_budget: dict[str, bool], truncation_detected: bool = False) -> FailureType:
    if results_by_budget.get("DEFAULT", False):
        return FailureType.CLEAN
    if truncation_detected:
        return FailureType.INTENTIONAL_TRUNCATION
    if results_by_budget.get("UNCAPPED", False):
        return FailureType.TOKEN_STARVED
    return FailureType.GENUINE_COLLAPSE


def classify_failure_for_cell(cell_results: list[TrialResult]) -> FailureType:
    by_budget = defaultdict(list)
    trunc_detected = False
    for result in cell_results:
        by_budget[result.token_budget.value].append(result.correct)
        trunc_detected = trunc_detected or result.truncation_detected

    aggregated = {
        "DEFAULT": any(by_budget.get("DEFAULT", [])),
        "DOUBLE": any(by_budget.get("DOUBLE", [])),
        "UNCAPPED": any(by_budget.get("UNCAPPED", [])),
    }
    return classify_failure(aggregated, truncation_detected=trunc_detected)


def collapse_threshold(results: list[TrialResult]) -> int | None:
    """Find smallest n where genuine-collapse accuracy drops below 0.5."""
    grouped: dict[int, list[TrialResult]] = defaultdict(list)
    for result in results:
        if result.failure_type == FailureType.GENUINE_COLLAPSE:
            grouped[result.complexity].append(result)

    for n in sorted(grouped):
        if accuracy(grouped[n]) < 0.5:
            return n
    return None

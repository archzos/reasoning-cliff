"""Blocksworld placeholder (Day 2 stretch)."""

from __future__ import annotations

from reasoning_cliff.models import PuzzleInstance, VerifierResult


def generate_blocksworld_instance(complexity: int) -> PuzzleInstance:
    prompt = (
        "Blocksworld stretch target is out of scope for Day 1. "
        "Provide a legal sequence of pick/place operations that reaches the goal configuration."
    )
    return PuzzleInstance(
        puzzle_type="blocksworld",
        complexity=complexity,
        prompt=prompt,
        metadata={"status": "stretch"},
    )


def verify_blocksworld_solution(_: int, __: str) -> VerifierResult:
    return VerifierResult(
        correct=False,
        first_error_move_index=0,
        move_count=0,
        optimal_move_count=None,
        notes="blocksworld_not_implemented_in_v1",
    )

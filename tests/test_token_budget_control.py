from __future__ import annotations

from reasoning_cliff.runner import get_token_budgets, is_token_constrained


def test_budget_levels_present():
    budgets = get_token_budgets("gpt-4o")
    assert budgets["DEFAULT"] == 4096
    assert budgets["DOUBLE"] == 8192
    assert budgets["UNCAPPED"] == 32000


def test_hanoi_token_constraint_detection():
    assert is_token_constrained("hanoi", 10, "gpt-4o") is True
    assert is_token_constrained("hanoi", 4, "gpt-4o") is False


def test_river_not_marked_token_constrained_by_default():
    assert is_token_constrained("river_crossing", 5, "gpt-4o") is False

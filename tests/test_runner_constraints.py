from __future__ import annotations

from reasoning_cliff.cli import _filter_complexities_for_puzzles


def test_filter_complexities_no_river_crossing():
    values = _filter_complexities_for_puzzles(["hanoi"], [2, 3, 6, 10])
    assert values == [2, 3, 6, 10]


def test_filter_complexities_with_river_crossing_enforces_v1_limit():
    values = _filter_complexities_for_puzzles(["hanoi", "river_crossing"], [1, 2, 5, 6, 7, 10])
    assert values == [1, 2, 5]

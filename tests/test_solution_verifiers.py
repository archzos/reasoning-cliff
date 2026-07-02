from __future__ import annotations

import pytest

from reasoning_cliff.puzzles.river_crossing import parse_river_crossing_moves, verify_river_crossing_solution
from reasoning_cliff.puzzles.tower_of_hanoi import hanoi_ground_truth, parse_hanoi_moves, verify_hanoi_solution


def test_hanoi_verifier_accepts_ground_truth():
    moves = [(src, dst) for src, _, dst in hanoi_ground_truth(3)]
    result = verify_hanoi_solution(3, moves)
    assert result.correct is True
    assert result.move_count == 7


def test_hanoi_verifier_fails_illegal_move():
    result = verify_hanoi_solution(3, [(0, 2), (0, 2)])
    assert result.correct is False
    assert result.first_error_move_index == 1


def test_hanoi_parser_detects_truncation():
    text = "(0,1)\n(0,2)\nThe pattern continues, I'll stop here"
    moves, truncated = parse_hanoi_moves(text)
    assert len(moves) == 2
    assert truncated is True


def test_river_crossing_parser_and_verifier():
    raw = "-> 1M 1C\n<- 0M 1C\n-> 0M 2C"
    moves = parse_river_crossing_moves(raw)
    result = verify_river_crossing_solution(1, 3, moves)
    assert isinstance(result.correct, bool)


def test_river_crossing_verifier_rejects_unsolvable_instance():
    with pytest.raises(ValueError):
        verify_river_crossing_solution(6, 3, [])

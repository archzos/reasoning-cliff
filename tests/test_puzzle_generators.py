from __future__ import annotations

from reasoning_cliff.puzzles.river_crossing import generate_river_crossing_instance, verify_river_crossing_solvability
from reasoning_cliff.puzzles.tower_of_hanoi import generate_hanoi_instance, hanoi_ground_truth, required_hanoi_output_tokens


def test_hanoi_ground_truth_move_counts():
    for n in range(2, 7):
        assert len(hanoi_ground_truth(n)) == 2**n - 1


def test_hanoi_generator_contains_move_count():
    instance = generate_hanoi_instance(4)
    assert instance.metadata["moves_required"] == 15
    assert "Output ALL 15 moves" in instance.prompt


def test_hanoi_token_requirements():
    assert required_hanoi_output_tokens(8) == 2550
    assert required_hanoi_output_tokens(10) == 10230


def test_river_crossing_generator_rejects_unsolvable():
    assert verify_river_crossing_solvability(6, 3) is False


def test_river_crossing_generator_for_valid_case():
    instance = generate_river_crossing_instance(4, boat_capacity=3)
    assert instance.puzzle_type == "river_crossing"

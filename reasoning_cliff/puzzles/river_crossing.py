"""River Crossing generator and verifier."""

from __future__ import annotations

import re
from collections import deque

from reasoning_cliff.models import PuzzleInstance, VerifierResult

RIVER_CROSSING_SOLVABILITY = {
    (1, 2): True,
    (2, 2): False,
    (3, 2): False,
    (1, 3): True,
    (2, 3): True,
    (3, 3): True,
    (4, 3): True,
    (5, 3): True,
    (6, 3): False,
    (7, 3): False,
    (8, 3): False,
    (1, 4): True,
    (2, 4): True,
    (3, 4): True,
    (4, 4): True,
    (5, 4): True,
    (6, 4): True,
    (7, 4): True,
    (8, 4): True,
    (10, 4): True,
}

RIVER_STANDARD_PROMPT = """You are solving a River Crossing puzzle.

SETUP:
- {n} missionaries and {n} cannibals are on the LEFT bank
- One boat with capacity {boat_capacity} is on the LEFT bank
- Goal: move everyone to the RIGHT bank

RULES:
- Boat needs at least 1 person to cross
- Boat carries at most {boat_capacity} people
- Missionaries must never be outnumbered by cannibals on EITHER bank
  (unless there are 0 missionaries on that bank)

This puzzle HAS a valid solution. Output the complete crossing sequence.

FORMAT: Each line = one crossing
Direction -> means left to right, <- means right to left
Example: "-> 2M 1C" means 2 missionaries and 1 cannibal cross left to right

Output every crossing. Verify your solution is complete before submitting."""


def river_crossing_bfs(n_pairs: int, boat_capacity: int) -> list[tuple[int, int, bool]] | None:
    start = (n_pairs, n_pairs, True)
    goal = (0, 0, False)
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        (ml, cl, boat_left), path = queue.popleft()
        if (ml, cl, boat_left) == goal:
            return path

        moves = [
            (m, c)
            for m in range(boat_capacity + 1)
            for c in range(boat_capacity + 1)
            if 1 <= m + c <= boat_capacity
        ]

        for dm, dc in moves:
            if boat_left:
                nm, nc, nb = ml - dm, cl - dc, False
            else:
                nm, nc, nb = ml + dm, cl + dc, True

            if not (0 <= nm <= n_pairs and 0 <= nc <= n_pairs):
                continue

            if nm > 0 and nm < nc:
                continue

            mr, cr = n_pairs - nm, n_pairs - nc
            if mr > 0 and mr < cr:
                continue

            state = (nm, nc, nb)
            if state not in visited:
                visited.add(state)
                queue.append((state, path + [state]))

    return None


def verify_river_crossing_solvability(n_pairs: int, boat_capacity: int) -> bool:
    if boat_capacity == 3 and n_pairs > 5:
        return False
    known = RIVER_CROSSING_SOLVABILITY.get((n_pairs, boat_capacity))
    if known is not None:
        return known
    return river_crossing_bfs(n_pairs, boat_capacity) is not None


def get_valid_river_crossing_suite(boat_capacity: int = 3) -> list[int]:
    return [n for n in range(1, 20) if verify_river_crossing_solvability(n, boat_capacity)]


def parse_river_crossing_moves(raw_output: str) -> list[tuple[bool, int, int]]:
    moves: list[tuple[bool, int, int]] = []
    for line in raw_output.splitlines():
        text = line.strip().lower()
        if not text:
            continue
        direction_lr = "->" in text or "→" in text
        direction_rl = "<-" in text or "←" in text
        if not direction_lr and not direction_rl:
            continue

        m_match = re.search(r"(\d+)\s*m", text)
        c_match = re.search(r"(\d+)\s*c", text)
        m = int(m_match.group(1)) if m_match else 0
        c = int(c_match.group(1)) if c_match else 0
        moves.append((direction_lr, m, c))
    return moves


def verify_river_crossing_solution(
    n_pairs: int,
    boat_capacity: int,
    moves: list[tuple[bool, int, int]],
) -> VerifierResult:
    if not verify_river_crossing_solvability(n_pairs, boat_capacity):
        raise ValueError(f"unsolvable instance n={n_pairs}, b={boat_capacity}")

    ml = n_pairs
    cl = n_pairs
    boat_left = True

    for i, (left_to_right, m, c) in enumerate(moves):
        if m + c < 1 or m + c > boat_capacity:
            return VerifierResult(False, i, len(moves), None, "illegal_boat_load")
        if left_to_right != boat_left:
            return VerifierResult(False, i, len(moves), None, "wrong_boat_direction")

        if left_to_right:
            ml -= m
            cl -= c
            boat_left = False
        else:
            ml += m
            cl += c
            boat_left = True

        if not (0 <= ml <= n_pairs and 0 <= cl <= n_pairs):
            return VerifierResult(False, i, len(moves), None, "invalid_population")

        if ml > 0 and ml < cl:
            return VerifierResult(False, i, len(moves), None, "left_bank_violation")
        mr = n_pairs - ml
        cr = n_pairs - cl
        if mr > 0 and mr < cr:
            return VerifierResult(False, i, len(moves), None, "right_bank_violation")

    solved = ml == 0 and cl == 0 and not boat_left
    return VerifierResult(
        correct=solved,
        first_error_move_index=None if solved else len(moves),
        move_count=len(moves),
        optimal_move_count=None,
        notes="",
    )


def generate_river_crossing_instance(complexity: int, boat_capacity: int = 3) -> PuzzleInstance:
    if not verify_river_crossing_solvability(complexity, boat_capacity):
        raise ValueError(f"Unsolvable river crossing instance n={complexity}, b={boat_capacity}")
    return PuzzleInstance(
        puzzle_type="river_crossing",
        complexity=complexity,
        prompt=RIVER_STANDARD_PROMPT.format(n=complexity, boat_capacity=boat_capacity),
        metadata={"boat_capacity": boat_capacity},
    )

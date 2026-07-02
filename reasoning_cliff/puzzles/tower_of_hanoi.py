"""Tower of Hanoi generator and verifier."""

from __future__ import annotations

import re
from dataclasses import dataclass

from reasoning_cliff.models import PuzzleInstance, VerifierResult

TRUNCATION_PHRASES = [
    "the pattern continues",
    "to avoid making this too long",
    "i'll stop here",
    "following this pattern",
    "and so on",
    "etc.",
    "continuing this pattern",
    "truncating for brevity",
    "the remaining moves follow",
    "i could continue but",
]

HANOI_STANDARD_PROMPT = """You are solving the Tower of Hanoi puzzle.

RULES:
- There are {n} disks numbered 1 (smallest) to {n} (largest)
- Three pegs: 0, 1, 2
- Initial state: all disks on peg 0, disk {n} at bottom, disk 1 at top
- Goal: move all disks to peg 2 in the same order
- You may only move the TOP disk of any peg
- You may never place a larger disk on a smaller disk

OUTPUT FORMAT:
List every single move as: (source_peg, destination_peg)
Example for 2 disks:
(0, 1)
(0, 2)
(1, 2)

Output ALL {moves_required} moves. Do not abbreviate or summarize.
Do not say "and so on" or "the pattern continues."
Output every move explicitly."""

HANOI_FUNCTION_PROMPT = """You are solving the Tower of Hanoi puzzle.

RULES:
- {n} disks numbered 1 (smallest) to {n} (largest)
- Three pegs: 0, 1, 2
- Initial: all disks on peg 0
- Goal: all disks on peg 2
- May only move top disk; never place larger on smaller

OUTPUT FORMAT:
Write a Python function that returns the complete move list:

def generate_hanoi_solution(n: int) -> list[tuple[int, int]]:
    # Your implementation here
    ...

Then call: print(generate_hanoi_solution({n}))

Do not output the moves directly. Output the function and the call.
The function must work for any n, not just {n}."""

HANOI_ALGORITHM_PROMPT = """You are solving Tower of Hanoi. Here is the optimal algorithm:

ALGORITHM (recursive):
To move n disks from src to dst using via:
  1. Move (n-1) disks from src to via, using dst
  2. Move disk n from src to dst
  3. Move (n-1) disks from via to dst, using src

Base case: to move 1 disk from src to dst: output (src, dst)

Apply this algorithm to move {n} disks from peg 0 to peg 2 using peg 1.

Output ALL {moves_required} moves explicitly as (source, destination).
Do not abbreviate. Execute every step of the algorithm."""

HANOI_STEPWISE_SYSTEM = """You are solving Tower of Hanoi one move at a time.
Rules: {n} disks, pegs 0/1/2, disk {n} largest, start peg 0, goal peg 2.
Never place larger disk on smaller. Only move top disk.
Respond with EXACTLY ONE move in format: (source, destination)
Nothing else. One move only."""

HANOI_STEPWISE_USER = """Current state:
Peg 0: {peg0}  (top is rightmost)
Peg 1: {peg1}
Peg 2: {peg2}

Move {step_number} of approximately {total_moves}. What is your next move?"""


def required_hanoi_output_tokens(n: int, tokens_per_move: int = 10) -> int:
    return (2**n - 1) * tokens_per_move


def hanoi_ground_truth(n: int, src: int = 0, dst: int = 2, via: int = 1) -> list[tuple[int, int, int]]:
    """Exact optimal Tower of Hanoi sequence."""
    if n < 1:
        return []
    if n == 1:
        return [(src, via, dst)]
    return (
        hanoi_ground_truth(n - 1, src, via, dst)
        + [(src, via, dst)]
        + hanoi_ground_truth(n - 1, via, dst, src)
    )


class HanoiState:
    def __init__(self, n_disks: int):
        self.pegs = [list(range(n_disks, 0, -1)), [], []]
        self.n = n_disks

    def apply_move(self, src: int, dst: int) -> bool:
        if src not in (0, 1, 2) or dst not in (0, 1, 2):
            return False
        if not self.pegs[src]:
            return False
        disk = self.pegs[src][-1]
        if self.pegs[dst] and self.pegs[dst][-1] < disk:
            return False
        self.pegs[src].pop()
        self.pegs[dst].append(disk)
        return True

    def is_solved(self) -> bool:
        goal = list(range(self.n, 0, -1))
        return self.pegs[2] == goal and not self.pegs[0] and not self.pegs[1]


def parse_hanoi_moves(raw_output: str) -> tuple[list[tuple[int, int]], bool]:
    lowered = raw_output.lower()
    truncated = any(phrase in lowered for phrase in TRUNCATION_PHRASES)

    pattern_a = re.findall(r"\((\d+),\s*(\d+)\)", raw_output)
    if pattern_a:
        return [(int(s), int(d)) for s, d in pattern_a], truncated

    pattern_d = re.findall(r"\[(\d+),\s*(\d+),\s*(\d+)\]", raw_output)
    if pattern_d:
        return [(int(s), int(d)) for s, _, d in pattern_d], truncated

    pattern_c = re.findall(r"(\d+)\s*[-→>]+\s*(\d+)", raw_output)
    if pattern_c:
        return [(int(s), int(d)) for s, d in pattern_c], truncated

    pattern_b = re.findall(
        r"(?:from|move[^0-9]+)peg\s*(\d+)[^0-9]+(?:to|onto)\s*peg\s*(\d+)",
        raw_output,
        re.IGNORECASE,
    )
    if pattern_b:
        return [(int(s), int(d)) for s, d in pattern_b], truncated

    return [], truncated


def verify_hanoi_solution(n_disks: int, moves: list[tuple[int, int]]) -> VerifierResult:
    state = HanoiState(n_disks)
    for i, (src, dst) in enumerate(moves):
        if not state.apply_move(src, dst):
            return VerifierResult(
                correct=False,
                first_error_move_index=i,
                move_count=len(moves),
                optimal_move_count=2**n_disks - 1,
                notes="illegal_move",
            )

    solved = state.is_solved()
    optimal = 2**n_disks - 1
    if solved and len(moves) == optimal:
        return VerifierResult(
            correct=True,
            first_error_move_index=None,
            move_count=len(moves),
            optimal_move_count=optimal,
        )

    return VerifierResult(
        correct=False,
        first_error_move_index=None,
        move_count=len(moves),
        optimal_move_count=optimal,
        notes="wrong_final_state_or_move_count",
    )


def generate_hanoi_instance(complexity: int, condition: str = "STANDARD") -> PuzzleInstance:
    moves_required = 2**complexity - 1
    if condition == "FUNCTION":
        prompt = HANOI_FUNCTION_PROMPT.format(n=complexity)
    elif condition == "GIVEN_ALGORITHM":
        prompt = HANOI_ALGORITHM_PROMPT.format(n=complexity, moves_required=moves_required)
    else:
        prompt = HANOI_STANDARD_PROMPT.format(n=complexity, moves_required=moves_required)

    return PuzzleInstance(
        puzzle_type="hanoi",
        complexity=complexity,
        prompt=prompt,
        metadata={"moves_required": moves_required},
    )

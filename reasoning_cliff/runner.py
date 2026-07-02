"""Experiment runner orchestration."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reasoning_cliff.adapters.bedrock_adapter import BedrockAdapter
from reasoning_cliff.adapters.openai_adapter import OpenAIAdapter
from reasoning_cliff.metrics import classify_failure
from reasoning_cliff.models import ExperimentCondition, FailureType, TokenBudget, TrialResult
from reasoning_cliff.puzzles.river_crossing import (
    generate_river_crossing_instance,
    parse_river_crossing_moves,
    verify_river_crossing_solution,
)
from reasoning_cliff.puzzles.tower_of_hanoi import (
    HANOI_STEPWISE_SYSTEM,
    HANOI_STEPWISE_USER,
    generate_hanoi_instance,
    parse_hanoi_moves,
    required_hanoi_output_tokens,
    verify_hanoi_solution,
)
from reasoning_cliff.report.store import initialize_db, insert_trial

MODEL_DEFAULTS = {
    "claude-sonnet-4-6": 8192,
    "gpt-4o": 4096,
    "o1": 32768,
    "o3": 32768,
}

MODEL_PRICING = {
    "claude-sonnet-4-6": (0.003, 0.015),
    "gpt-4o": (0.005, 0.015),
    "o1": (0.015, 0.060),
}


@dataclass(slots=True)
class MockAdapterResponse:
    text: str
    output_tokens: int
    thinking_tokens: int | None
    truncated: bool
    stop_reason: str | None
    latency_ms: float


class MockReasoningAdapter:
    """Deterministic adapter for dry-run/tests/examples."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str, max_tokens: int, thinking_budget: int | None = None) -> MockAdapterResponse:
        start = time.perf_counter()
        # Emit very short pseudo output to exercise failure classification paths.
        text = "(0, 1)\n(0, 2)\n(1, 2)"
        if "Do not output the moves directly" in prompt:
            text = "def generate_hanoi_solution(n: int):\n    return [(0,1),(0,2),(1,2)]\nprint(generate_hanoi_solution(2))"
        latency_ms = (time.perf_counter() - start) * 1000
        approx_tokens = max(1, len(text.split()))
        truncated = approx_tokens >= max_tokens
        return MockAdapterResponse(
            text=text,
            output_tokens=approx_tokens,
            thinking_tokens=min(approx_tokens + 5, max_tokens) if "hanoi" in prompt.lower() else None,
            truncated=truncated,
            stop_reason="max_tokens" if truncated else "stop",
            latency_ms=latency_ms,
        )


def _load_model_config(config_path: str) -> dict[str, Any]:
    payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return dict(payload.get("models", {}))


def _can_use_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _can_use_bedrock() -> bool:
    return bool(os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"))


def _build_adapter(model: str, model_config: dict[str, Any], allow_live_adapters: bool) -> Any:
    if not allow_live_adapters:
        return MockReasoningAdapter(model)

    config = model_config.get(model, {})
    provider = str(config.get("provider", "")).lower()

    if provider == "openai" and _can_use_openai():
        return OpenAIAdapter(config.get("model_id", model))

    if provider == "bedrock" and _can_use_bedrock():
        return BedrockAdapter(
            model_id=config.get("model_id", model),
            region=os.getenv("AWS_REGION", "ap-south-1"),
        )

    return MockReasoningAdapter(model)


def get_token_budgets(model: str) -> dict[str, int]:
    default = MODEL_DEFAULTS.get(model, 4096)
    return {
        TokenBudget.DEFAULT.value: default,
        TokenBudget.DOUBLE.value: default * 2,
        TokenBudget.UNCAPPED.value: 32000,
    }


def is_token_constrained(puzzle_type: str, n: int, model: str) -> bool:
    if puzzle_type == "hanoi":
        required = required_hanoi_output_tokens(n)
        return required > MODEL_DEFAULTS.get(model, 4096)
    return False


def estimate_experiment_cost(
    models: list[str],
    puzzles: list[str],
    n_values: list[int],
    conditions: list[str],
    token_budgets: list[str],
    trials_per_cell: int,
    avg_input_tokens: int = 500,
) -> dict[str, float]:
    breakdown: dict[str, float] = {}
    for model in models:
        in_price, out_price = MODEL_PRICING.get(model, (0.01, 0.03))
        total = 0.0
        for puzzle in puzzles:
            for n in n_values:
                expected_output = required_hanoi_output_tokens(n) if puzzle == "hanoi" else max(120, n * 20)
                for condition in conditions:
                    budgets = token_budgets if condition == "TOKEN_CONTROLLED" else [TokenBudget.DEFAULT.value]
                    for budget in budgets:
                        limit = get_token_budgets(model).get(budget, MODEL_DEFAULTS.get(model, 4096))
                        output_tokens = min(expected_output, limit)
                        trial_cost = (avg_input_tokens / 1000 * in_price) + (output_tokens / 1000 * out_price)
                        total += trial_cost * trials_per_cell
        breakdown[model] = round(total, 4)
    return breakdown


def _normalize_condition(value: str) -> ExperimentCondition:
    return ExperimentCondition(value)


def _build_stepwise_prompt(n: int, pegs: list[list[int]], step: int, total_moves: int) -> str:
    system = HANOI_STEPWISE_SYSTEM.format(n=n)
    user = HANOI_STEPWISE_USER.format(
        peg0=pegs[0],
        peg1=pegs[1],
        peg2=pegs[2],
        step_number=step,
        total_moves=total_moves,
    )
    return f"{system}\n\n{user}"


def run_stepwise_trial(n: int, adapter: Any, max_steps: int, max_tokens: int) -> tuple[bool, int | None, int, dict[str, Any]]:
    from reasoning_cliff.puzzles.tower_of_hanoi import HanoiState

    state = HanoiState(n)
    for step in range(max_steps):
        prompt = _build_stepwise_prompt(n, state.pegs, step + 1, max_steps)
        response = adapter.generate(prompt, max_tokens=min(max_tokens, 256))
        moves, truncated_detected = parse_hanoi_moves(response.text)
        if not moves:
            return False, step, step, {
                "output_tokens": response.output_tokens,
                "thinking_tokens": response.thinking_tokens,
                "truncated": response.truncated,
                "stop_reason": response.stop_reason,
                "raw_response": response.text,
                "truncation_detected": truncated_detected,
                "latency_ms": response.latency_ms,
            }
        src, dst = moves[0]
        if not state.apply_move(src, dst):
            return False, step, step, {
                "output_tokens": response.output_tokens,
                "thinking_tokens": response.thinking_tokens,
                "truncated": response.truncated,
                "stop_reason": response.stop_reason,
                "raw_response": response.text,
                "truncation_detected": truncated_detected,
                "latency_ms": response.latency_ms,
            }
        if state.is_solved():
            return True, None, step + 1, {
                "output_tokens": response.output_tokens,
                "thinking_tokens": response.thinking_tokens,
                "truncated": response.truncated,
                "stop_reason": response.stop_reason,
                "raw_response": response.text,
                "truncation_detected": truncated_detected,
                "latency_ms": response.latency_ms,
            }

    return False, max_steps, max_steps, {
        "output_tokens": 0,
        "thinking_tokens": None,
        "truncated": False,
        "stop_reason": "max_steps",
        "raw_response": "",
        "truncation_detected": False,
        "latency_ms": 0.0,
    }


def run_experiments(
    config_path: str,
    output_db: str,
    models: list[str],
    puzzles: list[str],
    n_values: list[int],
    token_budgets: list[str],
    trials: int,
    conditions: list[str],
    dry_run: bool = False,
    allow_live_adapters: bool = False,
) -> int:
    if dry_run:
        Path(config_path).read_text(encoding="utf-8")
        return 0

    initialize_db(output_db)
    model_config = _load_model_config(config_path)

    adapters: dict[str, Any] = {
        model: _build_adapter(model, model_config, allow_live_adapters=allow_live_adapters) for model in models
    }

    inserted = 0
    for model in models:
        adapter = adapters[model]
        budget_map = get_token_budgets(model)

        for puzzle in puzzles:
            for n in n_values:
                if puzzle == "river_crossing" and n > 5:
                    # Hard constraint for b=3 in v1.
                    continue
                for condition_name in conditions:
                    condition = _normalize_condition(condition_name)
                    budget_keys = token_budgets if condition == ExperimentCondition.TOKEN_CONTROLLED else [TokenBudget.DEFAULT.value]
                    for budget_key in budget_keys:
                        budget = TokenBudget(budget_key)
                        max_tokens = budget_map[budget_key]
                        pending_trials: list[dict[str, Any]] = []

                        for trial_idx in range(trials):
                            experiment_id = str(uuid.uuid4())
                            start = time.perf_counter()

                            if puzzle == "hanoi":
                                if condition == ExperimentCondition.STEPWISE:
                                    ok, first_error, move_count, stepwise = run_stepwise_trial(
                                        n=n,
                                        adapter=adapter,
                                        max_steps=(2**n - 1) + 20,
                                        max_tokens=max_tokens,
                                    )
                                    correct = ok
                                    first_error_move = first_error
                                    moves_output = move_count
                                    moves_required = 2**n - 1
                                    output_tokens = int(stepwise["output_tokens"])
                                    thinking_tokens = stepwise["thinking_tokens"]
                                    truncated = bool(stepwise["truncated"])
                                    stop_reason = str(stepwise["stop_reason"])
                                    raw = str(stepwise["raw_response"])
                                    truncation_detected = bool(stepwise["truncation_detected"])
                                else:
                                    instance = generate_hanoi_instance(n, condition=condition.value)
                                    response = adapter.generate(instance.prompt, max_tokens=max_tokens)
                                    moves, truncation_detected = parse_hanoi_moves(response.text)
                                    verify = verify_hanoi_solution(n, moves)

                                    correct = verify.correct
                                    first_error_move = verify.first_error_move_index
                                    moves_output = verify.move_count
                                    moves_required = verify.optimal_move_count
                                    output_tokens = response.output_tokens
                                    thinking_tokens = response.thinking_tokens
                                    truncated = response.truncated
                                    stop_reason = response.stop_reason
                                    raw = response.text
                            elif puzzle == "river_crossing":
                                instance = generate_river_crossing_instance(n, boat_capacity=3)
                                response = adapter.generate(instance.prompt, max_tokens=max_tokens)
                                moves = parse_river_crossing_moves(response.text)
                                verify = verify_river_crossing_solution(n, 3, moves)

                                correct = verify.correct
                                first_error_move = verify.first_error_move_index
                                moves_output = verify.move_count
                                moves_required = None
                                output_tokens = response.output_tokens
                                thinking_tokens = response.thinking_tokens
                                truncated = response.truncated
                                stop_reason = response.stop_reason
                                raw = response.text
                                truncation_detected = False
                            else:
                                continue

                            latency_ms = (time.perf_counter() - start) * 1000
                            pending_trials.append(
                                {
                                    "experiment_id": experiment_id,
                                    "puzzle_type": puzzle,
                                    "model": model,
                                    "condition": condition,
                                    "token_budget": budget,
                                    "trial_index": trial_idx,
                                    "complexity": n,
                                    "correct": correct,
                                    "output_tokens": output_tokens,
                                    "thinking_tokens": thinking_tokens,
                                    "truncated": truncated,
                                    "truncation_detected": truncation_detected,
                                    "stop_reason": stop_reason,
                                    "raw_response": raw,
                                    "moves_output": moves_output,
                                    "moves_required": moves_required,
                                    "first_error_move": first_error_move,
                                    "latency_ms": latency_ms,
                                }
                            )

                        # Classify this budget cell after all trials are complete.
                        budget_outcomes = {
                            TokenBudget.DEFAULT.value: any(t["correct"] for t in pending_trials if t["token_budget"] == TokenBudget.DEFAULT),
                            TokenBudget.DOUBLE.value: any(t["correct"] for t in pending_trials if t["token_budget"] == TokenBudget.DOUBLE),
                            TokenBudget.UNCAPPED.value: any(t["correct"] for t in pending_trials if t["token_budget"] == TokenBudget.UNCAPPED),
                        }
                        trunc_detected_any = any(t["truncation_detected"] for t in pending_trials)
                        cell_failure_type = classify_failure(budget_outcomes, truncation_detected=trunc_detected_any)

                        for trial_data in pending_trials:
                            trial = TrialResult(
                                experiment_id=trial_data["experiment_id"],
                                puzzle_type=trial_data["puzzle_type"],
                                model=trial_data["model"],
                                condition=trial_data["condition"],
                                token_budget=trial_data["token_budget"],
                                trial_index=trial_data["trial_index"],
                                complexity=trial_data["complexity"],
                                correct=trial_data["correct"],
                                failure_type=FailureType.CLEAN if trial_data["correct"] else cell_failure_type,
                                output_tokens=trial_data["output_tokens"],
                                thinking_tokens=trial_data["thinking_tokens"],
                                truncated=trial_data["truncated"],
                                truncation_detected=trial_data["truncation_detected"],
                                stop_reason=trial_data["stop_reason"],
                                raw_response=trial_data["raw_response"],
                                moves_output=trial_data["moves_output"],
                                moves_required=trial_data["moves_required"],
                                first_error_move=trial_data["first_error_move"],
                                latency_ms=trial_data["latency_ms"],
                            )
                            insert_trial(output_db, trial)
                            inserted += 1

    return inserted

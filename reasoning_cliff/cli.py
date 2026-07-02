"""CLI entrypoint for reasoning-cliff."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from reasoning_cliff.puzzles.river_crossing import verify_river_crossing_solvability
from reasoning_cliff.runner import estimate_experiment_cost, run_experiments


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_range(value: str) -> list[int]:
    if ":" in value:
        start, end = value.split(":", 1)
        return list(range(int(start), int(end) + 1))
    return [int(v.strip()) for v in value.split(",") if v.strip()]


def _filter_complexities_for_puzzles(puzzles: list[str], n_values: list[int]) -> list[int]:
    if "river_crossing" not in puzzles:
        return n_values
    filtered = [n for n in n_values if n <= 5 and verify_river_crossing_solvability(n, 3)]
    return filtered


def _load_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reasoning-cliff")
    sub = parser.add_subparsers(dest="command", required=True)

    estimate = sub.add_parser("estimate")
    estimate.add_argument("--config", required=True)
    estimate.add_argument("--models", required=True)
    estimate.add_argument("--dry-run", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--models", required=True)
    run.add_argument("--puzzles", required=True)
    run.add_argument("--complexity-range", required=True)
    run.add_argument("--token-budgets", default="DEFAULT,DOUBLE,UNCAPPED")
    run.add_argument("--trials", type=int, default=5)
    run.add_argument("--conditions", default="STANDARD,TOKEN_CONTROLLED,STEPWISE,FUNCTION")
    run.add_argument("--output-db", required=True)
    run.add_argument("--live-adapters", action="store_true")
    run.add_argument("--dry-run", action="store_true")

    plot = sub.add_parser("plot")
    plot.add_argument("--db", required=True)
    plot.add_argument("--output-dir", required=True)
    plot.add_argument("--dry-run", action="store_true")

    demo = sub.add_parser("demo")
    demo.add_argument("--model", required=True)
    demo.add_argument("--puzzle", required=True)
    demo.add_argument("--output-db", required=True)
    demo.add_argument("--dry-run", action="store_true")

    return parser


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mpl")
    args = build_parser().parse_args()

    if args.command == "estimate":
        config = _load_config(args.config)
        models = _parse_csv(args.models)
        if args.dry_run:
            print(json.dumps({"ok": True, "models": models}, indent=2))
            return

        n_values = config["puzzles"]["hanoi"]["n_range"]
        costs = estimate_experiment_cost(
            models=models,
            puzzles=["hanoi", "river_crossing"],
            n_values=n_values,
            conditions=config["conditions"],
            token_budgets=list(config["token_budget_levels"].keys()),
            trials_per_cell=config["trials_per_cell"],
        )
        total = round(sum(costs.values()), 4)
        cells = (
            len(models)
            * len(["hanoi", "river_crossing"])
            * len(n_values)
            * config["trials_per_cell"]
            * len(config["conditions"])
        )
        print(json.dumps({"per_model_usd": costs, "total_usd": total, "approx_cells": cells}, indent=2))
        return

    if args.command == "run":
        puzzles = _parse_csv(args.puzzles)
        n_values = _parse_range(args.complexity_range)
        n_values = _filter_complexities_for_puzzles(puzzles, n_values)
        inserted = run_experiments(
            config_path=args.config,
            output_db=args.output_db,
            models=_parse_csv(args.models),
            puzzles=puzzles,
            n_values=n_values,
            token_budgets=[v.upper() for v in _parse_csv(args.token_budgets)],
            trials=args.trials,
            conditions=[v.upper() for v in _parse_csv(args.conditions)],
            dry_run=args.dry_run,
            allow_live_adapters=args.live_adapters,
        )
        print(json.dumps({"inserted_rows": inserted, "db": args.output_db}, indent=2))
        return

    if args.command == "plot":
        from reasoning_cliff.plots.visualizer import generate_all_plots

        if args.dry_run:
            print(json.dumps({"ok": True, "db": args.db, "output_dir": args.output_dir}, indent=2))
            return
        paths = [str(path) for path in generate_all_plots(args.db, args.output_dir)]
        print(json.dumps({"generated": paths}, indent=2))
        return

    if args.command == "demo":
        config_path = "config/experiment_config.json"
        if args.dry_run:
            print(json.dumps({"ok": True, "model": args.model, "puzzle": args.puzzle}, indent=2))
            return
        inserted = run_experiments(
            config_path=config_path,
            output_db=args.output_db,
            models=[args.model],
            puzzles=[args.puzzle],
            n_values=[3, 4, 5, 6, 7, 8],
            token_budgets=["DEFAULT", "UNCAPPED"],
            trials=3,
            conditions=["STANDARD", "TOKEN_CONTROLLED"],
            dry_run=False,
        )
        print(json.dumps({"demo_rows": inserted, "db": args.output_db}, indent=2))


if __name__ == "__main__":
    main()

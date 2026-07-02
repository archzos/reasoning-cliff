"""Matplotlib visualizations for collapse and effort curves."""

from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


def plot_collapse_curve(db_path: str, output_dir: str, puzzle: str = "hanoi") -> Path:
    conn = duckdb.connect(db_path, read_only=True)
    df = conn.execute(
        """
        SELECT model, n, token_budget, AVG(correct::INT) AS accuracy
        FROM experiments
        WHERE puzzle_type = ?
        GROUP BY model, n, token_budget
        ORDER BY model, n, token_budget
        """,
        [puzzle],
    ).df()
    conn.close()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    models = df["model"].unique() if not df.empty else []
    if len(models) == 0:
        path = out_dir / f"collapse_curve_{puzzle}.png"
        plt.figure(figsize=(8, 4))
        plt.title("No data")
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        return path

    fig, axes = plt.subplots(1, len(models), figsize=(6 * len(models), 5), sharey=True)
    if len(models) == 1:
        axes = [axes]

    budgets = ["DEFAULT", "DOUBLE", "UNCAPPED"]
    colors = {"DEFAULT": "#e74c3c", "DOUBLE": "#f39c12", "UNCAPPED": "#27ae60"}
    styles = {"DEFAULT": "-", "DOUBLE": "--", "UNCAPPED": ":"}

    for ax, model in zip(axes, models):
        model_df = df[df["model"] == model]
        for budget in budgets:
            budget_df = model_df[model_df["token_budget"] == budget].sort_values("n")
            if budget_df.empty:
                continue
            ax.plot(
                budget_df["n"],
                budget_df["accuracy"],
                marker="o",
                linestyle=styles[budget],
                color=colors[budget],
                label=budget,
            )
        ax.axhline(0.5, color="gray", linestyle=":", linewidth=1, alpha=0.5)
        ax.set_title(f"{model} - {puzzle}")
        ax.set_xlabel("Complexity N")
        ax.set_ylabel("Accuracy")
        ax.set_ylim(-0.05, 1.05)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)

    fig.suptitle("Accuracy vs Complexity: Reasoning Cliff")
    plt.tight_layout()
    path = out_dir / f"collapse_curve_{puzzle}.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    return path


def plot_effort_curve(db_path: str, output_dir: str, puzzle: str = "hanoi") -> Path:
    conn = duckdb.connect(db_path, read_only=True)
    df = conn.execute(
        """
        SELECT model, n,
               AVG(COALESCE(thinking_tokens, output_tokens)) AS mean_effort,
               AVG(correct::INT) AS accuracy
        FROM experiments
        WHERE puzzle_type = ?
        GROUP BY model, n
        ORDER BY model, n
        """,
        [puzzle],
    ).df()
    conn.close()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    models = df["model"].unique() if not df.empty else []
    if len(models) == 0:
        path = out_dir / f"effort_curve_{puzzle}.png"
        plt.figure(figsize=(8, 4))
        plt.title("No data")
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        return path

    fig, axes = plt.subplots(1, len(models), figsize=(6 * len(models), 5))
    if len(models) == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_df = df[df["model"] == model].sort_values("n")
        ax2 = ax.twinx()
        ax.plot(model_df["n"], model_df["mean_effort"], color="#8e44ad", marker="s", label="Effort")
        ax2.plot(model_df["n"], model_df["accuracy"], color="#e74c3c", marker="o", linestyle="--", label="Accuracy")
        ax.set_xlabel("Complexity N")
        ax.set_ylabel("Mean effort tokens", color="#8e44ad")
        ax2.set_ylabel("Accuracy", color="#e74c3c")
        ax2.set_ylim(-0.05, 1.05)
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
        ax.set_title(model)
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Effort vs Complexity")
    plt.tight_layout()
    path = out_dir / f"effort_curve_{puzzle}.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    return path


def plot_token_budget_comparison(db_path: str, output_dir: str, model: str, puzzle: str = "hanoi") -> Path:
    conn = duckdb.connect(db_path, read_only=True)
    df = conn.execute(
        """
        SELECT n,
               SUM(CASE WHEN failure_type='token_starved' THEN 1 ELSE 0 END) AS token_starved,
               SUM(CASE WHEN failure_type='genuine_collapse' THEN 1 ELSE 0 END) AS genuine_collapse,
               SUM(CASE WHEN failure_type='intentional_truncation' THEN 1 ELSE 0 END) AS intentional
        FROM experiments
        WHERE puzzle_type = ? AND model = ?
        GROUP BY n
        ORDER BY n
        """,
        [puzzle, model],
    ).df()
    conn.close()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if df.empty:
        path = out_dir / f"budget_comparison_{puzzle}_{model}.png"
        plt.figure(figsize=(8, 4))
        plt.title("No data")
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        return path

    x = np.arange(len(df))
    width = 0.25

    plt.figure(figsize=(10, 5))
    plt.bar(x - width, df["token_starved"], width, label="Token-Starved", color="#f39c12")
    plt.bar(x, df["genuine_collapse"], width, label="Genuine Collapse", color="#e74c3c")
    plt.bar(x + width, df["intentional"], width, label="Intentional Truncation", color="#95a5a6")
    plt.xticks(x, df["n"])
    plt.xlabel("Complexity N")
    plt.ylabel("Failure Count")
    plt.title(f"Token Budget Comparison - {model} - {puzzle}")
    plt.legend()
    plt.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()

    path = out_dir / f"budget_comparison_{puzzle}_{model.replace('/', '_')}.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    return path


def generate_all_plots(db_path: str, output_dir: str) -> list[Path]:
    paths: list[Path] = []

    conn = duckdb.connect(db_path, read_only=True)
    puzzles = [row[0] for row in conn.execute("SELECT DISTINCT puzzle_type FROM experiments ORDER BY puzzle_type").fetchall()]
    models = [row[0] for row in conn.execute("SELECT DISTINCT model FROM experiments ORDER BY model").fetchall()]
    conn.close()

    for puzzle in puzzles:
        paths.append(plot_collapse_curve(db_path, output_dir, puzzle=puzzle))
        paths.append(plot_effort_curve(db_path, output_dir, puzzle=puzzle))

    for model in models:
        for puzzle in puzzles:
            paths.append(plot_token_budget_comparison(db_path, output_dir, model=model, puzzle=puzzle))
    return paths

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reasoning_cliff.plots.visualizer import generate_all_plots


if __name__ == "__main__":
    paths = generate_all_plots("report/results.duckdb", "outputs/figures")
    for path in paths:
        print(path)

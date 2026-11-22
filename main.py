"""Run CS 421 Project 2: exact almost-equal graph coloring from a text file."""

import argparse
from pathlib import Path

from graph_coloring import find_almost_equal_coloring, format_result, read_graph


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find a minimum-imbalance proper coloring using exactly k colors."
    )
    default_input = Path(__file__).resolve().parent / "sample_inputs" / "example_k3.txt"
    parser.add_argument("input_file", nargs="?", type=Path, default=default_input,
                        help="File: first line k, second line n, then n adjacency-matrix rows")
    args = parser.parse_args()
    try:
        k, matrix = read_graph(args.input_file)
        result = find_almost_equal_coloring(matrix, k)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Input error: {exc}\n")
    print(format_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Exact minimum-imbalance coloring for a simple, connected undirected graph.

A color sequence is sorted in nonincreasing order, and the objective is
    sum(abs(counts[i] - counts[i + 1]) for i in range(k - 1)).
For a sorted sequence, this equals max(counts) - min(counts).
Every one of the k colors must be used at least once.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ColoringResult:
    """A proper coloring, with groups ordered by decreasing class size."""

    sequence: tuple[int, ...]
    groups: tuple[tuple[int, ...], ...]  # 1-based vertex IDs
    imbalance: int


def read_graph(path: str | Path) -> tuple[int, list[list[int]]]:
    """Read k, n, and exactly n whitespace-delimited adjacency-matrix rows."""
    path = Path(path)
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    if len(lines) < 2:
        raise ValueError("The input file must begin with k and n on separate lines.")
    try:
        if len(lines[0].split()) != 1 or len(lines[1].split()) != 1:
            raise ValueError("k and n must each appear alone on their own line.")
        k, n = int(lines[0]), int(lines[1])
    except ValueError as exc:
        raise ValueError("The first two lines must contain integers k and n.") from exc

    if k < 1 or n < 1:
        raise ValueError("k and n must both be positive integers.")
    if len(lines) != n + 2:
        raise ValueError(f"Expected {n} adjacency rows; found {len(lines) - 2}.")

    matrix = []
    for index, line in enumerate(lines[2:], start=1):
        try:
            row = [int(item) for item in line.split()]
        except ValueError as exc:
            raise ValueError(f"Adjacency row {index} contains a noninteger.") from exc
        if len(row) != n:
            raise ValueError(f"Adjacency row {index} must contain exactly {n} numbers.")
        if any(entry not in (0, 1) for entry in row):
            raise ValueError("Adjacency entries must be 0 or 1.")
        matrix.append(row)

    validate_graph(matrix)
    return k, matrix


def validate_graph(matrix: list[list[int]]) -> None:
    """Verify that an adjacency matrix describes a simple connected graph."""
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("The adjacency matrix must be nonempty and square.")
    for i in range(n):
        if matrix[i][i] != 0:
            raise ValueError("A simple graph cannot have self-loops.")
        for j in range(n):
            if matrix[i][j] not in (0, 1):
                raise ValueError("Adjacency entries must be 0 or 1.")
            if matrix[i][j] != matrix[j][i]:
                raise ValueError("The adjacency matrix must be symmetric.")

    # BFS also validates connectedness, which the assignment assumes.
    reached = {0}
    queue = [0]
    for vertex in queue:
        for neighbor, adjacent in enumerate(matrix[vertex]):
            if adjacent == 1 and neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    if len(reached) != n:
        raise ValueError("The graph must be connected.")


def find_almost_equal_coloring(matrix: list[list[int]], k: int) -> Optional[ColoringResult]:
    """Find a proper coloring using exactly k colors with minimum imbalance.

    The algorithm uses DSATUR-style vertex selection and exhaustive
    backtracking with color-symmetry breaking and safe branch-and-bound.
    It is exact, but its worst-case time is exponential.
    """
    validate_graph(matrix)
    if k < 1:
        raise ValueError("k must be positive.")
    n = len(matrix)
    if k > n:
        return None  # Cannot give every color a nonempty class.

    adjacency = [[j for j, value in enumerate(row) if value] for row in matrix]
    degree = [len(neighbors) for neighbors in adjacency]
    assigned = [-1] * n
    counts = [0] * k
    best_assignment: Optional[tuple[int, ...]] = None
    best_range = n + 1
    global_floor = 0 if n % k == 0 else 1

    def select_vertex() -> int:
        """Uncolored vertex with highest saturation, then degree, then lower ID."""
        winner = -1
        winner_key = (-1, -1, -n)
        for vertex in range(n):
            if assigned[vertex] != -1:
                continue
            neighbor_colors = {assigned[u] for u in adjacency[vertex]
                               if assigned[u] != -1}
            key = (len(neighbor_colors), degree[vertex], -vertex)
            if key > winner_key:
                winner, winner_key = vertex, key
        return winner

    def search(colored: int, used: int) -> None:
        nonlocal best_assignment, best_range
        if best_range == global_floor:
            return  # Cannot beat the mathematical lower bound.
        remaining = n - colored
        if used + remaining < k:
            return  # Not enough vertices left to give all k colors a vertex.
        if colored == n:
            if used == k:
                difference = max(counts) - min(counts)
                if difference < best_range:
                    best_range = difference
                    best_assignment = tuple(assigned)
            return

        # Ignore adjacency constraints: even if every uncolored vertex goes
        # into a smallest class, its size cannot exceed min_count+remaining.
        # Therefore a smaller final difference is impossible when this bound
        # is at least our existing best difference.
        lower_bound = max(0, max(counts) - min(counts) - remaining)
        if lower_bound >= best_range:
            return

        vertex = select_vertex()
        forbidden = {assigned[u] for u in adjacency[vertex] if assigned[u] != -1}

        # Assign the current vertex to an existing color if legal.
        # Smaller classes first increases the chance of finding balance early.
        choices = sorted((c for c in range(used) if c not in forbidden),
                         key=lambda c: (counts[c], c))
        # All unused colors are symmetric; introduce only the next one.
        if used < k:
            choices.append(used)

        for color in choices:
            is_new = color == used
            assigned[vertex] = color
            counts[color] += 1
            search(colored + 1, used + int(is_new))
            counts[color] -= 1
            assigned[vertex] = -1
            if best_range == global_floor:
                return

    search(0, 0)
    if best_assignment is None:
        return None

    groups = []
    for color in range(k):
        group = tuple(vertex + 1 for vertex, assigned_color in enumerate(best_assignment)
                      if assigned_color == color)
        groups.append(group)
    # Match the definition n_1 >= n_2 >= ... >= n_k. Ties can be broken
    # arbitrarily; use larger summed vertex degree, then lower vertex IDs.
    # This also reproduces the handout's Blue/Red/Yellow order for its example.
    groups.sort(key=lambda group: (-len(group),
                                   -sum(degree[v - 1] for v in group), group))
    sequence = tuple(len(group) for group in groups)
    return ColoringResult(sequence, tuple(groups), max(sequence) - min(sequence))


def format_result(result: Optional[ColoringResult]) -> str:
    """Format the color sequence and the 1-based vertices of each class."""
    if result is None:
        return "no such a sequence exists."
    names = ["Blue", "Red", "Yellow", "Green", "Orange", "Purple",
             "Cyan", "Magenta", "Brown", "Pink"]
    sequence = "(" + ",".join(map(str, result.sequence)) + ")"
    rows = [sequence]
    for i, group in enumerate(result.groups):
        color_name = names[i] if i < len(names) else f"Color {i + 1}"
        vertices = ", ".join(map(str, group))
        rows.append(f"{color_name:<8}: {vertices}")
    return "\n".join(rows)

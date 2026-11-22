"""Exact minimum-imbalance coloring for a simple, connected undirected graph.

A color sequence is sorted in nonincreasing order, and the objective is
    sum(abs(counts[i] - counts[i + 1]) for i in range(k - 1)).
For a sorted sequence, this equals max(counts) - min(counts).
Every one of the k colors must be used at least once.
"""

from collections.abc import Iterator
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
    if n == 0 or any(not isinstance(row, (list, tuple)) or len(row) != n
                     for row in matrix):
        raise ValueError("The adjacency matrix must be nonempty and square.")
    for i in range(n):
        if matrix[i][i] != 0:
            raise ValueError("A simple graph cannot have self-loops.")
        for j in range(n):
            if type(matrix[i][j]) is not int or matrix[i][j] not in (0, 1):
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
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer.")
    n = len(matrix)
    if k > n:
        return None  # Cannot give every color a nonempty class.

    adjacency = [[j for j, value in enumerate(row) if value] for row in matrix]
    degree = [len(neighbors) for neighbors in adjacency]
    if k == n:
        assignment = tuple(range(n))
    elif k == 1:
        return None  # A connected graph with more than one vertex has an edge.
    elif k == 2:
        assignment = two_color(adjacency)
    else:
        assignment = search_coloring(adjacency, degree, k)
    if assignment is None:
        return None

    groups = [[] for _ in range(k)]
    for vertex, color in enumerate(assignment, start=1):
        groups[color].append(vertex)
    # Match the definition n_1 >= n_2 >= ... >= n_k. Ties can be broken
    # arbitrarily; use larger summed vertex degree, then lower vertex IDs.
    # This also reproduces the handout's Blue/Red/Yellow order for its example.
    groups.sort(key=lambda group: (-len(group),
                                   -sum(degree[v - 1] for v in group), group))
    sequence = tuple(len(group) for group in groups)
    return ColoringResult(sequence, tuple(map(tuple, groups)), sequence[0] - sequence[-1])


def two_color(adjacency: list[list[int]]) -> Optional[tuple[int, ...]]:
    """A connected bipartite graph has one bipartition up to swapping colors."""
    colors = [-1] * len(adjacency)
    colors[0] = 0
    queue = [0]
    for vertex in queue:
        opposite = 1 - colors[vertex]
        for neighbor in adjacency[vertex]:
            if colors[neighbor] == -1:
                colors[neighbor] = opposite
                queue.append(neighbor)
            elif colors[neighbor] != opposite:
                return None
    return tuple(colors)


def search_coloring(adjacency: list[list[int]], degree: list[int],
                    k: int) -> Optional[tuple[int, ...]]:
    n = len(adjacency)
    assigned = [-1] * n
    forbidden = [0] * n
    counts = [0] * k
    capacities = [n] * k
    best_assignment = None
    best_range = n + 1
    floor, remainder = divmod(n, k)

    def branches(colored: int, used: int) -> Iterator[tuple[int, int]]:
        nonlocal best_assignment, best_range
        remaining = n - colored
        if remaining < k - used:
            return
        if not remaining:
            difference = max(counts) - min(counts)
            if difference < best_range:
                best_range = difference
                best_assignment = tuple(assigned)
            return

        if best_assignment is not None:
            # To beat the incumbent by one, the largest class must fit
            # within this upper limit. The smallest class is bounded by
            # the average, by available vertices, and by class capacities.
            smallest_upper = min(floor, min(counts) + remaining, min(capacities))
            largest_upper = smallest_upper + best_range - 1
            if max(counts) > largest_upper:
                return
            if sum(min(capacity, largest_upper) for capacity in capacities) < n:
                return
            # Every final class is within the target range of a largest
            # class, whose size is at least its current size or ceil(n/k).
            largest_lower = max(max(counts), floor + bool(remainder))
            smallest_lower = max(1, largest_lower - best_range + 1)
            if sum(max(0, smallest_lower - size) for size in counts) > remaining:
                return

        vertex = max((v for v in range(n) if assigned[v] == -1),
                     key=lambda v: (forbidden[v].bit_count(), degree[v], -v))
        # Only introduce the next unused color. When every remaining vertex
        # must open a class, skip the existing colors entirely.
        choices = []
        if remaining > k - used:
            choices = sorted((c for c in range(used) if not forbidden[vertex] & (1 << c)),
                             key=lambda c: (counts[c], c))
        if used < k:
            choices.insert(0, used)

        for color in choices:
            bit = 1 << color
            assigned[vertex] = color
            counts[color] += 1
            old_capacity = capacities[color]
            # A class containing this vertex cannot contain its neighbors.
            capacities[color] = min(old_capacity, n - degree[vertex])
            changed = []
            for neighbor in adjacency[vertex]:
                if assigned[neighbor] == -1 and not forbidden[neighbor] & bit:
                    forbidden[neighbor] |= bit
                    changed.append(neighbor)
            yield colored + 1, used + (color == used)
            for neighbor in changed:
                forbidden[neighbor] ^= bit
            capacities[color] = old_capacity
            counts[color] -= 1
            assigned[vertex] = -1

    # Each suspended iterator owns one assignment and undoes it when resumed.
    # Keeping the search stack explicitly avoids Python's recursion limit.
    stack = [branches(0, 0)]
    while stack and best_range != bool(remainder):
        child = next(stack[-1], None)
        if child is None:
            stack.pop()
        else:
            stack.append(branches(*child))
    return best_assignment


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

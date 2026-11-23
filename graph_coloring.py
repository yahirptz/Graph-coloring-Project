"""Exact minimum-imbalance coloring for a simple, connected undirected graph.

We sort the color sequence in nonincreasing order and minimize
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

    # We use BFS because the assignment requires a connected graph.
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

    For the general case, we use DSATUR vertex selection and exact
    depth-first backtracking with color symmetry breaking and branch-and-bound.
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
    # We break size ties by total degree, then by vertex IDs. This also
    # reproduces the handout's Blue/Red/Yellow order.
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


@dataclass
class SearchFrame:
    """The remaining choices and undo information for one vertex."""

    vertex: int
    used_colors: int
    choices: Iterator[int]
    previous_capacity: int = 0


def search_coloring(adjacency: list[list[int]], degree: list[int],
                    k: int) -> Optional[tuple[int, ...]]:
    n = len(adjacency)
    assigned = [-1] * n
    counts = [0] * k
    capacities = [n] * k
    best_assignment = None
    best_imbalance = n + 1
    average_floor, remainder = divmod(n, k)
    minimum_possible = int(remainder != 0)

    def can_improve(remaining: int) -> bool:
        # A better coloring must have imbalance at most best_imbalance - 1.
        # Bound the smallest class by the average, the remaining vertices,
        # and the tightest class capacity.
        smallest_upper = min(average_floor, min(counts) + remaining, min(capacities))
        largest_upper = smallest_upper + best_imbalance - 1
        if max(counts) > largest_upper:
            return False
        if sum(min(capacity, largest_upper) for capacity in capacities) < n:
            return False

        # Each class must get close enough to the largest eventual class.
        largest_lower = max(max(counts), average_floor + minimum_possible)
        smallest_lower = max(1, largest_lower - best_imbalance + 1)
        needed = sum(max(0, smallest_lower - count) for count in counts)
        return needed <= remaining

    def neighbor_colors(vertex: int) -> set[int]:
        return {assigned[u] for u in adjacency[vertex] if assigned[u] != -1}

    def make_frame(remaining: int, used_colors: int) -> Optional[SearchFrame]:
        missing_colors = k - used_colors
        if remaining < missing_colors:
            return None
        if best_assignment is not None and not can_improve(remaining):
            return None

        # We choose the uncolored vertex with the most distinct neighbor
        # colors, then prefer higher degree and lower vertex ID.
        vertex = max((v for v in range(n) if assigned[v] == -1),
                     key=lambda v: (len(neighbor_colors(v)), degree[v], -v))
        forbidden = neighbor_colors(vertex)
        choices = []
        # Unused colors are interchangeable, so we try only the next one.
        if missing_colors:
            choices.append(used_colors)
        if remaining > missing_colors:
            choices.extend(sorted((c for c in range(used_colors) if c not in forbidden),
                                  key=lambda c: (counts[c], c)))
        return SearchFrame(vertex, used_colors, iter(choices))

    # We use a depth-first stack so even inputs beyond Python's recursion
    # limit can use the same backtracking routine.
    first = make_frame(n, 0)
    stack = [first] if first is not None else []
    while stack and best_imbalance > minimum_possible:
        frame = stack[-1]
        vertex = frame.vertex

        # On return from a child (or a complete coloring), undo our last try.
        previous_color = assigned[vertex]
        if previous_color != -1:
            assigned[vertex] = -1
            counts[previous_color] -= 1
            capacities[previous_color] = frame.previous_capacity

        color = next(frame.choices, None)
        if color is None:
            stack.pop()
            continue

        assigned[vertex] = color
        counts[color] += 1
        frame.previous_capacity = capacities[color]
        # A class containing this vertex cannot contain any of its neighbors.
        capacities[color] = min(capacities[color], n - degree[vertex])
        remaining = n - len(stack)
        if remaining == 0:
            imbalance = max(counts) - min(counts)
            if imbalance < best_imbalance:
                best_imbalance = imbalance
                best_assignment = tuple(assigned)
        else:
            used_colors = frame.used_colors + int(color == frame.used_colors)
            child = make_frame(remaining, used_colors)
            if child is not None:
                stack.append(child)

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

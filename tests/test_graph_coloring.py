"""Run with: python -m unittest discover -s tests -v"""

import itertools
import random
import tempfile
import unittest
from pathlib import Path

from graph_coloring import (
    find_almost_equal_coloring,
    format_result,
    read_graph,
    validate_graph,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "sample_inputs"


def independent_optimum(matrix, k):
    """Small-case exhaustive reference with NO DSATUR or symmetry breaking."""
    n = len(matrix)
    best = None
    for colors in itertools.product(range(k), repeat=n):
        if set(colors) != set(range(k)):
            continue
        if any(matrix[i][j] and colors[i] == colors[j]
               for i in range(n) for j in range(i + 1, n)):
            continue
        amounts = [colors.count(c) for c in range(k)]
        score = max(amounts) - min(amounts)
        if best is None or score < best:
            best = score
    return best


class GraphColoringTests(unittest.TestCase):
    def assert_valid_optimal(self, matrix, k, expected_score):
        result = find_almost_equal_coloring(matrix, k)
        if expected_score is None:
            self.assertIsNone(result)
            return
        self.assertIsNotNone(result)
        self.assertEqual(len(result.groups), k)
        self.assertEqual(tuple(sorted(result.sequence, reverse=True)), result.sequence)
        self.assertEqual(sum(result.sequence), len(matrix))
        self.assertTrue(all(size > 0 for size in result.sequence))
        self.assertEqual(result.imbalance, expected_score)
        self.assertEqual(result.imbalance,
                         sum(abs(a - b) for a, b in zip(result.sequence, result.sequence[1:])))
        all_vertices = [v for group in result.groups for v in group]
        self.assertEqual(sorted(all_vertices), list(range(1, len(matrix) + 1)))
        for group in result.groups:
            for a, b in itertools.combinations(group, 2):
                self.assertEqual(matrix[a - 1][b - 1], 0)

    def test_assignment_k3_matches_handout_sequence(self):
        k, matrix = read_graph(SAMPLES / "example_k3.txt")
        self.assertEqual(k, 3)
        self.assert_valid_optimal(matrix, k, 0)
        output = format_result(find_almost_equal_coloring(matrix, k))
        self.assertEqual(output, "(2,2,2)\nBlue    : 2, 6\nRed     : 3, 4\nYellow  : 1, 5")

    def test_assignment_k2_is_impossible(self):
        k, matrix = read_graph(SAMPLES / "example_k2.txt")
        self.assert_valid_optimal(matrix, k, None)
        self.assertEqual(format_result(None), "no such a sequence exists.")

    def test_path_8_three_colors_is_3_3_2(self):
        k, matrix = read_graph(SAMPLES / "path8_k3.txt")
        self.assert_valid_optimal(matrix, k, 1)

    def test_star_requires_unbalanced_classes(self):
        k, matrix = read_graph(SAMPLES / "star_k2.txt")
        self.assert_valid_optimal(matrix, k, 4)
        self.assertEqual(find_almost_equal_coloring(matrix, k).sequence, (5, 1))

    def test_odd_cycle(self):
        k, matrix = read_graph(SAMPLES / "cycle5_k3.txt")
        self.assert_valid_optimal(matrix, k, 1)

    def test_complete_graph(self):
        k, matrix = read_graph(SAMPLES / "complete4_k4.txt")
        self.assert_valid_optimal(matrix, k, 0)

    def test_one_vertex(self):
        k, matrix = read_graph(SAMPLES / "single_vertex_k1.txt")
        self.assert_valid_optimal(matrix, k, 0)
        self.assert_valid_optimal(matrix, 2, None)

    def test_k_exceeds_n(self):
        _, matrix = read_graph(SAMPLES / "triangle_k3.txt")
        self.assert_valid_optimal(matrix, 4, None)

    def test_k1_on_graph_with_edge_has_no_solution(self):
        _, matrix = read_graph(SAMPLES / "triangle_k3.txt")
        self.assert_valid_optimal(matrix, 1, None)

    def test_invalid_matrix_inputs(self):
        invalid = [
            ([[0, 1], [0, 0]], "symmetric"),
            ([[1, 0], [0, 0]], "self-loops"),
            ([[0, 0], [0, 0]], "connected"),
            ([[0, 2], [2, 0]], "0 or 1"),
            ([[0, 1], [1]], "square"),
        ]
        for graph, message in invalid:
            with self.subTest(graph=graph), self.assertRaisesRegex(ValueError, message):
                validate_graph(graph)

    def test_invalid_files(self):
        content = [
            "3\n2\n0 1\n1 0\n0 0\n",  # Extra row
            "3\n2\n0 1\n1\n",         # Short row
            "0\n1\n0\n",             # Invalid k
            "2\n2\n0 1\n0 0\n",     # Asymmetric
            "2\n2\n0 0\n0 0\n",     # Disconnected
            "two\n1\n0\n",         # Invalid integer
        ]
        for text in content:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "graph.txt"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_graph(path)

    def test_against_independent_brute_force_random_connected_graphs(self):
        rng = random.Random(421)
        cases = 0
        for n in range(2, 8):
            for _ in range(12):
                # Start with a random spanning tree, add random other edges.
                matrix = [[0] * n for _ in range(n)]
                for v in range(1, n):
                    u = rng.randrange(v)
                    matrix[u][v] = matrix[v][u] = 1
                for u in range(n):
                    for v in range(u + 1, n):
                        if not matrix[u][v] and rng.random() < 0.30:
                            matrix[u][v] = matrix[v][u] = 1
                for k in range(1, min(4, n) + 1):
                    expected = independent_optimum(matrix, k)
                    self.assert_valid_optimal(matrix, k, expected)
                    cases += 1
        self.assertEqual(cases, 252)


if __name__ == "__main__":
    unittest.main()

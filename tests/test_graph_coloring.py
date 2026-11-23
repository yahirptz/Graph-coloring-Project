"""Run with: python -m unittest discover -s tests -v"""

import itertools
import random
import subprocess
import sys
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
    """Enumerate all labeled color assignments for small reference cases."""
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


def adjacency_matrix(n, edges):
    matrix = [[0] * n for _ in range(n)]
    for a, b in edges:
        matrix[a - 1][b - 1] = matrix[b - 1][a - 1] = 1
    return matrix


class GraphColoringTests(unittest.TestCase):
    def assert_valid_optimal(self, matrix, k, expected_score):
        result = find_almost_equal_coloring(matrix, k)
        if expected_score is None:
            self.assertIsNone(result)
            return
        self.assertIsNotNone(result)
        self.assertEqual(len(result.groups), k)
        self.assertEqual(result.sequence, tuple(map(len, result.groups)))
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

    def test_even_cycle_with_two_and_three_colors(self):
        edges = [(v, v + 1) for v in range(1, 6)] + [(6, 1)]
        matrix = adjacency_matrix(6, edges)
        for k in (2, 3):
            with self.subTest(k=k):
                self.assert_valid_optimal(matrix, k, independent_optimum(matrix, k))

    def test_complete_graph(self):
        k, matrix = read_graph(SAMPLES / "complete4_k4.txt")
        self.assert_valid_optimal(matrix, k, 0)

    def test_one_vertex(self):
        k, matrix = read_graph(SAMPLES / "single_vertex_k1.txt")
        self.assert_valid_optimal(matrix, k, 0)
        self.assert_valid_optimal(matrix, 2, None)

    def test_k_exceeds_n(self):
        _, matrix = read_graph(SAMPLES / "triangle_k3.txt")
        self.assert_valid_optimal(matrix, 3, 0)
        self.assert_valid_optimal(matrix, 4, None)

    def test_k1_on_graph_with_edge_has_no_solution(self):
        _, matrix = read_graph(SAMPLES / "triangle_k3.txt")
        self.assert_valid_optimal(matrix, 1, None)

    def test_handout_eight_vertex_tree(self):
        matrix = adjacency_matrix(8, [(1, 2), (2, 3), (3, 4), (4, 5),
                                      (3, 6), (3, 7), (3, 8)])
        for k, sequence in [(2, (5, 3)), (3, (3, 3, 2))]:
            with self.subTest(k=k):
                self.assert_valid_optimal(matrix, k, independent_optimum(matrix, k))
                self.assertEqual(find_almost_equal_coloring(matrix, k).sequence, sequence)

    def test_handout_twenty_vertex_diagram(self):
        # We numbered the handout diagram around the outside first, then
        # across the inside.
        matrix = adjacency_matrix(20, [
            (1, 2), (1, 14), (1, 15), (1, 16), (2, 3), (2, 4),
            (3, 4), (3, 5), (3, 6), (4, 5), (4, 16), (4, 18),
            (5, 6), (5, 7), (5, 18), (6, 7), (6, 8), (7, 8),
            (7, 9), (7, 18), (8, 9), (8, 10), (9, 10), (9, 11),
            (9, 18), (10, 12), (11, 12), (11, 19), (11, 20),
            (12, 13), (12, 20), (13, 14), (13, 20), (14, 15),
            (15, 16), (15, 17), (15, 20), (16, 17), (16, 18),
            (17, 19), (17, 20), (18, 19), (19, 20),
        ])
        self.assert_valid_optimal(matrix, 4, 0)
        self.assert_valid_optimal(matrix, 3, None)

    def test_exact_search_recovers_from_greedy_dsatur_failure(self):
        matrix = adjacency_matrix(7, [
            (1, 2), (1, 3), (1, 7), (2, 3), (2, 4), (2, 7),
            (3, 6), (4, 5), (4, 6), (5, 6), (5, 7),
        ])
        greedy = {}
        while len(greedy) < len(matrix):
            forbidden = {
                v: {color for u, color in greedy.items() if matrix[v][u]}
                for v in range(len(matrix)) if v not in greedy
            }
            vertex = max(forbidden, key=lambda v: (len(forbidden[v]), sum(matrix[v]), -v))
            greedy[vertex] = next(color for color in range(len(matrix))
                                  if color not in forbidden[vertex])
        self.assertEqual(len(set(greedy.values())), 4)
        self.assertEqual(independent_optimum(matrix, 3), 1)
        self.assert_valid_optimal(matrix, 3, 1)

    def test_larger_graphs(self):
        path = adjacency_matrix(80, [(v, v + 1) for v in range(1, 80)])
        self.assert_valid_optimal(path, 5, 0)
        star = adjacency_matrix(80, [(1, v) for v in range(2, 81)])
        self.assert_valid_optimal(star, 3, 39)
        clique = [[int(a != b) for b in range(80)] for a in range(80)]
        self.assert_valid_optimal(clique, 79, None)
        self.assert_valid_optimal(clique, 80, 0)

    def test_search_can_exceed_python_recursion_depth(self):
        n = sys.getrecursionlimit() + 1
        path = adjacency_matrix(n, [(v, v + 1) for v in range(1, n)])
        self.assert_valid_optimal(path, 3, int(n % 3 != 0))

    def test_cli_handout_examples_and_default(self):
        expected = "(2,2,2)\nBlue    : 2, 6\nRed     : 3, 4\nYellow  : 1, 5\n"
        for args, output in [
            ([], expected),
            ([str(SAMPLES / "example_k3.txt")], expected),
            ([str(SAMPLES / "example_k2.txt")], "no such a sequence exists.\n"),
        ]:
            with self.subTest(args=args):
                run = subprocess.run([sys.executable, "-B", str(ROOT / "main.py"), *args],
                                     capture_output=True, text=True, check=True)
                self.assertEqual(run.stdout, output)
                self.assertEqual(run.stderr, "")

    def test_cli_rejects_malformed_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.txt"
            path.write_text("2\n2\n0 1\n0 0\n", encoding="utf-8")
            run = subprocess.run([sys.executable, "-B", str(ROOT / "main.py"), str(path)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(run.stdout, "")
            self.assertIn("symmetric", run.stderr)

    def test_invalid_matrix_inputs(self):
        invalid = [
            ([[0, 1], [0, 0]], "symmetric"),
            ([[1, 0], [0, 0]], "self-loops"),
            ([[0, 0], [0, 0]], "connected"),
            ([[0, 2], [2, 0]], "0 or 1"),
            ([[0, 1], [1]], "square"),
            ([[0, 1], None], "square"),
            ([[0, True], [True, 0]], "0 or 1"),
            ([[0, 1.0], [1.0, 0]], "0 or 1"),
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
                # We start with a spanning tree to guarantee connectivity.
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

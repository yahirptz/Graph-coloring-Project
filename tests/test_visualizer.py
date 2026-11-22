"""Smoke tests for the browser visualizer and its solver adapter."""
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from visualizer import GraphHandler, solve_payload

ROOT = Path(__file__).resolve().parents[1]


class VisualizerTests(unittest.TestCase):
    def test_handout_sample_same_as_command_line_solver(self):
        rows = (ROOT / "sample_inputs/example_k3.txt").read_text().splitlines()
        k, n = int(rows[0]), int(rows[1])
        matrix = [list(map(int, r.split())) for r in rows[2:]]
        result = solve_payload({"k": k, "matrix": matrix})
        self.assertTrue(result["possible"])
        self.assertEqual(result["sequence"], [2, 2, 2])
        self.assertEqual(result["text"], "(2,2,2)\nBlue    : 2, 6\nRed     : 3, 4\nYellow  : 1, 5")

    def test_impossible_case(self):
        rows = (ROOT / "sample_inputs/example_k2.txt").read_text().splitlines()
        matrix = [list(map(int, r.split())) for r in rows[2:]]
        result = solve_payload({"k": 2, "matrix": matrix})
        self.assertFalse(result["possible"])
        self.assertEqual(result["text"], "no such a sequence exists.")

    def test_reject_invalid_graph(self):
        with self.assertRaisesRegex(ValueError, "connected"):
            solve_payload({"k": 2, "matrix": [[0, 0], [0, 0]]})
        with self.assertRaisesRegex(ValueError, "positive"):
            solve_payload({"k": 0, "matrix": [[0]]})

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GraphHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def test_homepage_and_assets(self):
        for url, expected in [
            ("/", b"Graph canvas"),
            ("/app.js", b"function renderGraph"),
            ("/style.css", b".canvas-container"),
        ]:
            with self.subTest(url=url), urlopen(self.base + url) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(expected, response.read())

    def test_sample_endpoint(self):
        with urlopen(self.base + "/api/example?name=triangle_k3") as response:
            data = json.load(response)
        self.assertEqual(data["k"], 3)
        self.assertEqual(data["matrix"], [[0, 1, 1], [1, 0, 1], [1, 1, 0]])

    def test_solve_http_endpoint(self):
        payload = json.dumps({"k": 3, "matrix": [[0, 1, 1], [1, 0, 1], [1, 1, 0]]}).encode()
        request = Request(self.base + "/api/solve", payload, {"Content-Type": "application/json"})
        with urlopen(request) as response:
            result = json.load(response)
        self.assertEqual(result["sequence"], [1, 1, 1])
        self.assertEqual(result["imbalance"], 0)

    def test_reject_unknown_sample_and_malformed_post(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + "/api/example?name=../../private")
        self.assertEqual(ctx.exception.code, 404)
        request = Request(self.base + "/api/solve", b"not json", {"Content-Type": "application/json"})
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()

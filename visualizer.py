"""Launch a local, dependency-free browser editor for CS 421 graph coloring.

Run: python3 visualizer.py
The editor creates an adjacency matrix and uses graph_coloring.py for solutions.
Only listens on your own computer (127.0.0.1).
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlsplit
import webbrowser

from graph_coloring import find_almost_equal_coloring, format_result, read_graph

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "visualizer"
SAMPLES = ROOT / "sample_inputs"
ALLOWED_EXAMPLES = {
    "example_k3", "example_k2", "triangle_k3", "star_k2",
    "cycle5_k3", "path8_k3", "complete4_k4", "single_vertex_k1",
}
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8"}


def solve_payload(payload: dict) -> dict:
    """Validate the editor's input and return the same result as the CLI."""
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object.")
    k = payload.get("k")
    matrix = payload.get("matrix")
    if type(k) is not int or k < 1:
        raise ValueError("The number of colors (k) must be a positive integer.")
    if not isinstance(matrix, list) or not 1 <= len(matrix) <= 80:
        raise ValueError("The graph must contain between 1 and 80 vertices.")
    # The same exact algorithm and adjacency validation as the file program.
    result = find_almost_equal_coloring(matrix, k)
    if result is None:
        return {"possible": False, "text": format_result(None)}
    return {
        "possible": True,
        "sequence": list(result.sequence),
        "groups": [list(group) for group in result.groups],
        "imbalance": result.imbalance,
        "text": format_result(result),
    }


class GraphHandler(BaseHTTPRequestHandler):
    def log_message(self, format_string, *args):
        # Keep terminal output short, but still expose requests and errors.
        print(f"[visualizer] {self.address_string()} {format_string % args}")

    def respond(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def respond_json(self, status: int, obj: dict) -> None:
        self.respond(status, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        url = urlsplit(self.path)
        if url.path == "/api/example":
            name = parse_qs(url.query).get("name", [""])[0]
            if name not in ALLOWED_EXAMPLES:
                self.respond_json(404, {"error": "Sample not found."})
                return
            try:
                k, matrix = read_graph(SAMPLES / (name + ".txt"))
            except (OSError, ValueError) as exc:
                self.respond_json(500, {"error": str(exc)})
                return
            self.respond_json(200, {"k": k, "matrix": matrix})
            return
        if url.path == "/":
            path = WEB / "index.html"
        elif url.path in ("/style.css", "/app.js"):
            path = WEB / url.path.lstrip("/")
        else:
            self.respond(404, b"Not found", "text/plain; charset=utf-8")
            return
        try:
            contents = path.read_bytes()
        except OSError:
            self.respond(404, b"Not found", "text/plain; charset=utf-8")
            return
        self.respond(200, contents, CONTENT_TYPES[path.suffix])

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/solve":
            self.respond_json(404, {"error": "Not found."})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= length <= 1_000_000:
                raise ValueError("Invalid or oversized request.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = solve_payload(payload)
        except ValueError as exc:
            self.respond_json(400, {"error": str(exc)})
            return
        self.respond_json(200, result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Visual interactive graph coloring editor")
    parser.add_argument("--port", type=int, default=8765, help="Local port (default: 8765; use 0 for automatic)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    args = parser.parse_args()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), GraphHandler)
    except OSError as exc:
        parser.exit(2, f"Cannot start the visualizer: {exc}. Try --port 0\n")
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"\nGraph Coloring Visualizer: {url}\nPress Ctrl+C to stop.\n", flush=True)
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nVisualizer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

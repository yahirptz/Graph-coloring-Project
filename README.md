# CS 421 Project 2 — Almost Equal Graph Coloring

We wrote our solution in Python 3.10+ using the standard library. We read `k`, `n`, and a binary adjacency matrix from a file, then find a proper coloring with exactly `k` nonempty classes and minimum imbalance. We report the class sizes and one-based vertex lists.

## Visual graph editor

On a Mac, **double-click `START_VISUALIZER.command`** (you may need to right-click → Open the first time), or open this project folder in Cursor (File → Open Folder), then open its terminal and run:

```bash
python3 visualizer.py
```

We serve the editor locally at **http://127.0.0.1:8765** and allow up to 80 vertices. Keep the terminal open while using it. When finished, press **Ctrl+C** in the terminal to stop the server. If your browser does not open automatically, copy the local URL printed in the terminal and paste it into Chrome/Safari. The visualizer does not need an internet connection or extra Python libraries.

1. **Add vertex:** click empty space on the canvas; vertex IDs are assigned automatically.
2. **Connect:** select the Connect tool, then click two vertices to add an edge. Selecting the same pair again removes it.
3. **Move / Delete:** drag existing vertices with Move, or delete nodes or edges with Delete.
4. **Choose k:** edit Number of colors, then click **Find optimal coloring**. The exact solver colors the nodes and shows the sequence and vertex groups. The playback controls reveal the final coloring one vertex at a time (not the full backtracking search).
5. **Use custom graphs:** choose one of the provided examples or clear the canvas. A live adjacency matrix appears under the drawing.
6. **Import / Export:** export `graph_input.txt` from the editor, then pass the downloaded file’s path to `main.py`. If the file is in the project folder, run `python3 main.py graph_input.txt`. You can import a `.txt` file in the assignment format as well.

**Important:** The assignment specifies a **simple connected** graph. If you draw a disconnected graph, the solver will show an input error until you connect its components. Exact graph coloring can take a long time on large/hard graphs. We use `main.py` for the assignment’s file-input workflow and the editor for interactive demonstrations.

### Troubleshooting the visual editor

- If port 8765 is in use: `python3 visualizer.py --port 0` (it prints a different local URL).
- If it doesn't open a browser: `python3 visualizer.py --no-browser`, then enter the printed URL yourself.
- If `python3` is not found, install Python 3.10 or newer.
- If Python starts but the browser cannot connect, leave the terminal running and use the exact URL displayed there.

## Quick start (command-line version)

1. Open a terminal in this folder.
2. Run the sample from the handout:

   ```bash
   python3 main.py sample_inputs/example_k3.txt
   ```

3. Run the handout's impossible case:

   ```bash
   python3 main.py sample_inputs/example_k2.txt
   ```

4. Run all tests:

   ```bash
   python3 -B -m unittest discover -s tests -v
   ```

Running `python3 main.py` without a filename uses the six-vertex sample by default.

## Input format

First line: positive integer `k`, the number of **distinct, nonempty** colors.  
Second line: positive integer `n`, the number of vertices.  
Next `n` lines: a square, symmetric `n × n` adjacency matrix of zeroes and ones, with **whitespace between every entry** and zero on the diagonal.

Example:

```text
3
6
0 1 1 0 0 0
1 0 1 1 0 0
1 1 0 0 1 1
0 1 0 0 0 1
0 0 1 0 0 1
0 0 1 1 1 0
```

The graph must be connected. For malformed input, we print an error to standard error and exit with status 2.

## Expected output for the handout graph

Our CLI prints the handout’s three-color result.

```text
(2,2,2)
Blue    : 2, 6
Red     : 3, 4
Yellow  : 1, 5
```


For `sample_inputs/example_k2.txt`, the output is:

```text
no such a sequence exists.
```

## Files

- `main.py` — command-line runner (required file input).
- `START_VISUALIZER.command` — optional macOS double-click launcher.
- `visualizer.py` — local web server using Python standard library, with APIs for samples and solving.
- `visualizer/index.html`, `visualizer/style.css`, `visualizer/app.js` — interactive graph drawing, animation, live matrix and TXT import/export.
- `graph_coloring.py` — exact depth-first backtracking solver and input validation.
- `sample_inputs/` — the handout example and edge-case graphs.
- `tests/test_graph_coloring.py`, `tests/test_visualizer.py` — 29 automated tests, including independent brute-force cross-checks on 252 random graph/color cases and visualizer HTTP/API checks.
- `REPORT.md` — full explanation of the technique, data structures, major functions, correctness, complexity, and test results.
- `Project2_Report.docx` — Word report, maintained separately.
- `TEST_RESULTS.txt` — output from our latest full test run.

## Approach and limitations

We minimize the handout’s sum of differences between consecutive class sizes. Because the sizes are sorted, the sum telescopes to the largest class size minus the smallest.

We order the vertices once using their adjacency lists, then use an explicit stack for exact backtracking. We check neighbor colors with sets and use class-size bounds to prune branches. We handle two-color cases with a bipartite traversal. The exact search can take exponential time on difficult instances. Our report gives the complexity analysis and test results.

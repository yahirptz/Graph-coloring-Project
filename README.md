# CS 421 Project 2 — Almost Equal Graph Coloring

A complete **Python 3** solution for the class assignment. It reads the required `k`, `n`, and 0/1 adjacency matrix from a file, finds an optimal proper coloring using **exactly `k` colors**, and prints the size sequence and one-based vertex lists. No third-party packages are required.

## NEW: Visual graph editor (recommended)

On a Mac, **double-click `START_VISUALIZER.command`** (you may need to right-click → Open the first time), or open this project folder in Cursor (File → Open Folder), then open its terminal and run:

```bash
python3 visualizer.py
```

The program opens your **default browser** to a locally hosted editor at **http://127.0.0.1:8765**. Keep the terminal open while using it. When finished, press **Ctrl+C** in the terminal to stop the server. If your browser does not open automatically, copy the local URL printed in the terminal and paste it into Chrome/Safari. The visualizer does not need an internet connection or extra Python libraries.

1. **Add vertex:** click empty space on the canvas; vertex IDs are assigned automatically.
2. **Connect:** select the Connect tool, then click two vertices to add an edge. Selecting the same pair again removes it.
3. **Move / Delete:** drag existing vertices with Move, or delete nodes or edges with Delete.
4. **Choose k:** edit Number of colors, then click **Find optimal coloring**. The exact solver colors the nodes and shows the sequence and vertex groups. The playback controls reveal the final coloring one vertex at a time (not the full backtracking search).
5. **Use custom graphs:** choose one of the provided examples or clear the canvas. A live adjacency matrix appears under the drawing.
6. **Import / Export:** export `graph_input.txt` from the editor, then run `python3 main.py graph_input.txt` to execute the standard assignment interface. You can import a `.txt` file in the assignment format as well.

**Important:** The assignment specifies a **simple connected** graph. If you draw a disconnected graph, the solver will show an input error until you connect its components. Exact graph coloring can take a long time on large/hard graphs. Keep the original `main.py` file-input runner when submitting your project; the visualizer is an extra demonstration tool.

### Troubleshooting the visual editor

- If port 8765 is in use: `python3 visualizer.py --port 0` (it prints a different local URL).
- If it doesn't open a browser: `python3 visualizer.py --no-browser`, then enter the printed URL yourself.
- If `python3` is not found, install Python 3 on your computer.
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
   python3 -m unittest discover -s tests -v
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

The graph must be connected. If the input is malformed, the program prints an informative input error to standard error and exits with status 2.

## Expected output for the handout graph

The program prints a valid version of:

```text
(2,2,2)
Blue    : 1, 5
Red     : 2, 6
Yellow  : 3, 4
```

(The handout labels the same three groups with the colors in a different order. Both are equivalent.)

For `sample_inputs/example_k2.txt`, the output is:

```text
no such a sequence exists.
```

## Files

- `main.py` — command-line runner (required file input).
- `START_VISUALIZER.command` — optional macOS double-click launcher.
- `visualizer.py` — local web server using Python standard library, with APIs for samples and solving.
- `visualizer/index.html`, `visualizer/style.css`, `visualizer/app.js` — interactive graph drawing, animation, live matrix and TXT import/export.
- `graph_coloring.py` — exact DSATUR-ordered backtracking solver and input validation.
- `sample_inputs/` — the handout example and edge-case graphs.
- `tests/test_graph_coloring.py`, `tests/test_visualizer.py` — 19 automated tests, including independent brute-force cross-checks on 252 random graph/color cases and visualizer HTTP/API checks.
- `REPORT.md` — full explanation of the technique, data structures, major functions, correctness, complexity, and test results.
- `Project2_Report.docx` — Word version of the written report.

## Approach and limitations

The objective is to minimize the handout's sum of absolute differences between adjacent, descending class sizes. Since it telescopes to `largest_class - smallest_class`, this is what the solver minimizes exactly.

The algorithm is exact, not a greedy approximation. Consequently, worst-case time is exponential (`O(n² k^n)`), so very large or difficult graphs may take a long time. The code intentionally does not impose a time limit that could silently return a nonoptimal answer.

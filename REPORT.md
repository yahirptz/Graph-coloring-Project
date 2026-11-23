# CS 421 — Project 2: Almost Equal Graph Coloring

**Assignment:** Project 2 (150 points), due November 22, 2026  
**Implementation:** Python 3.10+ and the standard library

## 1. Problem statement and objective

We read the number of colors `k`, the number of vertices `n`, and an `n × n` binary adjacency matrix from a text file. Our input represents a simple, connected, undirected graph. We look for a proper coloring using exactly `k` nonempty classes, so the endpoints of every edge must have different colors.

We sort the class sizes so that `n_1 ≥ n_2 ≥ … ≥ n_k > 0`. The handout defines imbalance as the sum of absolute differences between consecutive sizes. Since each difference is nonnegative, the sum telescopes to the expression below.

`F = |n_1 − n_2| + … + |n_(k−1) − n_k| = n_1 − n_k`.

We minimize that difference and print the sorted sizes and one-based vertex IDs for each group. If no proper coloring uses exactly `k` colors, we print `no such a sequence exists.`

## 2. Problem-solving techniques (10 points)

For the general case, we use exact backtracking. We build one vertex order before the search. At each step we choose the vertex with the most neighbors already in the order, breaking ties by higher degree and then lower vertex ID. The first vertex therefore has the highest degree. This puts edges between early vertices, where a conflict can cut off more of the search. The order depends only on the graph.

We compared natural order and descending degree with the final order. Natural order stalled on an 80-vertex star when the center came last. Plain descending degree was much slower on our set of 65-vertex impossible instances. The fixed order we chose performed well on both sets and preserved the handout’s exact output.

We try the next unused color first, followed by legal existing colors in ascending order of class size and color index. Introducing unused colors in index order avoids equivalent label permutations. We also use branch-and-bound to skip partial assignments that cannot improve our best complete coloring.

We handle several cases directly. When `k > n`, there are too few vertices. When `k = n`, singleton classes give imbalance zero. A connected graph with more than one vertex cannot use one color. For two colors, we traverse the graph with breadth-first search (BFS). A conflict rules out a bipartition. Because the graph is connected, a successful bipartition is unique up to swapping its colors and therefore fixes the class sizes.

These choices connect to Chapters 6–9. We use a priority rule during preprocessing and find the highest-priority vertex with a scan (Chapter 6). We sort legal color choices and analyze the search by depth (Chapter 7). The general solver uses exhaustive backtracking (Chapter 8). We use an adjacency matrix for input, adjacency lists for neighbor checks, DFS for the search, and BFS for connectivity and two-coloring (Chapter 9).

## 3. Data structures (10 points)

| Data structure | Role |
|---|---|
| Adjacency matrix and lists | We read the required matrix and build lists for efficient neighbor traversal. |
| `assigned` and `degree` | We store each vertex’s color, or −1 if uncolored, and its degree for tie-breaking. |
| Vertex order and temporary forbidden-color set | We store a fixed order in a list and collect the current vertex’s colored-neighbor colors in a set. |
| `counts` and `capacities` | We track current sizes and upper bounds on final class sizes. |
| Stack of `SearchFrame` records | Each frame holds its remaining color choices, the number of colors in use before the assignment, and the capacity to restore on undo. The stack depth identifies the vertex. |
| BFS queue and reached set | We use a list as a queue and a set to track connectivity. Two-color BFS tracks visits in its color array. |
| `ColoringResult` | We return the sequence, one-based vertex groups, and optimal imbalance. |

## 4. Major functions (10 points)

| Function | Purpose |
|---|---|
| `main()` in `main.py` | Reads the input path from the command line, runs our solver, and prints the result. |
| `read_graph(path)` | Parses and validates the file and returns the color count and matrix. |
| `validate_graph(matrix)` | Checks matrix shape, binary entries, symmetry, diagonal entries, and connectivity. |
| `find_almost_equal_coloring(matrix, k)` | Validates the input, selects the solving method, and orders the returned groups. |
| `two_color(adjacency)` | Finds a bipartition using BFS or returns `None` if a conflict occurs. |
| `choose_vertex_order(adjacency, degree)` | Builds the fixed vertex order using earlier-neighbor counts and degree. |
| `search_coloring(adjacency, degree, k)` | Tries assignments depth first, undoes them on return, and stores the best complete coloring. |
| `make_frame(remaining, used_colors)` | Nested in `search_coloring`. Rejects infeasible or bounded states and prepares the legal colors at the next depth. |
| `can_improve(remaining)` | Nested in `search_coloring`. Tests necessary class-size and capacity bounds for improving the best result. |
| `format_result(result)` | Returns the formatted sequence and vertex lists or the required impossibility message. |
| `solve_payload(payload)` in `visualizer.py` | Validates the request and packages the shared solver’s result for the browser. |

## 5. Algorithm (pseudocode)

```text
READ and validate k, n, and the adjacency matrix
HANDLE k > n, k = n, k = 1, and k = 2 directly
OTHERWISE build a fixed vertex order and push the first choice frame
WHILE the stack is nonempty and the theoretical minimum has not been reached:
    Undo the top frame's previous assignment, if any
    Use its next legal color, or pop the frame if its choices are exhausted
    Update the assignment, count, and class capacity
    If complete, save the assignment if its imbalance improves the best
    Otherwise, push a child frame unless a pruning rule rules it out

TO BUILD A FRAME:
    Check that enough vertices remain to open every missing class
    Check class-size bounds if a complete coloring has been found
    Collect colors of previously assigned neighbors of the next vertex
    Try one unused color, then legal existing colors by class size

SORT returned groups by descending size and format the output
```

## 6. Correctness argument

**Properness and class count.** When we color the second endpoint of an edge, we collect the first endpoint’s color in the forbidden set. A frame is built only when the remaining vertices can still fill the missing classes. If all remaining vertices must start a class, each has only the new-color choice. On undo, we restore the assignment, count, and capacity before trying the next color.

**Completeness.** For any proper partition, label its classes by their first appearance in our fixed vertex order. At each depth, the resulting color is either a legal existing class or the next unused index. We try both kinds of choices when feasible, which covers every possible partition up to renaming the colors.

**Safe pruning.** Let `B` be the best complete imbalance and `r` the number of remaining vertices. After assigning a vertex of degree `d` to a class, we cap that class at `n − d`, since none of its neighbors can join it. Let `U` be the minimum of the smallest capacity, the smallest current count plus `r`, and `floor(n/k)`. Each term bounds the final smallest class from above. Improving `B` requires every final class to fit under `U + B − 1`. We prune if an existing class already exceeds that limit or if the sum of the class capacities clipped to that limit is less than `n`.

We also use `L = max(largest current count, ceil(n/k))` as a lower bound on the final largest class. To improve `B`, every class must reach at least `max(1, L − B + 1)`. We prune if the sum of the remaining deficits exceeds `r`.

**Optimality.** We stop if the best imbalance reaches zero when `k` divides `n`, or one otherwise. No smaller value is possible. If we exhaust the search first, all other proper partitions were checked or could not beat our best result. If we saved no assignment, no proper coloring with exactly `k` classes exists.

## 7. Complexity analysis (30 points)

Let `n` be the vertex count, `m` the edge count, and `k` the color count. We use an adjacency matrix as required, so parsing a well-formed matrix, validation, and building adjacency lists take `O(n²)` time. The two-color traversal takes `O(n + m)` after the lists are built.

We build the order in `O(n² + m)` time. The repeated maximum scans examine a total of `n + (n−1) + … + 1` candidates. When we place a vertex, we update the counts for its neighbors. We use the standard constant-time membership model for sets of integer vertex and color IDs.

At depth `d`, there are at most `k^d` partial assignments. Each frame scans one neighbor list (at most `n−1` entries), checks bounds over `k` classes, and sorts at most `k` choices in `O(k log k)` time. Trying or undoing a color takes constant time, while scoring a complete coloring costs `O(k)` and saving an improved assignment takes `O(n)`. With at most `O(k^n)` total states for the general case, a conservative time bound is `O(n² + (n + k log k) · k^n)`. The search remains exponential in the worst case. Under a model that charges linear time for each hash-set operation, a looser bound is `O(n² + nm + (nk + k² + k log k) · k^n)`.

The matrix takes `O(n²)` space, and the adjacency lists take `O(n + m)`. We store `O(n + k)` entries for the order, assignments, counts, capacities, and best coloring. The stack has at most `n` frames, each with up to `k` saved choices and constant-size undo information. The temporary forbidden set uses `O(k)` space. The resulting bound is `O(n² + m + nk)`, or `O(n²)` for the valid search range `k ≤ n`.

## 8. Testing and results (100 points)

We ran 29 automated tests, including 20 solver and CLI tests and nine visualizer adapter and HTTP tests. We compared the solver against a separate brute-force enumerator on 252 seeded random graph and color-count combinations. We also compared all 3,807 connected labeled graph and color-count cases on up to five vertices in a separate run. For feasible cases in the automated suite, we checked that all vertices appear once, classes are nonempty and proper, and the reported sizes and imbalance match the returned groups.

| Input file or case | Expected | Observed | Status |
|---|---|---|---|
| `example_k3.txt` | `(2,2,2)` and the handout’s exact groups | Exact match | Pass |
| `example_k2.txt` | `no such a sequence exists.` | Exact match | Pass |
| `path8_k3.txt`, `star_k2.txt` | `(3,3,2)`, `(5,1)` | Exact matches | Pass |
| `cycle5_k3.txt`, `triangle_k3.txt` | `(2,2,1)`, `(1,1,1)` | Exact matches | Pass |
| `complete4_k4.txt`, `single_vertex_k1.txt` | `(1,1,1,1)`, `(1)` | Exact matches | Pass |
| Eight-vertex handout tree | `(5,3)` with two colors and `(3,3,2)` with three | Exact matches | Pass |
| Twenty-vertex handout diagram as transcribed | `(5,5,5,5)` with four colors | Balanced with four colors and infeasible with three | Pass |
| Even six-vertex cycle | Optimal with two and three colors | Matched brute force in both cases | Pass |
| Greedy coloring regression | Exact three-color solution despite the reference greedy method using four | Imbalance 1 | Pass |
| Larger graphs, malformed inputs, and HTTP cases | Correct solutions, errors, and status codes | Assertions passed | Pass |

We kept the capacity bound after comparing it with a trial that used only the remaining count-based bounds. On our 23-vertex star with three colors, the final search returned `(11,11,1)` in about 0.30 ms, while the trial took about 2.98 s for the same result. These are local measurements.

Our six-vertex result lists Blue as vertices 2 and 6, Red as 3 and 4, and Yellow as 1 and 5. For equal class sizes, we order groups by descending total vertex degree and then by vertex IDs. The complete test log is in `TEST_RESULTS.txt`.

```bash
python3 main.py sample_inputs/example_k3.txt
python3 main.py sample_inputs/example_k2.txt
python3 -B -m unittest discover -s tests -v
```

## 9. Optional interactive visual demonstration

We developed a local browser editor to add, move, and delete vertices and to add or remove edges. We included sample loading and reset, a live adjacency matrix, and text import and export in the assignment’s format. The editor stores positions in a JavaScript array and undirected edge identifiers in a set.

With **Find optimal coloring**, we send the current matrix and `k` to a local HTTP endpoint. The endpoint calls the same solver as our file-based CLI. The editor displays the sequence and groups, colors the vertices, and reports when no solution exists. Playback reveals the final coloring in vertex order. Our HTTP tests cover the server and solver adapter.

We launch the editor with `python3 visualizer.py` and open the printed loopback URL. The editor accepts up to 80 vertices. We use the CLI to run the required file-input workflow.

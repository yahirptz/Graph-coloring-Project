# CS 421 — Project 2: Almost Equal Graph Coloring

**Assignment:** Project 2 (150 points), due November 22, 2026  
**Implementation:** Python 3.10+ and the standard library

## 1. Problem statement and objective

We read the number of colors `k`, the number of vertices `n`, and an `n × n` binary adjacency matrix from a text file. Our input represents a simple, connected, undirected graph. We look for a proper coloring using exactly `k` nonempty classes, so the endpoints of every edge must have different colors.

We sort the class sizes so that `n_1 ≥ n_2 ≥ … ≥ n_k > 0`. The handout defines imbalance as the sum of absolute differences between consecutive sizes. Since each difference is nonnegative, the sum telescopes to the expression below.

`F = |n_1 − n_2| + … + |n_(k−1) − n_k| = n_1 − n_k`.

We minimize that difference and print the sorted sizes and one-based vertex IDs for each group. If no proper coloring uses exactly `k` colors, we print `no such a sequence exists.`

## 2. Problem-solving techniques (10 points)

For the general case, we use exact backtracking and select vertices with DSATUR. We choose the uncolored vertex with the most distinct colors among its colored neighbors. We break ties by higher graph degree, then lower vertex ID. Each uncolored vertex has an integer mask of forbidden colors, so we can find its saturation by counting the set bits.

We try the next unused color first, followed by legal existing colors in ascending order of class size and color index. Introducing unused colors in index order avoids equivalent label permutations. We also use branch-and-bound to skip partial assignments that cannot improve our best complete coloring.

We handle several cases directly. When `k > n`, there are too few vertices. When `k = n`, singleton classes give imbalance zero. A connected graph with more than one vertex cannot use one color. For two colors, we traverse the graph with breadth-first search (BFS). A conflict rules out a bipartition. Because the graph is connected, a successful bipartition is unique up to swapping its colors and therefore fixes the class sizes.

## 3. Data structures (10 points)

| Data structure | Role |
|---|---|
| Adjacency matrix and lists | We read the required matrix and build lists for efficient neighbor traversal. |
| `assigned` and `degree` | We store each vertex’s color, or −1 if uncolored, and its degree for tie-breaking. |
| `forbidden` | We store one bit per forbidden color in each uncolored vertex’s mask. |
| `counts` and `capacities` | We track current sizes and upper bounds on final class sizes. |
| Explicit stack of iterators | We suspend each branch while exploring its child and undo its changes when it resumes. |
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
| `search_coloring(adjacency, degree, k)` | Runs the exact search using an explicit stack of branch iterators. |
| `branches(colored, used)` | Nested in `search_coloring`. Applies bounds, selects the vertex, and yields child states while managing assignment and undo. |
| `format_result(result)` | Returns the formatted sequence and vertex lists or the required impossibility message. |
| `solve_payload(payload)` in `visualizer.py` | Validates the request and packages the shared solver’s result for the browser. |

## 5. Algorithm (pseudocode)

```text
READ and validate k, n, and the adjacency matrix
HANDLE k > n, k = n, k = 1, and k = 2 directly
OTHERWISE push the initial branch iterator onto a stack
WHILE the stack is nonempty and the theoretical minimum has not been reached:
    Advance the top iterator
    Pop it if exhausted, or push the child iterator it yields
RETURN the best complete assignment found, if any

BRANCH ITERATOR:
    Reject states with too few vertices left to open every missing class
    If complete, save the assignment if it improves the best imbalance
    Reject states whose class-size bounds rule out an improvement
    Select the next vertex by saturation, degree, then vertex ID
    Try the next unused color, then legal existing colors by class size
        Apply the color and record newly set bits and the old capacity
        Yield the child state
        On resumption, undo the assignment, count, bits, and capacity

SORT returned groups by descending size and format the output
```

## 6. Correctness argument

**Properness and class count.** We reject a color if a previously colored neighbor has that color. When we color the second endpoint of an edge, the first endpoint’s color is already in its forbidden mask. Each branch checks that the remaining vertices can fill the missing classes, so a completed assignment uses exactly `k` colors. On undo, we clear only bits that the current assignment introduced, preserving restrictions from earlier assignments.

**Completeness.** We can relabel any proper partition in the order its classes first appear along the search. DSATUR depends on the number of distinct neighbor colors, which stays the same under relabeling. Trying the next unused index and every legal existing class therefore covers each partition up to color labels. If every remaining vertex must open a class, we can skip existing classes.

**Safe pruning.** Let `B` be the best complete imbalance and `r` the number of remaining vertices. After assigning a vertex of degree `d` to a class, we cap that class at `n − d`, since none of its neighbors can join it. Let `U` be the minimum of the smallest capacity, the smallest current count plus `r`, and `floor(n/k)`. Each term bounds the final smallest class from above. Improving `B` requires every final class to fit under `U + B − 1`. We prune if an existing class already exceeds that limit or if the sum of the class capacities clipped to that limit is less than `n`.

We also use `L = max(largest current count, ceil(n/k))` as a lower bound on the final largest class. To improve `B`, every class must reach at least `max(1, L − B + 1)`. We prune if the sum of the remaining deficits exceeds `r`.

**Optimality.** We stop if the best imbalance reaches zero when `k` divides `n`, or one otherwise. No smaller value is possible. If we exhaust the search first, all other proper partitions were checked or could not beat our best result. If we saved no assignment, no proper coloring with exactly `k` classes exists.

## 7. Complexity analysis (30 points)

Let `n` be the vertex count, `m` the edge count, and `k` the color count. We use an adjacency matrix as required, so parsing a well-formed matrix, validation, and building adjacency lists take `O(n²)` time. The two-color traversal takes `O(n + m)` after the lists are built.

For the general case, we visit at most `O(k^n)` search states. Assuming unit-cost mask operations, DSATUR scans up to `n` vertices, the bounds scan `k` counts and capacities, and sorting choices costs up to `O(k log k)` per state. Updating or undoing a branch scans at most one vertex’s neighbors or recorded changes. A conservative total is `O(n² + (n + k log k) · k^n)` time. Python integers can span multiple machine words, so mask operations can cost more for large `k`. The exact search remains exponential in the worst case.

The matrix takes `O(n²)` space and the adjacency lists take `O(n + m)`. The stack has at most `n + 1` iterators, with up to `k` choices per level. The active undo lists together contain at most `O(m)` entries because each edge can contribute only when its first endpoint is assigned. The forbidden masks use up to `O(nk)` bits. Including the input matrix, the total is `O(n²)` space because the search runs only when `k ≤ n`.

## 8. Testing and results (100 points)

We ran 28 automated tests, including 19 solver and CLI tests and nine visualizer adapter and HTTP tests. We compared the solver against a separate brute-force enumerator on 252 seeded random graph and color-count combinations. For feasible cases, we checked that all vertices appear once, classes are nonempty and proper, and the reported sizes and imbalance match the returned groups.

| Input file or case | Expected | Observed | Status |
|---|---|---|---|
| `example_k3.txt` | `(2,2,2)` and the handout’s exact groups | Exact match | Pass |
| `example_k2.txt` | `no such a sequence exists.` | Exact match | Pass |
| `path8_k3.txt`, `star_k2.txt` | `(3,3,2)`, `(5,1)` | Exact matches | Pass |
| `cycle5_k3.txt`, `triangle_k3.txt` | `(2,2,1)`, `(1,1,1)` | Exact matches | Pass |
| `complete4_k4.txt`, `single_vertex_k1.txt` | `(1,1,1,1)`, `(1)` | Exact matches | Pass |
| Eight-vertex handout tree | `(5,3)` with two colors and `(3,3,2)` with three | Exact matches | Pass |
| Twenty-vertex handout diagram as transcribed | `(5,5,5,5)` with four colors | Balanced with four colors and infeasible with three | Pass |
| Greedy DSATUR regression | Exact three-color solution despite greedy using four | Imbalance 1 | Pass |
| Larger graphs, malformed inputs, and HTTP cases | Correct solutions, errors, and status codes | Assertions passed | Pass |

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

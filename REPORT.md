# CS 421 — Project 2: Almost Equal Graph Coloring

**Assignment:** Project 2 (150 points), due November 22, 2026  
**Implementation language:** Python 3 (standard library only)

## 1. Problem statement and objective

The input is a positive integer `k` followed by the size `n` and an `n × n` zero-one adjacency matrix of a simple, undirected, connected graph. The program must find a proper vertex coloring that uses **exactly `k` nonempty color classes**, or print `no such a sequence exists.` if that is impossible. A coloring is proper when the endpoints of every edge have different colors.

If the sizes of its color classes, sorted in descending order, are `n_1 >= n_2 >= ... >= n_k > 0`, the project defines the imbalance as

`F = |n_1 - n_2| + |n_2 - n_3| + ... + |n_(k-1) - n_k|`.

Because the sequence is nonincreasing, all differences are nonnegative and this sum telescopes:

`F = (n_1 - n_2) + ... + (n_(k-1) - n_k) = n_1 - n_k`.

Therefore the implementation **minimizes the difference between the largest and smallest color classes** among all proper colorings using exactly `k` colors. It does not assume equal group sizes are always possible: for example, a six-vertex star can only have color-class sizes `(5,1)` when `k = 2`.

For a successful coloring, the program prints the sorted sequence and the one-based vertex IDs for each color class.

## 2. Problem-solving techniques (10 points)

The program uses **exact backtracking** with two optimizations:

1. **DSATUR-style vertex selection:** choose an uncolored vertex with the largest number of distinct colors already present among its neighbors (its saturation). Break ties by larger graph degree, then smaller vertex number. Choosing the most constrained vertex early typically finds contradictions sooner.
2. **Branch-and-bound:** after each assignment, compute a lower bound on the best possible final imbalance. If it cannot improve the best complete solution found so far, stop exploring that branch. Also stop if there are too few uncolored vertices to use all `k` colors.

**Symmetry breaking:** names of colors do not affect graph-coloring validity or imbalance. The next new color is always introduced using its lowest unused internal index, instead of trying all indistinguishable unused colors. This avoids redundant copies of equivalent colorings while preserving every distinct partition into color classes.

**Search order:** try legal existing colors with smaller current classes first, then one new color if available. This tends to find low-imbalance solutions sooner. The result is still exact because the search considers all legal alternatives, unless a mathematically safe pruning rule applies.

The search also stops if it reaches the universal theoretical minimum: `0` when `n` is divisible by `k`, otherwise `1`. Such a coloring is necessarily optimal. This is a stopping condition, not an assumption that every graph admits such a coloring.

## 3. Data structures (10 points)

| Data structure | Role |
|---|---|
| `list[list[int]]` adjacency matrix | Stores the `n × n` matrix required by the assignment; `matrix[i][j]` is 1 exactly when vertices `i` and `j` are adjacent. |
| `list[list[int]]` adjacency list | Derived from the matrix to efficiently iterate over a vertex's neighbors during the search. |
| `list[int]` `assigned` | Current color number for each vertex; `-1` means uncolored. |
| `list[int]` `counts` | Number of vertices currently assigned to each color. |
| `list[int]` `degree` | Number of neighbors of each vertex, for tie-breaking. |
| `set[int]` | Tracks neighbor colors and checks graph connectivity during BFS. |
| `ColoringResult` dataclass | Stores the final size sequence, grouped one-based vertex IDs, and optimal imbalance. |

Internally, vertices are numbered `0` to `n-1`; the display converts them to the required `1` to `n`.

## 4. Major functions (10 points)

| Function | Purpose |
|---|---|
| `read_graph(path)` | Reads the required file format, checks its dimensions, and returns `(k, adjacency_matrix)`. |
| `validate_graph(matrix)` | Rejects nonsquare, nonbinary, asymmetric, disconnected, or self-loop-containing matrices. |
| `find_almost_equal_coloring(matrix, k)` | Exact DSATUR-ordered backtracking solver minimizing color-class imbalance. Returns a result or `None`. |
| `select_vertex()` (nested) | Picks the next uncolored vertex by saturation, degree, and vertex number. |
| `search(colored, used)` (nested) | Tries legal color choices recursively, applies pruning, and records the best solution. |
| `format_result(result)` | Prints the color sequence plus color-to-vertices lists, or the required no-solution message. |
| `main()` | Processes the input-file command-line argument, runs the solver, and prints output. |

## 5. Algorithm (pseudocode)

```text
READ k, n, and the n-by-n adjacency matrix from a file
VALIDATE that the matrix is a simple connected undirected graph
IF k > n: PRINT "no such a sequence exists."
ELSE:
    Initialize assigned[v] = uncolored for every vertex v
    Initialize counts[color] = 0 for every color
    best_solution = none
    best_imbalance = n + 1

    SEARCH(number_colored, number_of_colors_used):
        IF best possible theoretical imbalance is already achieved: RETURN
        IF there are not enough uncolored vertices to use all k colors: RETURN
        IF all vertices are colored:
            IF exactly k colors were used:
                imbalance = largest class size - smallest class size
                IF imbalance is better than best_imbalance:
                    SAVE the assignment and imbalance
            RETURN
        IF lower bound of final imbalance >= best_imbalance: RETURN

        v = uncolored vertex with highest saturation (DSATUR)
        FOR each legally usable existing color, smallest class first:
            COLOR v with it; SEARCH recursively; UNCOLOR v
        IF fewer than k colors have been used:
            COLOR v with the next unused color; SEARCH recursively; UNCOLOR v

    SEARCH(0, 0)
    IF no solution found: PRINT "no such a sequence exists."
    ELSE: SORT nonempty color groups by descending size and PRINT them
```

## 6. Correctness argument

**Properness:** A color is never assigned to a vertex if an already colored neighbor has that color. Each edge is checked when its second endpoint is colored, so every completed assignment is a proper coloring.

**Exactly `k` colors:** An assignment is accepted only when the search has colored every vertex and introduced exactly `k` nonempty classes. If `k > n` or insufficient vertices remain to introduce missing classes, it correctly rejects that branch.

**Completeness:** Any proper coloring can be relabeled in the order its color classes are first encountered by the search. Consequently, introducing only the next unused color loses no distinct proper partition. At each recursive step, every permissible existing color and the single canonical new color is examined. Thus, without pruning, the search covers every proper coloring into exactly `k` nonempty classes, up to renaming colors.

**Safe pruning:** If the current largest count is `M`, the smallest count (including still-unused colors) is `m`, and `r` vertices remain uncolored, then the final largest class is at least `M`, and the final smallest class can be no larger than `m+r`. Hence every completion has imbalance at least `max(0, M - m - r)`. Discarding a branch when this lower bound is at least the best completed score cannot discard a strictly better solution. Also, any solution has imbalance at least `n % k != 0` (that is, 0 if divisible, or 1 otherwise), so stopping at that lower bound is safe.

**Optimality:** Because all proper colorings (modulo irrelevant color labels) are explored or safely pruned, the best saved coloring minimizes `n_1 - n_k`, which equals the sum in the assignment definition. If no assignment is found, a proper coloring using exactly `k` colors does not exist.

## 7. Complexity analysis (30 points)

Let `n` be the number of vertices, `m` the edges, and `k` the required number of colors.

- **Reading and checking the input:** `O(n²)` time for the matrix, symmetry and value checks, adjacency-list construction, and connectivity BFS on the adjacency matrix.
- **Search:** in the worst case each vertex has at most `k` possible colors, yielding at most `O(k^n)` recursive states. Selecting the next DSATUR vertex may examine all uncolored vertices and their neighbors: `O(n + m)` per state, at most `O(n²)`. Pruning and ordering choices fit within this bound when `k <= n`.
- **Worst-case total time:** `O(n² · k^n)` for `k <= n`; exponential time is expected because general graph-coloring feasibility is computationally hard. The DSATUR selection and pruning typically save work, but cannot eliminate the exponential worst case.
- **Space:** `O(n²)` for the required adjacency matrix, plus `O(n + m)` for the adjacency list, `O(n + k)` for assignment/count arrays, and an `O(n)` recursion stack. Since `m <= n(n-1)/2`, **overall space is `O(n² + k)`**, or simply `O(n²)` when `k <= n`.

## 8. Testing and results (100 points)

The included automated test suite contains **12 test methods**. Along with individual examples and error handling, it checks **252 combinations of small, randomly generated connected graphs and color counts** against a separate brute-force reference implementation. For all feasible cases the tests independently confirm that every vertex appears exactly once, neighboring vertices receive different colors, all `k` classes are nonempty, the sequence is sorted, and the optimal imbalance matches exhaustive enumeration.

| Input file / case | Expected | Actual result | Status |
|---|---|---|---|
| `example_k3.txt` (six-vertex handout example) | `(2,2,2)` | `(2,2,2)` | Pass |
| `example_k2.txt` (same graph) | No valid two-coloring | `no such a sequence exists.` | Pass |
| `path8_k3.txt` | `(3,3,2)` | `(3,3,2)` | Pass |
| `star_k2.txt` | `(5,1)` | `(5,1)` | Pass |
| `cycle5_k3.txt` | `(2,2,1)` | `(2,2,1)` | Pass |
| `complete4_k4.txt` | `(1,1,1,1)` | `(1,1,1,1)` | Pass |
| `single_vertex_k1.txt` | `(1)` | `(1)` | Pass |
| Invalid matrices and file formats | Descriptive input error | Correctly rejected | Pass |
| 252 random small graph/color instances | Independent brute-force optimum | Exact match in all cases | Pass |

Color names are interchangeable: for the handout example, this solution prints the same `(2,2,2)` and the same three independent vertex groups as the sample, but may assign **Blue**, **Red**, and **Yellow** to those groups in a different order. That is an equivalent proper coloring.

### Commands to reproduce

From the project folder:

```bash
python3 main.py sample_inputs/example_k3.txt
python3 main.py sample_inputs/example_k2.txt
python3 -m unittest discover -s tests -v
```

No external Python libraries or network access are needed.


## 9. Optional interactive visual demonstration

An additional local browser interface (`visualizer.py` and the `visualizer/` directory) makes the core solution easier to demonstrate. The user can add and move numbered vertices, add/remove undirected edges, delete vertices, switch the number of colors, select sample graphs, and view the adjacency matrix automatically derived from the drawing. The **Find optimal coloring** button sends the selected integer `k` and the current 0/1 matrix to a local Python HTTP endpoint, which calls the **same** `find_almost_equal_coloring(matrix, k)` function as the required command-line program. It displays the class-size sequence, color-group vertex lists, and a colored graph. The animation is a step-by-step **reveal of the final optimal coloring**, not a depiction of each recursive backtracking branch.

The browser also imports and exports `.txt` files containing `k`, `n`, and `n` space-separated adjacency-matrix rows. Thus the visual editor is **optional** and does not replace the assignment's required file input. The extra data structures are JavaScript arrays for vertex positions, a Set for undirected edge identifiers, and the adjacency matrix built from those edges. Browser rendering takes `O(n² + m)` due to the visible matrix; the exact solver's worst-case complexity remains `O(n² k^n)`.

**Running:** `python3 visualizer.py`, then use the local URL printed in the terminal. The server binds only to `127.0.0.1`, has no external dependencies, and serves the HTML/CSS/JavaScript plus a small JSON API.

**Additional verification:** The visualizer server and adapter are covered by seven further automated tests for the handout's successful and impossible cases, invalid graphs, static asset delivery, sample loading, JSON solving, and bad requests. The full automated suite now has **19 passing tests**. Browser UI controls were additionally smoke-tested in a headless browser using a mocked local request layer due to the restricted test environment; API correctness was separately verified by real local HTTP requests.

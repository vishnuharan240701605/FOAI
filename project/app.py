"""
===============================================================================
MAZE AI Web Application - Enhanced Flask Server
===============================================================================
Provides REST API endpoints with strict wall collision checking, path validation,
and debug logging for:
  - Random Solvable Maze Generation (70% path / 30% wall)
  - Algorithm Pathfinding (BFS, DFS, A*)
  - Real-time Dynamic Obstacle Replanning (A*)
===============================================================================
"""

import time
import heapq
import random
from collections import deque
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# =============================================================================
# DATA STRUCTURES & STRICT PATHFINDING
# =============================================================================

class Node:
    def __init__(self, position, parent=None, g=0, h=0):
        self.position = position  # (row, col)
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        if self.f == other.f:
            return self.h < other.h
        return self.f < other.f

    def __eq__(self, other):
        return isinstance(other, Node) and self.position == other.position

    def __hash__(self):
        return hash(self.position)


def heuristic(p1, p2):
    """Manhattan distance heuristic: |r1 - r2| + |c1 - c2|"""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def normalize_grid(raw_grid):
    """
    Normalizes grid to integers:
    0 = Free Path
    1 = Wall
    """
    normalized = []
    for r in range(len(raw_grid)):
        row = []
        for c in range(len(raw_grid[r])):
            val = raw_grid[r][c]
            if val == 1 or val == '1':
                row.append(1)
            else:
                row.append(0)
        normalized.append(row)
    return normalized


def get_neighbors(pos, grid, rows, cols):
    """
    Returns adjacent 4-directional move positions (Up, Down, Left, Right).
    STRICT CHECK: Must be within bounds AND cell must be 0 (Free path).
    """
    r, c = pos
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    neighbors = []
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            # STRICT WALL CHECK: Must NOT be 1 (wall)
            if grid[nr][nc] == 0:
                neighbors.append((nr, nc))
    return neighbors


def reconstruct_path(node):
    path = []
    curr = node
    while curr:
        path.append(list(curr.position))
        curr = curr.parent
    return path[::-1]


def validate_and_log_path(path, grid, algo_name):
    """
    DEBUG FEATURE: Logs path coordinates, wall locations, and verifies that
    NO coordinate in the path is a wall cell.
    """
    walls = set()
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                walls.add((r, c))

    print(f"\n=================== DEBUG LOG: {algo_name.upper()} ===================")
    print(f"Grid Dimensions: {rows}x{cols}")
    print(f"Total Walls Count: {len(walls)}")
    print(f"Wall Coordinates: {sorted(list(walls))}")
    print(f"Computed Path Length: {len(path)} steps")
    print(f"Path Coordinates: {path}")

    # Verify no coordinate in path is a wall
    for coord in path:
        r, c = coord[0], coord[1]
        if (r, c) in walls:
            print(f"[X] CRITICAL ERROR: Path coordinate ({r}, {c}) is a WALL!")
            print("=================================================================\n")
            return False

    print("[OK] VALIDATION PASSED: Path is 100% valid and contains NO walls!")
    print("=================================================================\n")
    return True


# =============================================================================
# ALGORITHMS (BFS, DFS, A*)
# =============================================================================

def run_bfs(grid, start, goal, rows, cols):
    start_time = time.perf_counter()
    start_pos = tuple(start)
    goal_pos = tuple(goal)

    queue = deque([Node(start_pos)])
    visited_set = {start_pos}
    visited_order = [list(start_pos)]
    nodes_explored = 0
    final_node = None

    while queue:
        curr = queue.popleft()
        nodes_explored += 1

        if curr.position == goal_pos:
            final_node = curr
            break

        for n_pos in get_neighbors(curr.position, grid, rows, cols):
            if n_pos not in visited_set:
                visited_set.add(n_pos)
                visited_order.append(list(n_pos))
                queue.append(Node(n_pos, parent=curr))

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(final_node) if final_node else []
    return path, visited_order, nodes_explored, elapsed_ms


def run_dfs(grid, start, goal, rows, cols):
    start_time = time.perf_counter()
    start_pos = tuple(start)
    goal_pos = tuple(goal)

    stack = [Node(start_pos)]
    visited_set = set()
    visited_order = []
    nodes_explored = 0
    final_node = None

    while stack:
        curr = stack.pop()
        pos = curr.position

        if pos in visited_set:
            continue

        visited_set.add(pos)
        visited_order.append(list(pos))
        nodes_explored += 1

        if pos == goal_pos:
            final_node = curr
            break

        for n_pos in reversed(get_neighbors(pos, grid, rows, cols)):
            if n_pos not in visited_set:
                stack.append(Node(n_pos, parent=curr))

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(final_node) if final_node else []
    return path, visited_order, nodes_explored, elapsed_ms


def run_astar(grid, start, goal, rows, cols):
    start_time = time.perf_counter()
    start_pos = tuple(start)
    goal_pos = tuple(goal)

    start_node = Node(start_pos, g=0, h=heuristic(start_pos, goal_pos))
    counter = 0
    open_set = []
    heapq.heappush(open_set, (start_node.f, counter, start_node))

    g_score = {start_pos: 0}
    visited_set = set()
    visited_order = []
    nodes_explored = 0
    final_node = None

    while open_set:
        _, _, curr = heapq.heappop(open_set)
        pos = curr.position

        if pos in visited_set:
            continue

        visited_set.add(pos)
        visited_order.append(list(pos))
        nodes_explored += 1

        if pos == goal_pos:
            final_node = curr
            break

        for n_pos in get_neighbors(pos, grid, rows, cols):
            tentative_g = curr.g + 1

            if n_pos not in g_score or tentative_g < g_score[n_pos]:
                g_score[n_pos] = tentative_g
                h_val = heuristic(n_pos, goal_pos)
                neighbor_node = Node(n_pos, parent=curr, g=tentative_g, h=h_val)
                counter += 1
                heapq.heappush(open_set, (neighbor_node.f, counter, neighbor_node))

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    path = reconstruct_path(final_node) if final_node else []
    return path, visited_order, nodes_explored, elapsed_ms


# =============================================================================
# FLASK ROUTES & API ENDPOINTS
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate-maze', methods=['POST'])
def generate_maze():
    """
    Generates a random maze:
    - 70% chance -> path (0)
    - 30% chance -> wall (1)
    - Start (0,0) and Goal (rows-1, cols-1) are ALWAYS path (0).
    Guarantees a solvable path exists.
    """
    data = request.get_json() or {}
    rows = int(data.get('rows', 10))
    cols = int(data.get('cols', 10))
    wall_prob = float(data.get('wall_prob', 0.30))  # 30% wall probability

    start = [0, 0]
    goal = [rows - 1, cols - 1]

    for attempt in range(100):
        grid = []
        for r in range(rows):
            row = []
            for c in range(cols):
                if (r == 0 and c == 0) or (r == rows - 1 and c == cols - 1):
                    row.append(0)  # Always free path at Start & Goal
                else:
                    row.append(1 if random.random() < wall_prob else 0)
            grid.append(row)

        path, _, _, _ = run_bfs(grid, start, goal, rows, cols)
        if path:
            return jsonify({
                'grid': grid,
                'rows': rows,
                'cols': cols,
                'start': start,
                'goal': goal
            })

    # Clear grid fallback if random generation was blocked
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    return jsonify({
        'grid': grid,
        'rows': rows,
        'cols': cols,
        'start': start,
        'goal': goal
    })


@app.route('/api/solve', methods=['POST'])
def solve():
    """
    Solves the maze received from frontend UI using selected algorithm.
    Validates that NO cell in returned path passes through a wall.
    """
    data = request.get_json() or {}
    raw_grid = data.get('grid', [])
    start = data.get('start', [0, 0])
    goal = data.get('goal', [0, 0])
    algo = data.get('algorithm', 'astar').lower()

    grid = normalize_grid(raw_grid)
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Ensure Start and Goal are 0 (free path)
    grid[start[0]][start[1]] = 0
    grid[goal[0]][goal[1]] = 0

    if algo == 'bfs':
        path, visited_order, nodes_explored, elapsed_ms = run_bfs(grid, start, goal, rows, cols)
    elif algo == 'dfs':
        path, visited_order, nodes_explored, elapsed_ms = run_dfs(grid, start, goal, rows, cols)
    else:  # astar
        path, visited_order, nodes_explored, elapsed_ms = run_astar(grid, start, goal, rows, cols)

    # Validate path strictly
    is_valid = validate_and_log_path(path, grid, algo)
    if not is_valid:
        path = []

    path_len = len(path) - 1 if len(path) > 0 else 0

    return jsonify({
        'algorithm': algo,
        'path': path,
        'visited_order': visited_order,
        'nodes_explored': nodes_explored,
        'path_length': path_len,
        'execution_time_ms': round(elapsed_ms, 4)
    })


@app.route('/api/replan', methods=['POST'])
def replan():
    """
    Re-calculates A* path from current position when dynamic obstacle is added.
    """
    data = request.get_json() or {}
    raw_grid = data.get('grid', [])
    current_pos = data.get('current_pos', [0, 0])
    goal = data.get('goal', [0, 0])

    grid = normalize_grid(raw_grid)
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    grid[current_pos[0]][current_pos[1]] = 0
    grid[goal[0]][goal[1]] = 0

    path, visited_order, nodes_explored, elapsed_ms = run_astar(grid, current_pos, goal, rows, cols)
    validate_and_log_path(path, grid, 'astar-replan')

    path_len = len(path) - 1 if len(path) > 0 else 0

    return jsonify({
        'path': path,
        'visited_order': visited_order,
        'nodes_explored': nodes_explored,
        'path_length': path_len,
        'execution_time_ms': round(elapsed_ms, 4)
    })


if __name__ == '__main__':
    print("Starting MAZE AI Web Server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)

"""
===============================================================================
MAZE AI – Intelligent Pathfinding Agent
===============================================================================
Concepts   : Artificial Intelligence (Search Algorithms)
Algorithms : Breadth-First Search (BFS), Depth-First Search (DFS), A* (A-Star)
Features    : 2D Grid Maze, Random Maze Generation, Manhattan Heuristic,
              Dynamic Replanning, Performance Metrics, and Step-by-Step
              Console Animation.
===============================================================================
"""

import time
import os
import sys
import heapq
import random
from collections import deque

# Reconfigure stdout/stderr encoding to UTF-8 if running on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ANSI Color Codes for Terminal Output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GRAY = "\033[90m"


class Node:
    """Represents a single cell/state in the maze grid during pathfinding."""
    def __init__(self, position, parent=None, g=0, h=0):
        self.position = position  # Tuple (row, col)
        self.parent = parent      # Reference to parent Node
        self.g = g                # Cost from start to current node
        self.h = h                # Estimated heuristic cost to goal
        self.f = g + h            # Total cost (f = g + h)

    def __lt__(self, other):
        if self.f == other.f:
            return self.h < other.h
        return self.f < other.f

    def __eq__(self, other):
        return isinstance(other, Node) and self.position == other.position

    def __hash__(self):
        return hash(self.position)

    def __repr__(self):
        return f"Node({self.position}, g={self.g}, h={self.h}, f={self.f})"


class Maze:
    """Represents the 2D grid maze structure and visualization helpers."""
    def __init__(self, grid):
        self.grid = [list(row) for row in grid]
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0
        self.start_pos = self._find_symbol('S') or (0, 0)
        self.goal_pos = self._find_symbol('G') or (self.rows - 1, self.cols - 1)

    def _find_symbol(self, symbol):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == symbol:
                    return (r, c)
        return None

    def is_valid_move(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col] != 1
        return False

    def get_neighbors(self, pos):
        row, col = pos
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        neighbors = []
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self.is_valid_move(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def set_obstacle(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row][col] = 1

    def display(self, path=None, visited=None, agent_pos=None, title=None):
        path_set = set(path) if path else set()
        visited_set = set(visited) if visited else set()

        if title:
            print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")

        for r in range(self.rows):
            line = []
            for c in range(self.cols):
                pos = (r, c)
                cell = self.grid[r][c]

                if agent_pos and pos == agent_pos:
                    line.append(f"{BOLD}{MAGENTA}🤖{RESET} ")
                elif pos == self.start_pos or cell == 'S':
                    line.append(f"{BOLD}{GREEN}S {RESET}")
                elif pos == self.goal_pos or cell == 'G':
                    line.append(f"{BOLD}{RED}G {RESET}")
                elif pos in path_set:
                    line.append(f"{BOLD}{YELLOW}* {RESET}")
                elif pos in visited_set:
                    line.append(f"{GRAY}· {RESET}")
                elif cell == 1:
                    line.append(f"{BOLD}█ {RESET}")
                else:
                    line.append("  ")
            print("".join(line))
        print()


def heuristic(p1, p2):
    """Calculates Manhattan Distance heuristic: |x1 - x2| + |y1 - y2|"""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def reconstruct_path(node):
    path = []
    current = node
    while current:
        path.append(current.position)
        current = current.parent
    return path[::-1]


def generate_random_maze(rows=6, cols=6, wall_probability=0.25):
    """Generates a random solvable maze grid of size (rows x cols)."""
    print(f"\n{BOLD}{CYAN}Generating a solvable random maze ({rows}x{cols})...{RESET}")
    for attempt in range(100):
        grid = []
        for r in range(rows):
            row = []
            for c in range(cols):
                if (r == 0 and c == 0) or (r == rows - 1 and c == cols - 1):
                    row.append(0)
                else:
                    row.append(1 if random.random() < wall_probability else 0)
            grid.append(row)

        grid[0][0] = 'S'
        grid[rows - 1][cols - 1] = 'G'

        # Test path existence using BFS
        temp_maze = Maze(grid)
        path, _, _, _ = bfs(temp_maze)
        if path:
            return grid

    # Fallback clear grid if random generation is blocked
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    grid[0][0] = 'S'
    grid[rows - 1][cols - 1] = 'G'
    return grid


# =============================================================================
# ALGORITHM IMPLEMENTATIONS
# =============================================================================

def bfs(maze, start=None, goal=None):
    start_pos = start if start else maze.start_pos
    goal_pos = goal if goal else maze.goal_pos
    start_time = time.perf_counter()

    queue = deque([Node(start_pos)])
    visited = {start_pos}
    nodes_explored = 0
    final_node = None

    while queue:
        current_node = queue.popleft()
        nodes_explored += 1

        if current_node.position == goal_pos:
            final_node = current_node
            break

        for neighbor_pos in maze.get_neighbors(current_node.position):
            if neighbor_pos not in visited:
                visited.add(neighbor_pos)
                queue.append(Node(neighbor_pos, parent=current_node))

    end_time = time.perf_counter()
    return reconstruct_path(final_node) if final_node else [], nodes_explored, (end_time - start_time) * 1000, visited


def dfs(maze, start=None, goal=None):
    start_pos = start if start else maze.start_pos
    goal_pos = goal if goal else maze.goal_pos
    start_time = time.perf_counter()

    stack = [Node(start_pos)]
    visited = set()
    nodes_explored = 0
    final_node = None

    while stack:
        current_node = stack.pop()
        if current_node.position in visited:
            continue
            
        visited.add(current_node.position)
        nodes_explored += 1

        if current_node.position == goal_pos:
            final_node = current_node
            break

        for neighbor_pos in reversed(maze.get_neighbors(current_node.position)):
            if neighbor_pos not in visited:
                stack.append(Node(neighbor_pos, parent=current_node))

    end_time = time.perf_counter()
    return reconstruct_path(final_node) if final_node else [], nodes_explored, (end_time - start_time) * 1000, visited


def astar(maze, start=None, goal=None):
    start_pos = start if start else maze.start_pos
    goal_pos = goal if goal else maze.goal_pos
    start_time = time.perf_counter()

    start_node = Node(start_pos, g=0, h=heuristic(start_pos, goal_pos))
    counter = 0
    open_set = []
    heapq.heappush(open_set, (start_node.f, counter, start_node))
    
    g_score = {start_pos: 0}
    visited = set()
    nodes_explored = 0
    final_node = None

    while open_set:
        _, _, current_node = heapq.heappop(open_set)
        if current_node.position in visited:
            continue

        visited.add(current_node.position)
        nodes_explored += 1

        if current_node.position == goal_pos:
            final_node = current_node
            break

        for neighbor_pos in maze.get_neighbors(current_node.position):
            tentative_g = current_node.g + 1
            if neighbor_pos not in g_score or tentative_g < g_score[neighbor_pos]:
                g_score[neighbor_pos] = tentative_g
                h_val = heuristic(neighbor_pos, goal_pos)
                neighbor_node = Node(neighbor_pos, parent=current_node, g=tentative_g, h=h_val)
                counter += 1
                heapq.heappush(open_set, (neighbor_node.f, counter, neighbor_node))

    end_time = time.perf_counter()
    return reconstruct_path(final_node) if final_node else [], nodes_explored, (end_time - start_time) * 1000, visited


def run_dynamic_agent(maze, dynamic_obstacle_pos, trigger_step=2):
    print(f"\n{BOLD}{MAGENTA}===================================================={RESET}")
    print(f"{BOLD}{MAGENTA}      DYNAMIC MAZE REPLANNING SIMULATION           {RESET}")
    print(f"{BOLD}{MAGENTA}===================================================={RESET}")
    
    start_pos, goal_pos = maze.start_pos, maze.goal_pos
    print(f"\n{CYAN}Step 1: Calculating Initial A* Path from Start {start_pos} to Goal {goal_pos}...{RESET}")
    current_path, _, _, _ = astar(maze, start_pos, goal_pos)

    if not current_path:
        print(f"{RED}No path available to solve this maze.{RESET}")
        return

    maze.display(path=current_path, title="Initial Computed Route")

    current_pos, path_index = start_pos, 0
    full_executed_path = [current_pos]
    obstacle_introduced = False

    while current_pos != goal_pos:
        path_index += 1
        if path_index >= len(current_path):
            break

        next_pos = current_path[path_index]

        # Dynamic obstacle insertion at trigger_step
        if path_index == trigger_step and not obstacle_introduced:
            obs_r, obs_c = dynamic_obstacle_pos
            print(f"\n{BOLD}{RED}Dynamic obstacle introduced at ({obs_r}, {obs_c}){RESET}")
            maze.set_obstacle(obs_r, obs_c)
            obstacle_introduced = True

        # Check if remaining path or next step is blocked
        if maze.grid[next_pos[0]][next_pos[1]] == 1 or any(maze.grid[r][c] == 1 for r, c in current_path[path_index:]):
            print(f"\n{BOLD}{RED}Path blocked – recalculating using A*{RESET}")
            maze.display(path=current_path, agent_pos=current_pos, title="Obstacle Encountered!")

            print(f"{BOLD}{CYAN}🔄 Re-running A* algorithm from current agent position {current_pos}...{RESET}")
            new_path, _, replan_time, _ = astar(maze, current_pos, goal_pos)

            if not new_path:
                print(f"{BOLD}{RED}❌ No alternative path to goal could be found! Agent stuck.{RESET}")
                return

            print(f"{BOLD}{GREEN}✨ New Path Found! (Length: {len(new_path) - 1}, Re-calculated in {replan_time:.3f} ms){RESET}")
            current_path = new_path
            path_index = 1
            next_pos = current_path[1]
            maze.display(path=current_path, agent_pos=current_pos, title="Updated Route after Replanning")

        current_pos = next_pos
        full_executed_path.append(current_pos)
        print(f"Agent moved to -> {BOLD}{MAGENTA}{current_pos}{RESET}")

    print(f"\n{BOLD}{GREEN}🎉 GOAL REACHED SUCCESSFULLY! Total steps taken: {len(full_executed_path) - 1}{RESET}")
    maze.display(path=full_executed_path, agent_pos=goal_pos, title="Final Agent Trajectory")


def print_performance_metrics(maze):
    results = []

    path_bfs, nodes_bfs, time_bfs, visited_bfs = bfs(maze)
    results.append({"algo": "Breadth First Search (BFS)", "path_len": len(path_bfs) - 1 if path_bfs else 0, "nodes": nodes_bfs, "time": time_bfs, "path": path_bfs, "visited": visited_bfs})

    path_dfs, nodes_dfs, time_dfs, visited_dfs = dfs(maze)
    results.append({"algo": "Depth First Search (DFS)", "path_len": len(path_dfs) - 1 if path_dfs else 0, "nodes": nodes_dfs, "time": time_dfs, "path": path_dfs, "visited": visited_dfs})

    path_ast, nodes_ast, time_ast, visited_ast = astar(maze)
    results.append({"algo": "A* Search (Manhattan)", "path_len": len(path_ast) - 1 if path_ast else 0, "nodes": nodes_ast, "time": time_ast, "path": path_ast, "visited": visited_ast})

    print(f"\n{BOLD}{CYAN}======================================================================={RESET}")
    print(f"{BOLD}{CYAN}                    ALGORITHM PERFORMANCE COMPARISON                  {RESET}")
    print(f"{BOLD}{CYAN}======================================================================={RESET}")
    header = f"{'Algorithm':<28} | {'Path Length':<12} | {'Nodes Explored':<14} | {'Time (ms)':<10}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * len(header))

    for res in results:
        print(f"{res['algo']:<28} | {res['path_len']:<12} | {res['nodes']:<14} | {res['time']:<10.4f}")
    print("-" * len(header))

    for res in results:
        maze.display(path=res['path'], visited=res['visited'], title=f"Path Visualized: {res['algo']}")

    return results


def main():
    os.system("")  # Enable ANSI colors on Windows Command Prompt

    print(f"{BOLD}{GREEN}")
    print("      ==============================================")
    print("            MAZE AI - INTELLIGENT PATHFINDING       ")
    print("      ==============================================")
    print(f"           College AI Search Algorithms Project{RESET}\n")

    grid = generate_random_maze(rows=6, cols=6, wall_probability=0.25)
    maze = Maze(grid)
    maze.display(title="GENERATED RANDOM MAZE GRID")

    print_performance_metrics(maze)

    path_init, _, _, _ = astar(maze)
    if len(path_init) > 3:
        dyn_pos = path_init[len(path_init) // 2]
        run_dynamic_agent(maze, dynamic_obstacle_pos=dyn_pos, trigger_step=2)
    else:
        print(f"\n{YELLOW}Note: Path length is too short for dynamic obstacle insertion.{RESET}")

if __name__ == "__main__":
    main()

# MAZE AI – Intelligent Pathfinding Web Application

> **Artificial Intelligence & Search Algorithms Web Application**
> Built with Python (Flask), Tailwind CSS, and Vanilla JavaScript. Features random solvable maze generation, graph search algorithms (BFS, DFS, A* with Manhattan heuristic), strict wall collision protection, step-by-step path animation, performance benchmarking, and real-time dynamic obstacle replanning.

---

## 📌 Features

1. **🎲 Random Solvable Maze Generation**:
   - Configurable grid dimensions ($N \times M$).
   - Generates 70% path / 30% wall distribution (`0` = path, `1` = wall).
   - Start `(0,0)` and Goal `(N-1, M-1)` are guaranteed free paths.
   - Retries up to 100 times to guarantee a solvable path exists.

2. **Core Algorithms Implemented**:
   - **Breadth-First Search (BFS)**: Uses a Queue (FIFO via `collections.deque`) to guarantee the shortest unweighted path.
   - **Depth-First Search (DFS)**: Uses a Stack (LIFO) to explore deep branches, returning a valid (though non-optimal) path.
   - **A\* Search (A-Star)**: Uses a Priority Queue (`heapq`) paired with the **Manhattan Distance Heuristic** ($h(n) = |x_1 - x_2| + |y_1 - y_2|$) for optimal, informed path finding.

3. **❗ Strict Wall Collision Protection**:
   - Algorithms strictly check bounds and verify `grid[row][col] != 1`.
   - Backend debug logs print grid matrix, wall coordinates, path coordinates, and run automated assertion checks to ensure **0 wall overlaps**.
   - Frontend visualization strictly protects wall cells (`.cell-wall`).

4. **🎮 Real-Time Dynamic Replanning**:
   - Inject dynamic obstacle mid-route.
   - Triggers alert banner: `"Path Blocked – Recalculating using A*..."`.
   - Re-runs A* dynamically from current agent position to Goal.

5. **Performance Metrics**:
   - Path Length (step count)
   - Nodes Explored (search space complexity)
   - Execution Time in milliseconds ($ms$)

---

## 📁 Repository Structure

```
FOAI/
├── project/
│   ├── app.py                  # Flask Backend Server with API endpoints
│   ├── maze_ai.py              # Self-contained CLI Python project file
│   ├── templates/
│   │   └── index.html          # Modern Glassmorphism Visual Interface
│   └── static/
│       ├── css/
│       │   └── styles.css      # Custom cell state styles, glow effects, animations
│       └── js/
│           └── script.js       # Asynchronous visualizer engine & interactive grid
├── project reports/
│   ├── MAZE_AI_IEEE_Paper.pdf          # Research paper on the Maze AI system
│   ├── MAZE_AI_Project_Report-2.pdf    # Comprehensive project report
│   └── Project_Presentation_MAZE_AI_.pptx # Presentation slide deck
├── README.md
└── .gitignore
```

---

## 🚀 How to Launch Locally

```bash
# Navigate into the project folder
cd project

# Install Flask (if not already installed)
pip install flask

# Launch Web Server
python app.py
```
Open browser at: **`http://127.0.0.1:5000`**

/**
 * MAZE AI – Interactive Pathfinding Engine & Visualizer
 * Random Maze & Dynamic Replanning System
 */

// Application State
let rows = 10;
let cols = 10;
let grid = [];
let startPos = [0, 0];
let goalPos = [rows - 1, cols - 1];

let isSolving = false;
let isMouseDown = false;
let animationSpeed = 30; // ms per step

let currentPath = [];
let currentVisited = [];

// DOM Elements
const mazeGridEl = document.getElementById('maze-grid');
const algoSelect = document.getElementById('algo-select');
const rowsInput = document.getElementById('grid-rows');
const colsInput = document.getElementById('grid-cols');
const speedSlider = document.getElementById('speed-slider');
const speedValEl = document.getElementById('speed-val');

const btnGenerate = document.getElementById('btn-generate');
const btnSolve = document.getElementById('btn-solve');
const btnDynamic = document.getElementById('btn-dynamic');
const btnClear = document.getElementById('btn-clear');

const metricPathLen = document.getElementById('metric-path-len');
const metricNodes = document.getElementById('metric-nodes');
const metricTime = document.getElementById('metric-time');

const statusToast = document.getElementById('status-toast');
const statusIcon = document.getElementById('status-icon');
const statusText = document.getElementById('status-text');
const statusBadge = document.getElementById('status-badge');
const solverStateEl = document.getElementById('solver-state');

// Helper: Sleep delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// =============================================================================
// GRID INITIALIZATION & RENDERING
// =============================================================================

function renderGrid() {
    mazeGridEl.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
    mazeGridEl.innerHTML = '';

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const cell = document.createElement('div');
            cell.dataset.row = r;
            cell.dataset.col = c;
            cell.id = `cell-${r}-${c}`;
            cell.className = 'cell';

            if (r === startPos[0] && c === startPos[1]) {
                cell.classList.add('start');
                cell.innerText = 'S';
            } else if (r === goalPos[0] && c === goalPos[1]) {
                cell.classList.add('goal');
                cell.innerText = 'G';
            } else if (grid[r][c] === 1) {
                cell.classList.add('wall');
            }

            // Click event to toggle walls
            cell.addEventListener('click', (e) => {
                e.preventDefault();
                toggleWallCell(r, c);
            });

            // Drag event for smooth wall drawing
            cell.addEventListener('mousedown', (e) => {
                e.preventDefault();
                isMouseDown = true;
                toggleWallCell(r, c);
            });

            cell.addEventListener('mouseenter', () => {
                if (isMouseDown) {
                    toggleWallCell(r, c);
                }
            });

            mazeGridEl.appendChild(cell);
        }
    }
}

document.addEventListener('mouseup', () => {
    isMouseDown = false;
});

function toggleWallCell(r, c) {
    if (isSolving) return;

    // Protect Start and Goal cells
    if ((r === startPos[0] && c === startPos[1]) || (r === goalPos[0] && c === goalPos[1])) {
        return;
    }

    const cellEl = document.getElementById(`cell-${r}-${c}`);
    if (!cellEl) return;

    // Toggle 2D array data and UI class
    if (grid[r][c] === 0) {
        grid[r][c] = 1;
        cellEl.classList.add('wall');
        cellEl.classList.remove('visited', 'path');
    } else {
        grid[r][c] = 0;
        cellEl.classList.remove('wall', 'visited', 'path');
    }

    console.log(`[TOGGLE WALL] Cell (${r}, ${c}) -> grid[${r}][${c}] = ${grid[r][c]}`);
}

// =============================================================================
// API CALLS (RANDOM MAZE, SOLVE, REPLAN)
// =============================================================================

async function fetchRandomMaze() {
    if (isSolving) return;
    updateToast('Generating 70% path / 30% wall solvable maze...', 'info', 'Generating');

    try {
        const response = await fetch('/api/generate-maze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rows: parseInt(rowsInput.value) || 10,
                cols: parseInt(colsInput.value) || 10,
                wall_prob: 0.30
            })
        });

        const data = await response.json();
        grid = data.grid;
        rows = data.rows;
        cols = data.cols;
        startPos = data.start;
        goalPos = data.goal;

        resetMetrics();
        renderGrid();
        updateToast('Random maze generated (Solvable)!', 'success', 'Ready');
    } catch (err) {
        console.error('Error generating maze:', err);
        updateToast('Failed to generate maze.', 'error', 'Error');
    }
}

async function solveMaze() {
    if (isSolving) return;
    isSolving = true;
    solverStateEl.innerText = 'Solving...';
    btnSolve.disabled = true;

    clearPathVisualization();
    const selectedAlgo = algoSelect.value;
    const algoName = algoSelect.options[algoSelect.selectedIndex].text;

    updateToast(`Running ${algoName}...`, 'info', 'Solving');

    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grid: grid,
                start: startPos,
                goal: goalPos,
                algorithm: selectedAlgo
            })
        });

        const data = await response.json();
        currentPath = data.path;
        currentVisited = data.visited_order;

        console.log(`[SOLVE DEBUG] Algorithm: ${algoName}`);
        console.log(`[SOLVE DEBUG] Visited Count: ${currentVisited.length}`);
        console.log(`[SOLVE DEBUG] Path Coordinates:`, currentPath);

        if (!currentPath || currentPath.length === 0) {
            updateToast('❌ No valid path found! Path is blocked by walls.', 'error', 'Unsolvable');
            metricPathLen.innerText = '0 steps';
            metricNodes.innerText = data.nodes_explored;
            metricTime.innerText = `${data.execution_time_ms} ms`;
            isSolving = false;
            btnSolve.disabled = false;
            solverStateEl.innerText = 'Idle';
            return;
        }

        // 1. ANIMATE VISITED NODES FIRST
        for (let i = 0; i < currentVisited.length; i++) {
            const [vr, vc] = currentVisited[i];
            if ((vr !== startPos[0] || vc !== startPos[1]) && (vr !== goalPos[0] || vc !== goalPos[1])) {
                const cellEl = document.getElementById(`cell-${vr}-${vc}`);
                if (cellEl && grid[vr][vc] === 0) {
                    cellEl.classList.add('visited');
                }
            }
            if (animationSpeed > 0) {
                await delay(animationSpeed);
            }
        }

        // 2. ANIMATE FINAL PATH
        for (let i = 0; i < currentPath.length; i++) {
            const [pr, pc] = currentPath[i];

            if ((pr !== startPos[0] || pc !== startPos[1]) && (pr !== goalPos[0] || pc !== goalPos[1])) {
                const cellEl = document.getElementById(`cell-${pr}-${pc}`);
                if (cellEl && grid[pr][pc] === 0) {
                    cellEl.classList.remove('visited');
                    cellEl.classList.add('path');
                }
            }
            if (animationSpeed > 0) {
                await delay(animationSpeed + 15);
            }
        }

        // Update Metrics
        metricPathLen.innerText = `${data.path_length} steps`;
        metricNodes.innerText = data.nodes_explored;
        metricTime.innerText = `${data.execution_time_ms} ms`;

        updateToast(`🎉 Goal Reached! (${data.path_length} steps, ${data.execution_time_ms} ms)`, 'success', 'Complete');
    } catch (err) {
        console.error('Error solving maze:', err);
        updateToast('An error occurred during pathfinding.', 'error', 'Error');
    }

    isSolving = false;
    btnSolve.disabled = false;
    solverStateEl.innerText = 'Idle';
}

async function triggerDynamicObstacle() {
    if (!currentPath || currentPath.length <= 2) {
        updateToast('Solve the maze first to trigger dynamic obstacles!', 'warning', 'Action Needed');
        return;
    }

    // Pick a step along current path to block
    const targetIdx = Math.floor(currentPath.length / 2);
    const [obsR, obsC] = currentPath[targetIdx];

    // Place dynamic obstacle
    grid[obsR][obsC] = 1;
    const obsCellEl = document.getElementById(`cell-${obsR}-${obsC}`);
    if (obsCellEl) {
        obsCellEl.classList.remove('path', 'visited');
        obsCellEl.classList.add('wall');
    }

    // Agent current position is coordinate right before the obstacle
    const agentPos = currentPath[Math.max(0, targetIdx - 1)];

    // Show Path Blocked Alert
    updateToast(`Path Blocked – Recalculating using A*...`, 'danger', 'Path Blocked');
    await delay(600);

    try {
        const response = await fetch('/api/replan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                grid: grid,
                current_pos: agentPos,
                goal: goalPos
            })
        });

        const data = await response.json();
        const newPath = data.path;

        if (!newPath || newPath.length === 0) {
            updateToast('❌ No alternative path found! Agent is stuck.', 'error', 'Blocked');
            return;
        }

        // Clear previous path visualization
        clearPathVisualization();

        // Animate new path from agentPos to Goal
        for (let i = 0; i < newPath.length; i++) {
            const [pr, pc] = newPath[i];
            if ((pr !== startPos[0] || pc !== startPos[1]) && (pr !== goalPos[0] || pc !== goalPos[1])) {
                const cellEl = document.getElementById(`cell-${pr}-${pc}`);
                if (cellEl && grid[pr][pc] === 0) {
                    cellEl.classList.add('path');
                }
            }
            await delay(25);
        }

        currentPath = newPath;
        metricPathLen.innerText = `${data.path_length} steps`;
        metricNodes.innerText = data.nodes_explored;
        metricTime.innerText = `${data.execution_time_ms} ms`;

        updateToast(`✨ New Path Found! Re-routed in ${data.execution_time_ms} ms`, 'success', 'Re-routed');
    } catch (err) {
        console.error('Error replanning path:', err);
    }
}

function clearPathVisualization() {
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if ((r === startPos[0] && c === startPos[1]) || (r === goalPos[0] && c === goalPos[1])) {
                continue;
            }
            const cellEl = document.getElementById(`cell-${r}-${c}`);
            if (cellEl && grid[r][c] === 0) {
                cellEl.classList.remove('visited', 'path');
            }
        }
    }
}

function resetCanvas() {
    if (isSolving) return;
    clearPathVisualization();
    resetMetrics();
    updateToast('Visualization reset.', 'info', 'Reset');
}

function resetMetrics() {
    metricPathLen.innerText = '0 steps';
    metricNodes.innerText = '0';
    metricTime.innerText = '0.00 ms';
    currentPath = [];
    currentVisited = [];
}

function updateToast(msg, type = 'info', badgeText = 'Status') {
    statusText.innerText = msg;
    statusBadge.innerText = badgeText;

    if (type === 'danger' || type === 'error') {
        statusIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation text-rose-400"></i>';
        statusToast.className = 'w-full mb-4 bg-rose-950/80 border border-rose-800 px-4 py-3 rounded-xl flex items-center justify-between shadow-lg text-rose-200';
    } else if (type === 'success') {
        statusIcon.innerHTML = '<i class="fa-solid fa-circle-check text-emerald-400"></i>';
        statusToast.className = 'w-full mb-4 bg-emerald-950/80 border border-emerald-800 px-4 py-3 rounded-xl flex items-center justify-between shadow-lg text-emerald-200';
    } else if (type === 'warning') {
        statusIcon.innerHTML = '<i class="fa-solid fa-circle-exclamation text-amber-400"></i>';
        statusToast.className = 'w-full mb-4 bg-amber-950/80 border border-amber-800 px-4 py-3 rounded-xl flex items-center justify-between shadow-lg text-amber-200';
    } else {
        statusIcon.innerHTML = '<i class="fa-solid fa-circle-info text-purple-400"></i>';
        statusToast.className = 'w-full mb-4 bg-slate-800/90 border border-slate-700 px-4 py-3 rounded-xl flex items-center justify-between shadow-lg text-slate-200';
    }
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================

btnGenerate.addEventListener('click', fetchRandomMaze);
btnSolve.addEventListener('click', solveMaze);
btnDynamic.addEventListener('click', triggerDynamicObstacle);
btnClear.addEventListener('click', resetCanvas);

speedSlider.addEventListener('input', (e) => {
    animationSpeed = parseInt(e.target.value);
    speedValEl.innerText = `${animationSpeed} ms`;
});

rowsInput.addEventListener('change', fetchRandomMaze);
colsInput.addEventListener('change', fetchRandomMaze);

// Init default on load
window.addEventListener('DOMContentLoaded', () => {
    fetchRandomMaze();
});

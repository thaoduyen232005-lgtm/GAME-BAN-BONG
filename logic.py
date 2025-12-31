import math, random
from collections import deque
from settings import BALL_RADIUS, X_MARGIN, PLAY_WIDTH, ROWS, COLS, row_h

def get_pos(r, c, grid_offset_state):
    off = BALL_RADIUS if (r + grid_offset_state) % 2 == 1 else 0
    return X_MARGIN + c * BALL_RADIUS * 2 + BALL_RADIUS + off, r * row_h + BALL_RADIUS

def get_neighbors(r, c, grid_offset_state):
    if (r + grid_offset_state) % 2 == 0:
        return [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    return [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]

def snap_to_grid(x, y, grid_offset_state, grid):
    r = max(0, min(ROWS - 1, int(round((y - BALL_RADIUS) / row_h))))
    off = BALL_RADIUS if (r + grid_offset_state) % 2 == 1 else 0
    c = max(0, min(COLS - 1, int(round((x - X_MARGIN - BALL_RADIUS - off) / (BALL_RADIUS * 2)))))
    if grid[r][c]:
        best_dist, best_pos = float('inf'), (r, c)
        for dr, dc in get_neighbors(r, c, grid_offset_state):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and not grid[nr][nc]:
                nx, ny = get_pos(nr, nc, grid_offset_state)
                dist = math.hypot(x - nx, y - ny)
                if dist < best_dist: best_dist, best_pos = dist, (nr, nc)
        r, c = best_pos
    fx, fy = get_pos(r, c, grid_offset_state)
    return r, c, fx, fy

def get_same_color_group(row, col, grid, grid_offset_state):
    color_id = grid[row][col].color_id
    queue = deque([(row, col)])
    visited = {(row, col)}
    while queue:
        r, c = queue.popleft()
        for dr, dc in get_neighbors(c, r, grid_offset_state):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc]:
                if grid[nr][nc].color_id == color_id and (nr, nc) not in visited:
                    visited.add((nr, nc)); queue.append((nr, nc))
    return visited

def handle_floating(grid, falling_bubbles, FallingEgg, grid_offset_state):
    connected = set()
    queue = deque([(0, c) for c in range(COLS) if grid[0][c]])
    for item in queue: connected.add(item)
    while queue:
        r, c = queue.popleft()
        for dr, dc in get_neighbors(r, c, grid_offset_state):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] and (nr, nc) not in connected:
                connected.add((nr, nc)); queue.append((nr, nc))
    gain = 0
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] and (r, c) not in connected:
                falling_bubbles.append(FallingEgg(grid[r][c]))
                grid[r][c] = None; gain += 20
    return gain

def shift_grid_down(grid, grid_offset_state, Egg, bubble_imgs, FallingEgg, falling_bubbles):
    new_offset = 1 - grid_offset_state
    for r in range(ROWS - 1, 0, -1):
        for c in range(COLS):
            grid[r][c] = grid[r-1][c]
            if grid[r][c]:
                grid[r][c].x, grid[r][c].y = get_pos(r, c, new_offset)
    for c in range(COLS):
        if new_offset == 1 and c == COLS - 1: grid[0][c] = None
        else:
            gx, gy = get_pos(0, c, new_offset)
            grid[0][c] = Egg(gx, gy, random.randint(0, 5), bubble_imgs)
    handle_floating(grid, falling_bubbles, FallingEgg, new_offset)

    return new_offset

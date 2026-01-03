import pygame, math, random, os, datetime
from collections import deque

# --- KHỞI TẠO ---
pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Bubble Shooter - Underwater Edition")
clock = pygame.time.Clock()


# --- CĂN CHỈNH KHUNG CHƠI VÀ VẠCH VÀNG ---
# Dựa trên ảnh background: Vùng đại dương chiếm khoảng 40% chiều rộng ở giữa
PLAY_WIDTH = int(WIDTH * 0.41)
X_MARGIN = (WIDTH - PLAY_WIDTH) // 2
BALL_RADIUS = PLAY_WIDTH // 24  # Tự động tính bán kính bóng để vừa khít 12 cột

# Vạch vàng trong ảnh nằm ở khoảng 80% chiều cao màn hình
# Ta điều chỉnh LOSE_LINE_ROW sao cho khớp với vị trí đó
row_h = BALL_RADIUS * 1.732
LOSE_LINE_ROW = (HEIGHT * 0.79 - BALL_RADIUS) / row_h

FPS = 60
COLS = 12
ROWS = 22

# Font chữ
SCORE_FONT = pygame.font.SysFont("Arial", 36, bold=True)
HISTORY_FONT = pygame.font.SysFont("Consolas", 22)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

level_config = {
    1: {"drop_time": 20000, "show_guide": True},
    2: {"drop_time": 15000, "show_guide": True},
    3: {"drop_time": 10000, "show_guide": False}
}


current_level = 1
grid_offset_state = 0
score = 0
game_history = []


def load_img(name, scale=None, height=None):
    path = os.path.join(DATA_PATH, name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if height:
            w, h = img.get_size()
            ratio = w / h
            scale = (int(height * ratio), height)
        if scale:
            img = pygame.transform.smoothscale(img, scale)
        return img
    return None


# --- TÀI NGUYÊN ---
bg_start = load_img("batdau.png", (WIDTH, HEIGHT))
bg_select = load_img("man.png", (WIDTH, HEIGHT))
background_game = load_img("background.png", (WIDTH, HEIGHT))
bg_gameover = load_img("gameover.png", (WIDTH, HEIGHT))
bg_help = load_img("huongdan.png", (WIDTH, HEIGHT))

btn_start_img = load_img("start.png", height=80)
btn_help_img = load_img("help.png", height=70)
btn_history_img = load_img("history.png", height=70)

btn_man1_img = load_img("man1.png", height=180)
btn_man2_img = load_img("man2.png", height=180)
btn_man3_img = load_img("man3.png", height=180)

btn_home_img = load_img("home.png", height=50)
btn_replay_img = load_img("choilai.png", height=50)
btn_home_big = load_img("home.png", height=85)
btn_replay_big = load_img("choilai.png", height=85)

bubble_images = []
for i in range(6):
    img = load_img(f"bubble_{i + 1}.gif", scale=(BALL_RADIUS * 2, BALL_RADIUS * 2))
    if not img:
        img = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(img, (100, 200, 255), (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
    bubble_images.append(img)
# --- ÂM THANH ---
pygame.mixer.init()

def load_sound(name):
    path = os.path.join(DATA_PATH, "sound", name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

snd_shot = load_sound("shot.mp3")
snd_pop = load_sound("pop.mp3")
snd_click = load_sound("click.mp3")
snd_lose = load_sound("lose.mp3")

bgm_path = os.path.join(DATA_PATH, "sound", "bgm.mp3")
if os.path.exists(bgm_path):
    pygame.mixer.music.load(bgm_path)
    pygame.mixer.music.set_volume(0.5) # Độ lớn 50%
    pygame.mixer.music.play(-1)        # Phát lặp vô tận
# --- UI SETUP ---
btn_start_rect = btn_start_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
btn_help_rect = btn_help_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
btn_history_rect = btn_history_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140))
btn_replay_rect = btn_replay_big.get_rect(center=(WIDTH // 2 - 130, HEIGHT // 2 + 180))
btn_home_rect = btn_home_big.get_rect(center=(WIDTH // 2 + 130, HEIGHT // 2 + 180))
btn_home_ingame_rect = btn_home_img.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
btn_replay_ingame_rect = btn_replay_img.get_rect(bottomright=(btn_home_ingame_rect.left - 20, HEIGHT - 20))
btn_home_any_rect = btn_home_img.get_rect(topright=(WIDTH - 30, 30))

spacing = 200
btn_man2_rect = btn_man2_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
btn_man1_rect = btn_man1_img.get_rect(center=(WIDTH // 2 - spacing, HEIGHT // 2))
btn_man3_rect = btn_man3_img.get_rect(center=(WIDTH // 2 + spacing, HEIGHT // 2))


def add_to_history():
    now = datetime.datetime.now().strftime("%H:%M %d/%m")
    entry = {"time": now, "score": score, "level": current_level}
    game_history.insert(0, entry)
    if len(game_history) > 12: game_history.pop()


def draw_button(surface, img, rect, mouse_pos):
    if rect.collidepoint(mouse_pos):
        w, h = img.get_size()
        zoomed = pygame.transform.smoothscale(img, (int(w * 1.1), int(h * 1.1)))
        surface.blit(zoomed, zoomed.get_rect(center=rect.center))
    else:
        surface.blit(img, rect)


def draw_score(surface):
    score_txt = SCORE_FONT.render(f"Score: {score}", True, (255, 255, 255))
    surface.blit(score_txt, (30, 30))


class Egg:
    def __init__(self, x, y, color_id):
        self.x, self.y, self.color_id = x, y, color_id
        self.image = bubble_images[color_id]

    def draw(self, surface):
        surface.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))


class FallingEgg:
    def __init__(self, egg):
        self.x, self.y, self.image = egg.x, egg.y, egg.image
        self.vel_y, self.vel_x = random.uniform(2, 6), random.uniform(-2, 2)

    def update(self):
        self.y += self.vel_y;
        self.x += self.vel_x;
        self.vel_y += 0.3

def get_random_color():
    return random.randint(0, 5)

next_egg_color = get_random_color()
current_egg = Egg(WIDTH // 2, HEIGHT - 80, get_random_color())
# --- LOGIC GAME ---
grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
falling_bubbles = []


def get_pos(r, c):
    off = BALL_RADIUS if (r + grid_offset_state) % 2 == 1 else 0
    return X_MARGIN + c * BALL_RADIUS * 2 + BALL_RADIUS + off, r * row_h + BALL_RADIUS


def get_neighbors(r, c):
    if (r + grid_offset_state) % 2 == 0:
        return [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
    return [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]


def snap_to_grid(x, y):
    r = max(0, min(ROWS - 1, int(round((y - BALL_RADIUS) / row_h))))
    off = BALL_RADIUS if (r + grid_offset_state) % 2 == 1 else 0
    c = max(0, min(COLS - 1, int(round((x - X_MARGIN - BALL_RADIUS - off) / (BALL_RADIUS * 2)))))
    if grid[r][c]:
        best_dist, best_pos = float('inf'), (r, c)
        for dr, dc in get_neighbors(r, c):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and not grid[nr][nc]:
                nx, ny = get_pos(nr, nc)
                dist = math.hypot(x - nx, y - ny)
                if dist < best_dist: best_dist, best_pos = dist, (nr, nc)
        r, c = best_pos
    fx, fy = get_pos(r, c)
    return r, c, fx, fy


def handle_floating():
    global score
    connected = set()
    queue = deque([(0, c) for c in range(COLS) if grid[0][c]])
    for item in queue: connected.add(item)
    while queue:
        r, c = queue.popleft()
        for dr, dc in get_neighbors(r, c):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] and (nr, nc) not in connected:
                connected.add((nr, nc));
                queue.append((nr, nc))
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] and (r, c) not in connected:
                falling_bubbles.append(FallingEgg(grid[r][c]))
                grid[r][c] = None
                score += 20


def explode(row, col):
    global score
    tid = grid[row][col].color_id
    q, visited = deque([(row, col)]), {(row, col)}
    while q:
        r, c = q.popleft()
        for dr, dc in get_neighbors(r, c):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and grid[nr][nc] and (nr, nc) not in visited:
                if grid[nr][nc].color_id == tid: visited.add((nr, nc)); q.append((nr, nc))
    if len(visited) >= 3:
        if snd_pop: snd_pop.play()
        for r, c in visited:
            falling_bubbles.append(FallingEgg(grid[r][c]));
            grid[r][c] = None
            score += 10
        handle_floating()


def init_grid(level):
    global last_drop_time, current_level, grid_offset_state, score
    grid_offset_state, score = 0, 0
    current_level, last_drop_time = level, pygame.time.get_ticks()
    falling_bubbles.clear()
    for r in range(ROWS):
        for c in range(COLS): grid[r][c] = None
    for row in range(5):
        for col in range(COLS):
            if (row + grid_offset_state) % 2 == 1 and col == COLS - 1: continue
            gx, gy = get_pos(row, col)
            grid[row][col] = Egg(gx, gy, random.randint(0, 5))


def shift_grid_down():
    global grid_offset_state
    grid_offset_state = 1 - grid_offset_state
    for r in range(ROWS - 1, 0, -1):
        for c in range(COLS):
            grid[r][c] = grid[r - 1][c]
            if grid[r][c]: grid[r][c].x, grid[r][c].y = get_pos(r, c)
    for c in range(COLS):
        if (grid_offset_state) % 2 == 1 and c == COLS - 1:
            grid[0][c] = None
        else:
            gx, gy = get_pos(0, c)
            grid[0][c] = Egg(gx, gy, random.randint(0, 5))
    handle_floating()


def draw_trajectory(start_x, start_y, mouse_pos):
    dx, dy = mouse_pos[0] - start_x, mouse_pos[1] - start_y
    if dy >= 0: return
    dist = math.hypot(dx, dy)
    vx, vy = (dx / dist) * 12, (dy / dist) * 12
    cx, cy = start_x, start_y
    for i in range(80):
        cx += vx;
        cy += vy
        if cx <= X_MARGIN + BALL_RADIUS or cx >= X_MARGIN + PLAY_WIDTH - BALL_RADIUS: vx *= -1
        stop = False
        if cy <= BALL_RADIUS:
            stop = True
        else:
            for r in range(min(ROWS, 18)):
                for c in range(COLS):
                    if grid[r][c] and math.hypot(cx - grid[r][c].x, cy - grid[r][c].y) < BALL_RADIUS * 1.5:
                        stop = True;
                        break
                if stop: break
        if stop: break
        if i % 2 == 0: pygame.draw.circle(screen, (255, 255, 255), (int(cx), int(cy)), 2)


# --- VÒNG LẶP ---
init_grid(1)
current_egg = Egg(WIDTH // 2, HEIGHT - 80, random.randint(0, 5))
shooting, game_state = False, 0
vel_x, vel_y = 0, 0
def swap_eggs():
    global current_egg, next_egg_color
    if not shooting:
        temp_color = current_egg.color_id
        current_egg.color_id = next_egg_color
        next_egg_color = temp_color
        current_egg.image = bubble_images[current_egg.color_id]
running = True
while running:
    clock.tick(FPS)
    current_time, mouse_pos = pygame.time.get_ticks(), pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                swap_eggs()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3: # Chuột phải (Right Click) để đổi
                swap_eggs()
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == 0:
                if btn_start_rect.collidepoint(mouse_pos):
                    game_state = 3
                elif btn_help_rect.collidepoint(mouse_pos):
                    game_state = 4
                elif btn_history_rect.collidepoint(mouse_pos):
                    game_state = 5
            elif game_state in [4, 5]:
                if btn_home_any_rect.collidepoint(mouse_pos): game_state = 0
            elif game_state == 3:
                if btn_man1_rect.collidepoint(mouse_pos):
                    init_grid(1); game_state = 1
                elif btn_man2_rect.collidepoint(mouse_pos):
                    init_grid(2); game_state = 1
                elif btn_man3_rect.collidepoint(mouse_pos):
                    init_grid(3); game_state = 1
            elif game_state == 1:
                if btn_home_ingame_rect.collidepoint(mouse_pos):
                    game_state = 0
                elif btn_replay_ingame_rect.collidepoint(mouse_pos):
                    init_grid(current_level); shooting = False
                elif not shooting:
                    dx, dy = mouse_pos[0] - current_egg.x, mouse_pos[1] - current_egg.y
                    if dy < 0:
                        dist = math.hypot(dx, dy)
                        vel_x, vel_y = (dx / dist) * 22, (dy / dist) * 22
                        shooting = True
                        if snd_shot: snd_shot.play()
            elif game_state == 2:
                if btn_replay_rect.collidepoint(mouse_pos):
                    init_grid(current_level); game_state = 1
                elif btn_home_rect.collidepoint(mouse_pos):
                    game_state = 0

    if game_state == 0:
        screen.blit(bg_start, (0, 0)) if bg_start else screen.fill((40, 40, 40))
        draw_button(screen, btn_start_img, btn_start_rect, mouse_pos)
        draw_button(screen, btn_help_img, btn_help_rect, mouse_pos)
        draw_button(screen, btn_history_img, btn_history_rect, mouse_pos)
        if snd_pop: snd_pop.play()
    elif game_state == 4:
        screen.blit(bg_help, (0, 0))
        draw_button(screen, btn_home_img, btn_home_any_rect, mouse_pos)
    elif game_state == 5:
        screen.fill((30, 30, 50))
        title = SCORE_FONT.render("HISTORY", True, (255, 255, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        for i, entry in enumerate(game_history):
            txt = f"{entry['time']} | Man {entry['level']} | Score: {entry['score']}"
            row = HISTORY_FONT.render(txt, True, (255, 255, 255))
            screen.blit(row, (WIDTH // 2 - 200, 180 + i * 35))
        draw_button(screen, btn_home_img, btn_home_any_rect, mouse_pos)
    elif game_state == 3:
        screen.blit(bg_select, (0, 0))
        draw_button(screen, btn_man1_img, btn_man1_rect, mouse_pos)
        draw_button(screen, btn_man2_img, btn_man2_rect, mouse_pos)
        draw_button(screen, btn_man3_img, btn_man3_rect, mouse_pos)
    elif game_state == 1:
        cfg = level_config[current_level]
        if current_time - last_drop_time > cfg["drop_time"]: shift_grid_down(); last_drop_time = current_time
        screen.blit(background_game, (0, 0))
        current_egg.draw(screen)
        next_egg_img = bubble_images[next_egg_color]
        next_egg_small = pygame.transform.smoothscale(next_egg_img, (BALL_RADIUS, BALL_RADIUS))
        screen.blit(next_egg_small, (WIDTH // 2 - 120, HEIGHT - 90))
        #Thêm chữ Next:
        next_txt = HISTORY_FONT.render("Next:", True, (0, 0, 0))
        screen.blit(next_txt, (WIDTH // 2 - 180, HEIGHT - 85))
        # Thêm chữ đổi:
        swap_txt = HISTORY_FONT.render("[Space] để đổi", True, (0, 0, 0))
        screen.blit(swap_txt, (WIDTH // 2 - 200, HEIGHT - 55))

        # Vẽ vạch thua (ẩn vạch đỏ của code để dùng vạch vàng của ảnh)
        # pygame.draw.line(screen, (255, 255, 0), (X_MARGIN, LOSE_LINE_ROW * row_h + BALL_RADIUS), (X_MARGIN + PLAY_WIDTH, LOSE_LINE_ROW * row_h + BALL_RADIUS), 2)

        if cfg["show_guide"] and not shooting: draw_trajectory(current_egg.x, current_egg.y, mouse_pos)
        for fb in falling_bubbles[:]:
            fb.update();
            screen.blit(fb.image, fb.image.get_rect(center=(int(fb.x), int(fb.y))))
            if fb.y > HEIGHT + 50: falling_bubbles.remove(fb)

        if shooting:
            current_egg.x += vel_x;
            current_egg.y += vel_y
            if current_egg.x <= X_MARGIN + BALL_RADIUS or current_egg.x >= X_MARGIN + PLAY_WIDTH - BALL_RADIUS: vel_x *= -1
            hit = (current_egg.y <= BALL_RADIUS)
            if not hit:
                for r in range(ROWS):
                    for c in range(COLS):
                        if grid[r][c] and math.hypot(current_egg.x - grid[r][c].x,
                                                     current_egg.y - grid[r][c].y) < BALL_RADIUS * 1.5:
                            hit = True;
                            break
                    if hit: break
            if hit:
                shooting = False
                r, c, gx, gy = snap_to_grid(current_egg.x, current_egg.y)
                grid[r][c] = Egg(gx, gy, current_egg.color_id)
                explode(r, c)
                current_egg = Egg(WIDTH // 2, HEIGHT - 80, next_egg_color)
                next_egg_color = get_random_color()

        for r in range(ROWS):
            for c in range(COLS):
                if grid[r][c]:
                    grid[r][c].draw(screen)
                    if grid[r][c].y >= (LOSE_LINE_ROW * row_h + BALL_RADIUS):
                        if snd_lose: snd_lose.play()
                        add_to_history();
                        game_state = 2

        current_egg.draw(screen)
        draw_score(screen)
        draw_button(screen, btn_replay_img, btn_replay_ingame_rect, mouse_pos)
        draw_button(screen, btn_home_img, btn_home_ingame_rect, mouse_pos)
    elif game_state == 2:
        screen.blit(bg_gameover, (0, 0))
        f_txt = SCORE_FONT.render(f"Final Score: {score}", True, (255, 255, 0))
        screen.blit(f_txt, f_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))
        draw_button(screen, btn_replay_big, btn_replay_rect, mouse_pos)
        draw_button(screen, btn_home_big, btn_home_rect, mouse_pos)

    pygame.display.flip()
pygame.quit()



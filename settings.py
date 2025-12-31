import pygame
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

PLAY_WIDTH = int(WIDTH * 0.41)
X_MARGIN = (WIDTH - PLAY_WIDTH) // 2
BALL_RADIUS = PLAY_WIDTH // 24
FPS = 60
COLS, ROWS = 12, 22
row_h = BALL_RADIUS * 1.732
LOSE_LINE_ROW = (HEIGHT * 0.79 - BALL_RADIUS) / row_h

DATA_PATH = "data"

SCORE_FONT = pygame.font.SysFont("Arial", 36, bold=True)
HISTORY_FONT = pygame.font.SysFont("Consolas", 22)

LEVEL_CONFIG = {
    1: {"drop_time": 20000, "show_guide": True},
    2: {"drop_time": 15000, "show_guide": True},
    3: {"drop_time": 10000, "show_guide": False}
}
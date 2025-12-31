import pygame, random

class Egg:
    def __init__(self, x, y, color_id, bubble_images):
        self.x, self.y, self.color_id = x, y, color_id
        self.image = bubble_images[color_id]

    def draw(self, surface):
        surface.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))

class FallingEgg:
    def __init__(self, egg):
        self.x, self.y, self.image = egg.x, egg.y, egg.image
        self.vel_y, self.vel_x = random.uniform(2, 6), random.uniform(-2, 2)

    def update(self):
        self.y += self.vel_y
        self.x += self.vel_x
        self.vel_y += 0.3
import math
import pygame
from game.settings import (
    TRACTOR_RADIUS, CROP_RADIUS,
    TRACTOR_COLOR, RIPE_COLOR, ROTTEN_COLOR,
    OBSTACLE_COLOR, BLACK
)


class Tractor:
    def __init__(self, x, y, speed=5):
        self.x = x
        self.y = y
        self.speed = speed
        self.radius = TRACTOR_RADIUS

    @property
    def pos(self):
        return (self.x, self.y)

    def move_with_keys(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_DOWN]:
            dy += self.speed

        self.x += dx
        self.y += dy

    def move_towards_mouse(self, mouse_pos):
        mx, my = mouse_pos
        dx = mx - self.x
        dy = my - self.y
        dist = math.hypot(dx, dy)

        if dist > 1:
            step = min(self.speed, dist)
            self.x += step * dx / dist
            self.y += step * dy / dist

    def draw(self, surface):
        pygame.draw.circle(surface, TRACTOR_COLOR, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)


class Crop:
    def __init__(self, x, y, crop_type="ripe"):
        self.x = x
        self.y = y
        self.radius = CROP_RADIUS
        self.crop_type = crop_type
        self.collected = False

    def collides_with_tractor(self, tractor):
        dist = math.hypot(self.x - tractor.x, self.y - tractor.y)
        return dist <= self.radius + tractor.radius

    def draw(self, surface):
        if self.collected:
            return
        color = RIPE_COLOR if self.crop_type == "ripe" else ROTTEN_COLOR
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)


class Obstacle:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        pygame.draw.rect(surface, OBSTACLE_COLOR, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
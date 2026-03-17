import pygame
import random


from game.settings import (
    WIDTH, HEIGHT, FIELD_MARGIN, ROW_WIDTH,
    BG_COLOR, FIELD_BORDER, ROW_COLOR,
    TEXT_COLOR, BLACK
)
from game.entities import Tractor, Crop, Obstacle


class World:
    def __init__(self):
        self.field_rect = pygame.Rect(
            FIELD_MARGIN,
            FIELD_MARGIN,
            WIDTH - 2 * FIELD_MARGIN,
            HEIGHT - 2 * FIELD_MARGIN
        )

        self.scroll_speed = 2
        self.row_centers = [150, 250, 350, 450, 550]
        self.tractor = Tractor(120, HEIGHT // 2)
        self.crops = self._generate_crops()
        self.obstacles = [
            Obstacle(430, 240, 50, 50),
            Obstacle(720, 430, 70, 40),
        ]

        self.score = 0
        self.penalty = 0

    def _generate_crops(self):
        crops = []
        for row_y in self.row_centers:
            for i, y in enumerate(range(150, 950, 70)):
                crop_type = "ripe" if i % 2 == 0 else "rotten"
                crops.append(Crop(row_y, y, crop_type))
        return crops

    def update(self):
        self._keep_tractor_inside_field()
        self._check_crop_interactions()
        self._check_crop_interactions()
    
    def _scroll_world(self):
        for crop in self.crops:
            crop.x -= self.scroll_speed

            if crop.x < self.field_rect.left - crop.radius:
                crop.x = self.field_rect.right + random.randint(20, 120)
                crop.collected = False
                crop.crop_type = random.choice(["ripe", "rotten"])

        for obstacle in self.obstacles:
            obstacle.rect.x -= self.scroll_speed

            if obstacle.rect.right < self.field_rect.left:
                obstacle.rect.x = self.field_rect.right + random.randint(100, 250)

    def _keep_tractor_inside_field(self):
        r = self.tractor.radius
        self.tractor.x = max(self.field_rect.left + r, min(self.field_rect.right - r, self.tractor.x))
        self.tractor.y = max(self.field_rect.top + r, min(self.field_rect.bottom - r, self.tractor.y))

    def _check_crop_interactions(self):
        for crop in self.crops:
            if crop.collected:
                continue
            if crop.collides_with_tractor(self.tractor):
                crop.collected = True
                if crop.crop_type == "ripe":
                    self.score += 1
                else:
                    self.penalty += 1

    def draw(self, surface, font):
        surface.fill(BG_COLOR)

        pygame.draw.rect(surface, FIELD_BORDER, self.field_rect, 5)

        for row_y in self.row_centers:
            row_rect = pygame.Rect(
                self.field_rect.left,
                row_y - ROW_WIDTH // 2,
                self.field_rect.width,
                ROW_WIDTH,
            )
            pygame.draw.rect(surface, ROW_COLOR, row_rect)

        for crop in self.crops:
            crop.draw(surface)

        for obstacle in self.obstacles:
            obstacle.draw(surface)

        self.tractor.draw(surface)

        score_text = font.render(f"Score: {self.score}", True, TEXT_COLOR)
        penalty_text = font.render(f"Penalty: {self.penalty}", True, TEXT_COLOR)
        info_text = font.render("Move with mouse or arrow keys", True, TEXT_COLOR)

        surface.blit(score_text, (20, 15))
        surface.blit(penalty_text, (150, 15))
        surface.blit(info_text, (320, 15))
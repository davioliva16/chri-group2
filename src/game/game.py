import pygame
import random
import math
import csv
import os
from datetime import datetime

from streamlit import image

from game.settings import DEBUG_RENDER, FENCE_FORCES, TOMATO_ATTRACTION, ROTTEN_TOMATO_REPULSION, ATTRACTION_STRENGTH
import time

class Tractor: 
    def __init__(self, x, y, image_path="assets/tractor.png"):
        # Position of the tracktor
        self.x = x
        self.y = y

        self.virtual_x = x
        self.virtual_y = y

        # Image
        self.image = pygame.image.load(image_path).convert_alpha()
        scale = 2
        original_w = self.image.get_width()
        original_h = self.image.get_height()
        new_size = (int(original_w * scale), int(original_h * scale))
        self.image = pygame.transform.smoothscale(self.image, new_size)
        
        # Rect rectangule -> for collisions
        self.rect = pygame.Rect(
            self.x - self.image.get_width() // 2,
            self.y - self.image.get_height() // 2,
            self.image.get_width(),
            self.image.get_height()
        )
        # For tomato collision, we will use a circle-based collision
        self.radius = self.image.get_width() / 2

        # Image rectangule -> for rendering
        self.virtual_rect = self.image.get_rect(center=(self.virtual_x, self.virtual_y))
    
    # Update position of the tractor given mouse or haptic pos
    def update_position(self, x, y):
        self.x = x
        self.y = y

        self.rect = pygame.Rect(
            self.x - self.image.get_width() // 2,
            self.y - self.image.get_height() // 2,
            self.image.get_width(),
            self.image.get_height()
        )

    def update_virtual_position(self, x, y):
        self.virtual_x = x
        self.virtual_y = y

        self.virtual_rect = self.image.get_rect(center=(self.virtual_x, self.virtual_y))
    
    def draw(self, screenVR):
        if DEBUG_RENDER:
            # Draw semi-transparent truck image at collision rect position
            debug_img = self.image.copy()
            debug_img.set_alpha(80)
            screenVR.blit(debug_img, self.rect)
            # Draw semi-transparent green collision rect outline
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((0, 220, 30, 60))
            screenVR.blit(overlay, self.rect.topleft)
        screenVR.blit(self.image, self.virtual_rect) # Draw the iamge in the position of the virtual rectangle


class Tomato:
    def __init__(self, x, y, tomato_type, row_id):
        self.x = x
        self.y = y

        self.hitbox_scaling = 0.5 # To make the hitbox smaller than the image

        # Two tomatoes: ripe or rotten
        self.tomato_type = tomato_type
        self.collected = False
        self.row_id = row_id

        # Tomatoes properties
        self.ripped = (220, 30, 30)
        self.rotten = (30, 180, 30)

        if self.tomato_type == "ripe":
            image_path = "assets/tomato.png"
        else:
            image_path = "assets/rotten_tomato.png"

        image = pygame.image.load(image_path).convert_alpha()
        scale = 0.1
        original_w = image.get_width()
        original_h = image.get_height()
        new_size = (int(original_w * scale), int(original_h * scale))
        self.image = pygame.transform.smoothscale(image, new_size)

        # Image rect centered at (x, y)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.radius = self.hitbox_scaling * self.image.get_width() / 2

    # Draw the tomatoes
    def draw(self, screenVR):
        if self.collected:
            return

        screenVR.blit(self.image, self.rect)

    # Check if a tomato has been taken using circle-based collision
    def check_collision_tomato_tractor(self, tractor):
        # Calculate distance between centers
        dx = self.x - tractor.x
        dy = self.y - tractor.y
        distance = math.sqrt(dx**2 + dy**2)
        # Collision if distance is less than sum of radii
        return distance < (self.radius + tractor.radius)
    
    def reload_image(self):
        if self.tomato_type == "ripe":
            image_path = "assets/tomato.png"
        else:
            image_path = "assets/rotten_tomato.png"

        image = pygame.image.load(image_path).convert_alpha()
        scale = 0.1
        original_w = image.get_width()
        original_h = image.get_height()
        new_size = (int(original_w * scale), int(original_h * scale))
        self.image = pygame.transform.smoothscale(image, new_size)


class Game:
    def __init__(self):
        self.tractor = Tractor(300, 200, "assets/tractor.png") # ScreenVR 600x400

        self.reward = 0
        self.penalty = 0

        self.max_possible_reward = 0
        self.max_possible_penalty = 0

        self.scroll_speed = 1

        # HUD flash feedback: list of {text, color, target ('score'|'time'), start_time}
        self.hud_flashes = []
        self.flash_duration = 1.0  # seconds

        # Hidden stat: upper vs lower screen time
        self.frames_upper = 0
        self.frames_lower = 0

        # Crops (x, y, width, height) - screenVR 600x400
        self.field = pygame.Rect(50, 80, 500, 250) # draw in screenVR
        self.crop1 = pygame.Rect(0, 10, 600, 180)
        self.crop2 = pygame.Rect(0, 210, 600, 180)

        # Scrolling mosaic background - farmland (brown crop rows)
        bg_tile = pygame.image.load("assets/farmland.png").convert()
        bg_scale = 2  # scale up the small tile
        self.bg_tile = pygame.transform.smoothscale(
            bg_tile,
            (int(bg_tile.get_width() * bg_scale), int(bg_tile.get_height() * bg_scale))
        )
        self.bg_tile_w = self.bg_tile.get_width()
        self.bg_tile_h = self.bg_tile.get_height()
        self.bg_scroll_offset = 0

        # HUD icons
        hud_icon_size = 28
        self.hud_fresh = pygame.transform.smoothscale(
            pygame.image.load("assets/fresh.png").convert_alpha(), (hud_icon_size, hud_icon_size))
        self.hud_ripe = pygame.transform.smoothscale(
            pygame.image.load("assets/ripe.png").convert_alpha(), (hud_icon_size, hud_icon_size))
        self.hud_rotten = pygame.transform.smoothscale(
            pygame.image.load("assets/rotten.png").convert_alpha(), (hud_icon_size, hud_icon_size))
        self.hud_clock = pygame.transform.smoothscale(
            pygame.image.load("assets/clock.png").convert_alpha(), (hud_icon_size, hud_icon_size))

        # Scrolling mosaic background - grass (green areas)
        grass_tile = pygame.image.load("assets/grass.png").convert()
        grass_scale = 2  # scale up the small tile
        self.grass_tile = pygame.transform.smoothscale(
            grass_tile,
            (int(grass_tile.get_width() * grass_scale), int(grass_tile.get_height() * grass_scale))
        )
        self.grass_tile_w = self.grass_tile.get_width()
        self.grass_tile_h = self.grass_tile.get_height()
        
        self.row1_center = self.crop1.centery
        self.row2_center = self.crop2.centery

        self.row1_phase = random.uniform(0, 2 * math.pi)
        self.row2_phase = random.uniform(0, 2 * math.pi)
                
        self.tomatoes = self.generate_tomatoes()
        self.fences = self.generate_fences()
        self.time_left = 30       # starting time in seconds
        self.total_time = 0
        self.last_time_update = pygame.time.get_ticks()
        self.fences = self.generate_fences()

        #init max possible reward/penalty
        for tomato in self.tomatoes:
            if tomato.tomato_type == "ripe":
                self.max_possible_reward += 1
            else:
                self.max_possible_penalty += 1

    # Update position of tractor given the input of the mouse or haptic device
    def update_tractor_pos_from_device(self, pos, pos_virtual=None):
        x = int(pos[0])
        y = int(pos[1])

        if pos_virtual is not None:
            x_virtual = int(pos_virtual[0])
            y_virtual = int(pos_virtual[1])
        else:
            x_virtual = x
            y_virtual = y

        self.tractor.update_position(x, y)
        self.tractor.update_virtual_position(x_virtual, y_virtual)
    
    # Generate the trayectories of the tomatoes inside of the row
    def get_row_y(self, x, row_id):
        if row_id == 1:
            base_y = self.row1_center
            phase = self.row1_phase
        else:
            base_y = self.row2_center
            phase = self.row2_phase

        y = base_y + 36 * math.sin(0.02 * x + phase) + random.randint(-4, 4)
        return int(y)


    # Generate the tomatoes inside of the field (brown part)
    def generate_tomatoes(self):
        tomatoes = []

        min_spacing = 150 # 70 and speed 2 too much

        for row_id in [1, 2]:
            last_x = 80
            for _ in range(10):
                x = last_x + random.randint(min_spacing, min_spacing + 100)
                y = self.get_row_y(x, row_id)
                tomato_type = random.choice(["ripe", "rotten"])
                tomatoes.append(Tomato(x, y, tomato_type, row_id))


                last_x = x  
                     
        return tomatoes
    
    # Check if a tomato has been taken
    def check_tomatoes_interactions(self):
        for tomato in self.tomatoes:
            if tomato.collected:
                continue
            
            # If the tomato collected is red is okay if not a penalty is introduced
            if tomato.check_collision_tomato_tractor(self.tractor):
                tomato.collected = True
                now = time.time()
                if tomato.tomato_type == "ripe":
                    self.reward += 1
                    self.time_left += 0.75
                    self.hud_flashes.append({"text": "+1", "color": (0, 255, 0), "target": "score", "start": now})
                    self.hud_flashes.append({"text": "+0.75s", "color": (0, 255, 0), "target": "time", "start": now})
                else:
                    self.penalty += 1
                    self.time_left -= 3
                    self.hud_flashes.append({"text": "-1", "color": (255, 50, 50), "target": "score", "start": now})
                    self.hud_flashes.append({"text": "-3s", "color": (255, 50, 50), "target": "time", "start": now})
    
                if self.time_left < 0:
                    self.time_left = 0

    # Scrolling of the world
    def scroll_world(self):
        for tomato in self.tomatoes:
            tomato.x -= self.scroll_speed

            if tomato.x < -tomato.radius:
                rightmost_x = max(t.x for t in self.tomatoes if t.row_id == tomato.row_id)
                tomato.x = rightmost_x + random.randint(70, 130)
                tomato.y = self.get_row_y(tomato.x, tomato.row_id)
                tomato.tomato_type = random.choice(["ripe", "rotten"])
                tomato.collected = False

                tomato.reload_image()

                #Add to the max possible reward/penalty
                if tomato.tomato_type == "ripe":
                    self.max_possible_reward += 1
                else:
                    self.max_possible_penalty += 1

            tomato.rect.center = (tomato.x, tomato.y)
    
        for fence in self.fences:
            fence.x -= self.scroll_speed
        
            if fence.right < 0:
                rightmost = max(f.right for f in self.fences)
                fence.x = rightmost + random.randint(200, 400)

        # Scroll the background mosaic
        self.bg_scroll_offset += self.scroll_speed
                
    # Draw the environment on the screenVR from graphics.py
    def draw_world(self, screenVR):
        # Field: 5 rows, 2 of them with tomatoes
        # Tile grass.png across the entire screen as the green background
        screen_w, screen_h = screenVR.get_size()
        start_x = -(self.bg_scroll_offset % self.grass_tile_w)
        for tx in range(int(start_x), screen_w, self.grass_tile_w):
            for ty in range(0, screen_h, self.grass_tile_h):
                screenVR.blit(self.grass_tile, (tx, ty))

        # Draw scrolling mosaic background for each crop row (farmland on top)
        for crop_rect in [self.crop1, self.crop2]:
            # Create a clipping region so tiles don't overflow the crop area
            screenVR.set_clip(crop_rect)
            start_x = crop_rect.x - (self.bg_scroll_offset % self.bg_tile_w)
            for tx in range(int(start_x), crop_rect.right, self.bg_tile_w):
                for ty in range(crop_rect.y, crop_rect.bottom, self.bg_tile_h):
                    screenVR.blit(self.bg_tile, (tx, ty))
            screenVR.set_clip(None)  # reset clipping
        
        #Draw the fences
        for fence in self.fences:
            screenVR.blit(self.fence_image, fence)
        
        #Draw the fences
        for fence in self.fences:
            if DEBUG_RENDER:
                overlay = pygame.Surface((fence.width, fence.height), pygame.SRCALPHA)
                overlay.fill((220, 30, 30, 60))
                screenVR.blit(overlay, fence.topleft)

            screenVR.blit(self.fence_image, fence)

        # Draw the tractor
        self.tractor.draw(screenVR)

        # Draw the tomatoes
        for tomato in self.tomatoes:
            tomato.draw(screenVR)
        
        # Draw HUD
        font = pygame.font.Font(None, 30)
        score = self.reward - self.penalty
        hud_y = 8
        icon_size = self.hud_fresh.get_height()

        # Left side: score icon + score number
        if score > 10:
            score_icon = self.hud_fresh
        elif score >= 0:
            score_icon = self.hud_ripe
        else:
            score_icon = self.hud_rotten

        screenVR.blit(score_icon, (10, hud_y))
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screenVR.blit(score_text, (10 + icon_size + 6, hud_y + (icon_size - score_text.get_height()) // 2))

        # Right side: clock icon + time left
        time_text = font.render(f"Time Left: {int(self.time_left)}s", True, (255, 255, 255))
        screen_w = screenVR.get_width()
        time_x = screen_w - time_text.get_width() - 10
        clock_x = time_x - icon_size - 6
        screenVR.blit(self.hud_clock, (clock_x, hud_y))
        screenVR.blit(time_text, (time_x, hud_y + (icon_size - time_text.get_height()) // 2))

        # Draw flash feedback
        now = time.time()
        flash_font = pygame.font.Font(None, 26)
        self.hud_flashes = [f for f in self.hud_flashes if now - f["start"] < self.flash_duration]
        for flash in self.hud_flashes:
            elapsed = now - flash["start"]
            alpha = max(0, int(255 * (1.0 - elapsed / self.flash_duration)))
            flash_surf = flash_font.render(flash["text"], True, flash["color"])
            flash_surf.set_alpha(alpha)
            # Float upward over time
            float_y = hud_y + icon_size + 2 - int(elapsed * 15)
            if flash["target"] == "score":
                flash_x = 10 + icon_size + 6 + score_text.get_width() + 6
            else:
                flash_x = clock_x - flash_surf.get_width() - 4
            screenVR.blit(flash_surf, (flash_x, float_y))

    
        
    
    # Update scrolling and tomatoes
    def update(self):
        self.scroll_world()
        self.check_tomatoes_interactions()
        self.update_timer()

        # Track upper vs lower screen position
        screen_mid_y = 200  # screenVR is 600x400
        if self.tractor.y < screen_mid_y:
            self.frames_upper += 1
        else:
            self.frames_lower += 1


    # Draw fences
    def generate_fences(self):
        fences = []
    
        # Load fence image
        fence_img = pygame.image.load("assets/fence.png").convert_alpha()
    
        # Optional scaling
        scale = 0.25
        fw = int(fence_img.get_width() * scale)
        fh = int(fence_img.get_height() * scale)
        fence_img = pygame.transform.smoothscale(fence_img, (fw, fh))
    
        # Store for drawing
        self.fence_image = fence_img
        self.fence_w = fw
        self.fence_h = fh
    
        # Fence vertical position (between crop1 and crop2)
        fence_y = (self.crop1.bottom + self.crop2.top) // 2
        
        # Horizontal limits of the environment
        left_limit = self.field.left
        right_limit = self.field.right


        # Generate scrolling fence segments
        x = left_limit

        while x + fw <= right_limit:
            if random.random() < 0.9:
                fences.append(pygame.Rect(x, fence_y - fh // 2, fw, fh))
                x += fw
            else:
                x +=20

        return fences
    
    def update_timer(self):
        now = pygame.time.get_ticks()
        elapsed_ms = now - self.last_time_update
    
        if elapsed_ms >= 1000:  # 1 second passed
            self.time_left -= 1
            self.total_time += 1
            self.last_time_update = now
           
            if self.time_left < 0:
                self.time_left = 0
                
        return self.time_left

    # Draw fences
    def generate_fences(self):
        fences = []
    
        # Load fence image
        fence_img = pygame.image.load("assets/fence.png").convert_alpha()
    
        # Optional scaling
        scale = 0.25
        fw = int(fence_img.get_width() * scale)
        fh = int(fence_img.get_height() * scale)
        fence_img = pygame.transform.smoothscale(fence_img, (fw, fh))
    
        # Store for drawing
        self.fence_image = fence_img
        self.fence_w = fw
        self.fence_h = fh
    
        # Fence vertical position (between crop1 and crop2)
        fence_y = (self.crop1.bottom + self.crop2.top) // 2 - self.fence_h//2 + 10
        
        # Horizontal limits of the environment
        left_limit = self.field.left
        right_limit = self.field.right


        # Generate scrolling fence segments
        x = left_limit

        while x + fw <= right_limit:
            if random.random() < 0.9:
                fences.append(pygame.Rect(x, fence_y - fh // 2, fw, fh))
                x += fw
            else:
                x +=20

        return fences
    
    def print_stats(self):
        total_frames = self.frames_upper + self.frames_lower
        if total_frames > 0:
            upper_pct = 100.0 * self.frames_upper / total_frames
            lower_pct = 100.0 * self.frames_lower / total_frames
        else:
            upper_pct = lower_pct = 0.0

        print(f"""
        Reward: {self.reward}
        Penalty: {self.penalty} 
        Max possible reward: {self.max_possible_reward}
        Max possible penalty: {self.max_possible_penalty}
        Score: {self.reward - self.penalty} 
        Time left: {int(self.time_left)} 
        Total time: {int(self.total_time)}
        Upper screen: {upper_pct:.1f}%
        Lower screen: {lower_pct:.1f}%
        """)

        # Append stats to CSV (filename based on settings)
        fence_str = "fenceOn" if FENCE_FORCES else "fenceOff"
        if TOMATO_ATTRACTION:
            attract_str = f"attraction{ATTRACTION_STRENGTH.capitalize()}"
        else:
            attract_str = "attractionNone"
        repulsion_str = "repulsionOn" if ROTTEN_TOMATO_REPULSION else "repulsionOff"
        csv_filename = f"results_{fence_str}_{attract_str}_{repulsion_str}.csv"
        csv_path = os.path.join("results", csv_filename)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        file_exists = os.path.isfile(csv_path) and os.path.getsize(csv_path) > 0
        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "reward", "penalty", "max_possible_reward",
                                 "max_possible_penalty", "score", "total_time",
                                 "upper_screen_pct", "lower_screen_pct"])
            writer.writerow([
                datetime.now().isoformat(),
                self.reward,
                self.penalty,
                self.max_possible_reward,
                self.max_possible_penalty,
                self.reward - self.penalty,
                int(self.total_time),
                round(upper_pct, 1),
                round(lower_pct, 1)
            ])
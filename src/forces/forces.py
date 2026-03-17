import numpy as np
import math
import pygame
from Graphics import Graphics
def get_gaussian_attraction(pos, center, strength, sigma, repel=False):
    """
    Calculates an attractive force towards a center point using a Gaussian falloff.
    
    pos: tuple/array of (x, y) - current position
    center: tuple/array of (center_x, center_y)  - the point that attracts (tomato position)
    strength: float, how hard the hole pulls
    sigma: float, the radius/width of the hole's influence
    """
    pos = np.array(pos)
    center = np.array(center)
    
    # Vector pointing to the center
    direction_vec = pos - center 

    if repel:
        direction_vec = -direction_vec  # Invert the direction for repulsion
    
    # Squared distance
    distance_sq = np.sum(direction_vec ** 2)
    
    # Gaussian falloff (1.0 at center, approaches 0.0 further away)
    falloff = np.exp(-distance_sq / (2 * sigma ** 2))
    
    # Calculate final force vector
    force = strength * falloff * direction_vec
    return force

def get_all_tomato_forces(tomatoes, xh, strength, sigma):
    """Calculate the total force on the haptic device from all tomatoes."""
    total_force = np.array([0.0, 0.0])
    for tomato in tomatoes:
        if not tomato.collected:
            force = get_gaussian_attraction(xh, (tomato.x, tomato.y), strength=strength, sigma=sigma)

            total_force += force  # Attractive force

    return total_force

def get_damping_force(xh, xh_last_frame, damping_coefficient):
    """Calculate the damping force based on velocity."""
    velocity = xh - xh_last_frame
    return -damping_coefficient * velocity

class fence_forces():
    def __init__(self,graphics):
        self.g = graphics
        self.unhandledFreeSpace = False
        self.unhandledCollision = False
        self.sideCollision = False
        
    def god_object(self,xh, fences, kc):
    
        tractor_rect = self.g.haptic  # your haptic proxy rectangle
    
        # Find all fences that collide with the haptic object
        colliding_fences = [f for f in fences if tractor_rect.colliderect(f)]
    
        if not colliding_fences:
            # No collision → reset state
            if self.unhandledFreeSpace:
                
                self.unhandledFreeSpace = False
    
            self.unhandledCollision = True
            return np.array([0.0, 0.0]), False
            proxyPosition = xh
    
        # Pick the closest fence (important when two overlap visually)
        fence = min(colliding_fences, key=lambda f: abs(f.x - xh[0]))
    
        # --- COLLISION HANDLING ---
        if self.unhandledCollision:
            # Determine if collision is horizontal or vertical
            dx = abs((xh[0] + 24) - fence.left)
            dy = abs((xh[1] + 24) - fence.top)
    
            self.sideCollision = dx < dy  # True = left/right collision
            
    
            self.unhandledCollision = False
    
        # Compute proxy position
        if self.sideCollision:
            proxyPosition = np.array([fence.left - 24, xh[1]])
        else:
            proxyPosition = np.array([xh[0], fence.top - 24])
    
        # Draw proxy rectangle (visual debugging)
        proxyRectangle = pygame.Rect(
            proxyPosition[0] - 24,
            proxyPosition[1] - 24,
            48,
            48
        )
        pygame.draw.rect(self.g.screenVR, self.g.cRed, proxyRectangle)
    
        # Compute collision force
        distance_from_proxy = proxyPosition - xh
        f_collision = -kc * distance_from_proxy
    
        self.unhandledFreeSpace = True
        return f_collision, colliding_fences, proxyPosition
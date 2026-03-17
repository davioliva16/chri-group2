import numpy as np
import math
from prometheus_client import Enum
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

class CollisionLocation(Enum):
    NONE = 0
    TOP = 1
    BOTTOM = 2
    LEFT = 3
    RIGHT = 4

class CollisionStatus(Enum):
    FREE_SPACE = 0
    COLLISION = 1
    UNHANDLED_FREE_SPACE = 2
    UNHANDLED_COLLISION = 3

class fence_forces():
    def __init__(self):
        self.collisionStatus = CollisionStatus.FREE_SPACE
        self.collisionLocation = CollisionLocation.NONE
        self.proxyPosition = np.array([0.0, 0.0])
        self.lastFenceInfo = None
        
    def handle_fences(self, tractor_rect:pygame.Rect, xh, fences, kc):

        #update proxy position to current position (no forces)
        tractorPosition = np.array([tractor_rect.centerx, tractor_rect.centery])

        # Find all fences that collide with the haptic object
        colliding_fences = [f for f in fences if tractor_rect.colliderect(f)]

        if len(colliding_fences)>1:
            print("""
                Multiple collisions detected! This probably should not happen, 
                but if it does, the code will just pick the first fence for 
                collision response."""
                )
    
        if self.collisionStatus == CollisionStatus.FREE_SPACE:

            self.proxyPosition = tractorPosition

            #Check for collision and set unhandled collision state
            if colliding_fences:
                self.lastFenceInfo = colliding_fences[0]
                self.collisionStatus = CollisionStatus.UNHANDLED_COLLISION

        elif self.collisionStatus == CollisionStatus.UNHANDLED_COLLISION:

            self.proxyPosition = tractorPosition
            
            if not colliding_fences:
                self.collisionStatus = CollisionStatus.UNHANDLED_FREE_SPACE
            else:
                fence = colliding_fences[0]
                #Determine collision location
  
                dTop = (abs((tractor_rect.bottom) - fence.top))
                dBottom = (abs((tractor_rect.top) - fence.bottom))
                dLeft = (abs((tractor_rect.right) - fence.left))
                dRight = (abs((tractor_rect.left) - fence.right))

                distance = [dTop, dBottom, dLeft, dRight]

                self.lastFenceInfo = colliding_fences[0]

                self.collisionLocation = distance.index(min(distance)) + 1 #1 because enum starts at 1
                self.collisionStatus = CollisionStatus.COLLISION

        
        elif self.collisionStatus == CollisionStatus.COLLISION:
            #Check if we have exited collision and set unhandled free space state

            if not colliding_fences:
                fence = self.lastFenceInfo
            else:
                fence = colliding_fences[0]

            if self.collisionLocation == CollisionLocation.TOP:

                self.proxyPosition = np.array([tractor_rect.centerx, fence.top - tractor_rect.height/2])
                
                if tractor_rect.centerx < fence.left or tractor_rect.centerx > fence.right or tractor_rect.bottom < fence.top:
                    self.collisionStatus = CollisionStatus.UNHANDLED_FREE_SPACE

            elif self.collisionLocation == CollisionLocation.BOTTOM:

                self.proxyPosition = np.array([tractor_rect.centerx, fence.bottom + tractor_rect.height/2])

                if tractor_rect.centerx < fence.left or tractor_rect.centerx > fence.right or tractor_rect.top > fence.bottom:
                    self.collisionStatus = CollisionStatus.UNHANDLED_FREE_SPACE

            elif self.collisionLocation == CollisionLocation.LEFT:

                self.proxyPosition = np.array([fence.left - tractor_rect.width/2, tractor_rect.centery])
                
                if tractor_rect.centery < fence.top or tractor_rect.centery > fence.bottom or tractor_rect.right < fence.left:
                    self.collisionStatus = CollisionStatus.UNHANDLED_FREE_SPACE

            elif self.collisionLocation == CollisionLocation.RIGHT:

                self.proxyPosition = np.array([fence.right + tractor_rect.width/2, tractor_rect.centery])

                if tractor_rect.centery < fence.top or tractor_rect.centery > fence.bottom or tractor_rect.left > fence.right:
                    self.collisionStatus = CollisionStatus.UNHANDLED_FREE_SPACE
                    
        elif self.collisionStatus == CollisionStatus.UNHANDLED_FREE_SPACE:
            self.proxyPosition = tractorPosition
            self.collisionLocation = CollisionLocation.NONE
            self.collisionStatus = CollisionStatus.FREE_SPACE

        verticalCollision = self.collisionLocation in [CollisionLocation.TOP, CollisionLocation.BOTTOM]
        horizontalCollision = self.collisionLocation in [CollisionLocation.LEFT, CollisionLocation.RIGHT]

        # Compute collision force
        if verticalCollision or horizontalCollision:
            distance_from_proxy = (self.proxyPosition - tractorPosition)
            f_collision = -kc*distance_from_proxy
        else:
            f_collision = np.array([0.0, 0.0])
        
        return f_collision, verticalCollision, horizontalCollision, self.proxyPosition
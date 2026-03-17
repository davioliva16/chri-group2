import numpy as np
import math


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

def get_all_tomato_forces(tomatoes, xh, strength, sigma, repel_rotten=False):
    """Calculate the total force on the haptic device from all tomatoes."""
    total_force = np.array([0.0, 0.0])
    for tomato in tomatoes:
        if not tomato.collected:

            repel = (tomato.tomato_type == "rotten") and repel_rotten

            force = get_gaussian_attraction(xh, (tomato.x, tomato.y), strength=strength, sigma=sigma, repel=repel)

            total_force += force  # Attractive force

        #TODO consider adding force decay based on how long the tomato has been collected
        
    return total_force

def get_damping_force(xh, xh_last_frame, damping_coefficient):
    """Calculate the damping force based on velocity."""
    velocity = xh - xh_last_frame
    return -damping_coefficient * velocity
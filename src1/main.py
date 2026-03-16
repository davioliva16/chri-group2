import numpy as np
import pygame

from Graphics import Graphics
from Physics import Physics
from game import Game


def main():
    physics = Physics()
    graphics = Graphics(device_connected=physics.is_device_connected(), window_size=(600, 400))
    game = Game()

    f = np.array([0.0, 0.0])

    try:
        while True:
            keyups, mouse_pos = graphics.get_events()

            if physics.is_device_connected():
                # Real haptic device
                pA0, pB0, pA, pB, pE_phys = physics.get_device_pos()
                pA0_s, pB0_s, pA_s, pB_s, pE_s = graphics.convert_pos(pA0, pB0, pA, pB, pE_phys)

                # Move tractor with haptic position
                game.update_from_device(pE_s)

                # No game forces yet --> need to do it
                physics.update_force(f)

            else:
                # Use mouse if no device
                if mouse_pos[0] >= 600:
                    vr_mouse_pos = (mouse_pos[0] - 600, mouse_pos[1])
                else:
                    vr_mouse_pos = (0, mouse_pos[1])

                game.update_from_device(vr_mouse_pos)

                # Fake values so graphics.render still works
                pE_s = [mouse_pos[0], mouse_pos[1]]
                pA0_s = pB0_s = pA_s = pB_s = pE_s

            # Update tomatoes and scrolling
            game.update()
            
            # Check tomato collection
            game.check_tomatoes_interactions()

            # Clear screens
            graphics.erase_screen()

            # Draw haptics side
            graphics.render(pA0_s, pB0_s, pA_s, pB_s, pE_s, f, mouse_pos)

            # Draw game side
            game.draw_world(graphics.screenVR)

            # Present both surfaces again after game drawing
            graphics.window.blit(graphics.screenHaptics, (0, 0))
            graphics.window.blit(graphics.screenVR, (600, 0))
            pygame.display.flip()
            graphics.clock.tick(graphics.FPS)

    finally:
        physics.close()
        graphics.close()


if __name__ == "__main__":
    main()
import numpy as np
import pygame

from Graphics import Graphics
from Physics import Physics
from game.game import Game
import forces.forces as forces
import sys


class PA3():
    def __init__(self):
        self.physics = Physics(hardware_version=3) #setup physics class. Returns a boolean indicating if a device is connected
        self.device_connected = self.physics.is_device_connected() #returns True if a connected haply device was found
        self.graphics = Graphics(self.device_connected) #setup class for drawing and graphics.
        self.game = Game()
        #  - Pass along if a device is connected so that the graphics class knows if it needs to simulate the pantograph
        ##############################################
        #ADD things here that you want to run at the start of the program!
        
        self.K = 10000
        self.xh_last_frame = np.array([0.0, 0.0])

    def update_game(self):
        # Update tomatoes and scrolling
        self.game.update()
        # Check tomato collection
        self.game.check_tomatoes_interactions()

    def run(self):
        p = self.physics
        g = self.graphics
        game = self.game
        keyups,xm = g.get_events()

        if self.device_connected:
            pA0,pB0,pA,pB,pE = p.get_device_pos() #positions of the various points of the pantograph
            pA0,pB0,pA,pB,xh = g.convert_pos(pA0,pB0,pA,pB,pE) #convert the physical positions to screen coordinates
        else:
            xh = np.array(g.haptic.center)

        f = np.array([0.0, 0.0])
        g.erase_screen()
        xc,yc = g.screenVR.get_rect().center

        f_damp = forces.get_damping_force(xh, self.xh_last_frame, damping_coefficient=0.1)

        f_tomatoes = forces.get_all_tomato_forces(game.tomatoes, xh, strength=0.1, sigma=50)

        fe = f_tomatoes + f_damp

        #Update last values
        self.xh_last_frame = xh

        # Keyups
        for key in keyups:
            if key==ord("q"): #q for quit, ord() gets the unicode of the given character
                sys.exit(0) #raises a system exit exception so the "PA.close()" function will still execute
            if key == ord('m'): #Change the visibility of the mouse
                pygame.mouse.set_visible(not pygame.mouse.get_visible())
            if key == ord('r'): #Change the visibility of the linkages
                g.show_linkages = not g.show_linkages
            if key == ord('d'): #Change the visibility of the debug text
                g.show_debug = not g.show_debug

                ##############################################
        if self.device_connected: #set forces only if the device is connected
            p.update_force(fe)
        else:
            xh = g.sim_forces(xh,fe,xm,mouse_k=0.5,mouse_b=0.8) #simulate forces with mouse haptics
            pos_phys = g.inv_convert_pos(xh)
            pA0,pB0,pA,pB,pE = p.derive_device_pos(pos_phys) #derive the pantograph joint positions given some endpoint position
            pA0,pB0,pA,pB,xh = g.convert_pos(pA0,pB0,pA,pB,pE) #convert the physical positions to screen coordinates

        self.game.update_from_device(xh)

        self.update_game()

        g.render(pA0,pB0,pA,pB,xh,fe,xm)
        game.draw_world(g.screenVR)
        g.window.blit(g.screenHaptics, (0, 0))
        g.window.blit(g.screenVR, (600, 0))
        pygame.display.flip()
        g.clock.tick(g.FPS)
        
    def close(self):
        ##############################################
        #ADD things here that you want to run right before the program ends!
        
        ##############################################
        self.graphics.close()
        self.physics.close()

if __name__ == "__main__":
    pa3 = PA3()
    try:
        while True:
            pa3.run()
    finally:
        pa3.close()
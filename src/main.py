import numpy as np
import pygame

from Graphics import Graphics
from Physics import Physics
from game.game import Game
import forces.forces as forces
import sys
import game.settings as Settings
from PIL import Image



class PA3():
    def __init__(self):
        self.physics = Physics(hardware_version=2) #setup physics class. Returns a boolean indicating if a device is connected
        self.device_connected = self.physics.is_device_connected() #returns True if a connected haply device was found
        self.graphics = Graphics(self.device_connected) #setup class for drawing and graphics.
        self.game = Game()
        self.game_over = "assets/yourefired.png"
        self.fence = forces.fence_forces()
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
        ff = self.fence
        keyups,xm = g.get_events()

        if self.device_connected:
            pA0,pB0,pA,pB,pE = p.get_device_pos() #positions of the various points of the pantograph
            pA0,pB0,pA,pB,xh = g.convert_pos(pA0,pB0,pA,pB,pE) #convert the physical positions to screen coordinates
        else:
            xh = np.array(g.haptic.center)


        g.erase_screen()

        if Settings.ATTRACTION_STRENGTH == 'STRONG':
            attraction_strength = 0.125
        else:
            attraction_strength = 0.075

        f_damp = forces.get_damping_force(xh, self.xh_last_frame, damping_coefficient=0.01)

        if Settings.TOMATO_ATTRACTION:
            f_tomatoes = forces.get_all_tomato_forces(
                game.tomatoes, xh, strength=attraction_strength, 
                sigma=50, 
                repel_rotten=Settings.ROTTEN_TOMATO_REPULSION
            )
        else:
            f_tomatoes = np.array([0.0, 0.0])
        
        f_collision, verticalCollision, horizontalCollision, proxyPosition = ff.handle_fences(
            tractor_rect=game.tractor.rect,
            xh=xh,
            fences=game.fences, 
            kc=0.1
        )

        if not Settings.FENCE_FORCES:
            f_collision = np.array([0.0, 0.0])

        fe = f_damp + f_collision + f_tomatoes

        #Update last values
        self.xh_last_frame = xh
        
        if game.time_left == 0:
           
           print("\nGame Over!\n")
           game.print_stats()
           path = self.game_over

           img = Image.open(path)
           img.show()

           pygame.quit()
           sys.exit(0)

            
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


        
        if verticalCollision:
            self.game.update_tractor_pos_from_device(pos=xh, pos_virtual=np.array([xh[0], proxyPosition[1]]))
        elif horizontalCollision:
            self.game.update_tractor_pos_from_device(pos=xh, pos_virtual=np.array([proxyPosition[0], xh[1]]))
        else:
            self.game.update_tractor_pos_from_device(pos = xh)
        
        
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
import pygame
from game.settings import WIDTH, HEIGHT, FPS, WHITE
from game.world import World


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Haptic Farming - Task 1")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)

    world = World()
    use_mouse_control = True

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    use_mouse_control = not use_mouse_control

        keys = pygame.key.get_pressed()

        if use_mouse_control:
            mouse_pos = pygame.mouse.get_pos()
            world.tractor.move_towards_mouse(mouse_pos)
        else:
            world.tractor.move_with_keys(keys)

        world.update()
        world.draw(screen, font)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
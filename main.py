import os
import pygame
from pygame import sprite, display, mouse
from pygame.locals import *
from utils import load_image

main_dir = os.path.split(os.path.abspath(__file__))[0]

BULLETS = pygame.sprite.RenderPlain()



class Bullet(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self, BULLETS)
        self.image, self.rect = load_image('blast.png', -1)
        screen = display.get_surface()
        self.area = screen.get_rect()

    def update(self):
        pos = mouse.get_pos()
        self.rect.midtop = pos




# here's the full code
def main():
    pygame.init()
    screen = pygame.display.set_mode((480, 480))

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    # scale the background image so that it fills the window and
    #   successfully overwrites the old sprite position.
    screen.blit(background, (0, 0))
    pygame.display.flip()

    tank = Tank((1, 1))
    b = Bullet()
    clock = pygame.time.Clock()

    while 1:

        clock.tick(60)
        for event in pygame.event.get():
            if event.type in (QUIT, KEYDOWN):
                break

        for t, bs in sprite.groupcollide(BASES, BULLETS, 0, 1).items():
            for b in bs:
                print(b)

        tank.update()
        BULLETS.update()
        screen.blit(background, (0, 0))
        tank.draw(screen)
        BULLETS.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__': main()

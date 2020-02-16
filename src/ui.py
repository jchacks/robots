import pygame

class Overlay(object):
    def __init__(self, robots):
        self._robots = robots

    def on_render(self, screen):
        offset = 0
        for robot in self._robots:
            offset = self.draw(screen, robot, offset)

    def draw(self,screen, robot, offset):
        if pygame.font:
            font = pygame.font.Font(None, 36)
            text = font.render(str(robot.__class__.__name__), 1, (255, 255, 255))
            textpos = text.get_rect(left=0, top=offset)
            screen.blit(text, textpos)

            backgr = pygame.Surface((100, 4))
            backgr.fill((255, 0, 0))
            if robot.energy > 0:
                energy = pygame.Surface((robot.energy, 2))
                energy.fill((0, 255, 0))
                backgr.blit(energy,(0,1))

            backgrpos = backgr.get_rect(left=0, top=textpos.bottom + 2)
            screen.blit(backgr, backgrpos)
            return backgrpos.bottom + 5



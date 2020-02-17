import pygame


class Overlay(object):
    def __init__(self, app, robots):
        self.app = app
        self._robots = robots
        w, h = app.size
        self.bar_dims = (100, 4)
        self.bar_dims = min(100, int(w * 100 / 400)), min(4, int(h * 4 / 400))
        if pygame.font:
            self.font_size = 36
            self.font_size = min(36, int(h * 36 / 400))
            self.font = pygame.font.Font(None, self.font_size)

    def on_resize(self, size):
        w, h = size
        self.bar_dims = min(100, int(w * 100 / 400)), min(4, int(h * 4 / 400))
        self.font_size = min(36, int(h * 36 / 400))
        self.font = pygame.font.Font(None, self.font_size)

    def on_render(self, screen):
        offset = 0
        for robot in self._robots:
            offset = self.draw(screen, robot, offset)

    def draw(self, screen, robot, offset):
        text = self.font.render(str(robot.__class__.__name__), 1, (255, 255, 255))
        textpos = text.get_rect(left=0, top=offset)
        screen.blit(text, textpos)

        backgr = pygame.Surface(self.bar_dims)
        backgr.fill((255, 0, 0))
        if robot.energy > 0:
            energy = pygame.Surface((robot.energy * self.bar_dims[0], 2))
            energy.fill((0, 255, 0))
            backgr.blit(energy, (0, 1))

        backgrpos = backgr.get_rect(left=0, top=textpos.bottom + 2)
        screen.blit(backgr, backgrpos)
        return backgrpos.bottom + 5

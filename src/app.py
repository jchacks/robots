import os
import time

import pygame

from robot import Bullet
from robots import RandomRobot, MyFirstRobot
from random import randint


# robots = []
# for path in os.listdir('robots'):
#     name = path.split('.')[0]
#     robot_class = __import__('robots.' + name, fromlist=[''])
#     robots.append(getattr(robot_class, name))
#
# robots = robots[1:]

class Battle(object):
    def __init__(self, size, robots):
        self.size = size
        self.ratio = size[0] / size[1]
        self.robots_classes = robots
        self.robots = []
        self.iterations = 10
        # display stuff
        self.scale_size = None
        self.surface = None
        self.rect = None

        # Iteration stuff
        self.last_sim = 0
        self.sim_rate = 60
        self.sim_interval = 1.0 / self.sim_rate
        self.simulate = False

    def on_init(self):
        self.surface = pygame.Surface(self.size)
        self.rect = self.surface.get_rect()
        self.surface = self.surface.convert()
        size = w, h = self.surface.get_size()
        self.bg = pygame.Surface(size)
        self.bg = self.bg.convert()
        self.surface.blit(self.bg, (0, 0))
        for Robot in self.robots_classes:
            robot = Robot(self, (randint(20, w - 20), randint(20, h - 20)), randint(0, 360))
            robot.on_init()
            self.robots.append(robot)

    def on_resize(self, size):
        nw, nh = size
        w, h = self.size
        r = min(nw / w, nh / h)
        w = int(w * r)
        h = int(h * r)
        self.scale_size = w, h

    def on_render(self, screen):
        self.surface.blit(self.bg, (0, 0))
        for robot in self.robots:
            robot._draw(self.surface)
        Bullet.draw(self.surface)

        resized = pygame.transform.smoothscale(self.surface, self.scale_size)
        resizedpos = resized.get_rect(centerx=screen.get_width() / 2, centery=screen.get_height() / 2)
        screen.blit(resized, resizedpos)

    def step(self):
        self.last_sim = time.time()
        for bullet in Bullet.class_group:
            bullet.delta()
        for robot in self.robots:
            robot.collide_bullets()
        for robot in self.robots:
            robot.update_logic()
        for robot in self.robots:
            robot.collide_wall()
        for robot in self.robots:
            robot.collide_robots()
        for robot in self.robots:
            robot.collide_scan(self.robots)
        Bullet.collide_bullets()

    def on_loop(self):
        if (time.time() - self.last_sim >= self.sim_interval) and self.simulate:
            self.step()

    def on_event(self, event):
        if event.key == pygame.K_w:
            self.sim_rate += 10
            self.sim_interval = 1.0 / self.sim_rate
            print(self.sim_rate, self.sim_interval)
        elif event.key == pygame.K_s:
            self.sim_rate = max(1, self.sim_rate - 10)
            self.sim_interval = 1.0 / self.sim_rate
            print(self.sim_rate, self.sim_interval)
        elif event.key == pygame.K_p:
            self.simulate = not self.simulate
        elif event.key == pygame.K_l:
            self.step()


class App(object):
    def __init__(self):
        self._running = True
        self.screen = None
        self.rect = None
        self.size = 1080, 800

        self.render = True
        self.last_render = 0
        self.render_rate = 120
        self.render_interval = 1.0 / self.render_rate

    def on_init(self):
        pygame.init()
        pygame.font.init()
        self._running = True
        self.battle = Battle((600, 400), [RandomRobot.RandomRobot, MyFirstRobot.MyFirstRobot])
        self.init_screen()
        self.battle.on_init()

    def init_screen(self):
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()

    def on_resize(self, size):
        self.size = size
        self.init_screen()
        self.battle.on_resize(size)

    def render_text(self, text):
        if pygame.font:
            font = pygame.font.Font(None, 36)
            text = font.render(str(text), 1, (255, 255, 255))
            textpos = text.get_rect(right=self.screen.get_width(), top=0)
            self.screen.blit(text, textpos)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.VIDEORESIZE:
            self.on_resize(event.dict['size'])
        elif event.type == pygame.KEYDOWN:
            self.battle.on_event(event)

    def on_render(self):
        if (time.time() - self.last_render >= self.render_interval):
            self.last_render = time.time()
            self.screen.blit(self.bg, (0, 0))
            self.battle.on_render(self.screen)
            self.render_text(int(1 / max(1, time.time() - self.battle.last_sim)))
            pygame.display.flip()

    def on_loop(self):
        if self.battle:
            self.battle.on_loop()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False
        while self._running:
            s = time.time()
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            if self.render:
                self.on_render()
            if not self.render and not self.battle.simulate:
                time.sleep(0.1)
            # print(time.time()-s)

        self.on_cleanup()


if __name__ == "__main__":
    app = App()
    app.on_execute()

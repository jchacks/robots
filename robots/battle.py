import time
from collections import deque
from random import randint

import pygame

from robots.robot.parts import Bullet
from robots.ui import Overlay


class Battle(object):
    def __init__(self, app, size, robots):
        self.app = app
        self.size = size
        self.ratio = size[0] / size[1]
        self.iterations = 10
        # display stuff
        self.scale_size = None
        self.surface = None
        self.rect = None

        # Iteration stuff
        self.sim_rate = -1
        self.sim_interval = 1.0 / self.sim_rate
        self.simulate = True
        self.sim_times = deque(maxlen=1000)

        # self.robots = [R() for R in self.robots_classes]
        self.robots = robots

    @property
    def alive_robots(self):
        return [r for r in self.robots if not r.dead]

    def on_init(self):
        # Draw stuff
        self.surface = pygame.Surface(self.size)
        self.rect = self.surface.get_rect()
        self.surface = self.surface.convert()
        size = w, h = self.surface.get_size()
        self.bg = pygame.Surface(size)
        self.bg = self.bg.convert()
        pygame.draw.rect(self.bg, (255, 0, 0), self.bg.get_rect(), 1)
        self.surface.blit(self.bg, (0, 0))

        # Simulation stuff
        self.tick = 0
        self.last_sim = 0

        Bullet.on_init()
        # Add bots
        for robot in self.robots:
            robot.set_bearing(randint(0, 360))
            robot.set_position((randint(20, w - 20), randint(20, h - 20)))
            robot.on_init()
        self.overlay = Overlay(self.app, self.robots)

    def on_clean_up(self):
        for robot in self.robots:
            robot.destroy()

    def on_resize(self, size):
        nw, nh = size
        w, h = self.size
        r = min(nw / w, nh / h)
        w = int(w * r)
        h = int(h * r)
        self.scale_size = w, h
        self.overlay.on_resize(size)

    def on_render(self, screen):
        self.surface.blit(self.bg, (0, 0))
        for robot in self.robots:
            robot._draw(self.surface)
        for bullet in Bullet.bullets:
            bullet.draw(self.surface)

        resized = pygame.transform.smoothscale(self.surface, self.scale_size)
        resizedpos = resized.get_rect(centerx=screen.get_width() / 2, centery=screen.get_height() / 2)
        screen.blit(resized, resizedpos)
        self.overlay.on_render(screen)

    def check_round_over(self):
        alive = sum(not robot.dead for robot in self.robots)
        if alive > 1:
            return False
        return True

    def get_sim_times(self):
        if len(self.sim_times) > 0:
            return sum(self.sim_times) / len(self.sim_times)
        else:
            return -1

    def step(self):
        self.last_sim = time.time()
        for bullet in Bullet.bullets.copy():
            bullet.delta(self.tick)
        for robot in self.alive_robots:
            robot.collide_bullets()
        for robot in self.alive_robots:
            robot.delta(self.tick)
        self.collide_walls()
        for robot in self.alive_robots:
            robot.collide_robots(self.robots)
        for robot in self.alive_robots:
            robot.collide_scan(self.alive_robots)
        Bullet.collide_bullets()
        if self.check_round_over():
            self.on_clean_up()
            self.on_init()

    def collide_walls(self):
        for robot in self.robots:
            if not robot.dead:
                if not self.rect.contains(robot.rect):
                    robot.collided_wall(self.size)

        for bullet in Bullet.bullets.copy():
            if not self.rect.contains(bullet.rect):
                bullet.clean_up()

    def on_loop(self):
        s = time.time()
        if ((s - self.last_sim) >= self.sim_interval) and self.simulate:
            self.step()
            self.sim_times.append(time.time() - s)
            self.tick += 1
        print(round(self.get_sim_times(), 5), round(1 / self.get_sim_times()), self.tick)

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

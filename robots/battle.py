import time
from collections import deque
from random import randint

import numpy as np
import pygame

from robot.utils import test_circles
from robots.robot.events import BattleEndedEvent
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
        self.is_finished = False
        self.sim_rate = -1
        self.sim_interval = 1.0 / self.sim_rate
        self.simulate = True
        self.sim_times = deque(maxlen=1000)

        self._robots = robots
        self.robots = None

    def set_sim_rate(self, r):
        self.sim_rate = int(r)
        self.sim_interval = 1.0 / self.sim_rate

    @property
    def alive_robots(self):
        return [r for r in self.robots if not r.dead]

    def init_video(self, screen):
        self.surface = screen
        self.rect = self.surface.get_rect()
        size = w, h = self.surface.get_size()
        self.bg = pygame.Surface(size)
        self.bg = self.bg.convert()

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
        Bullet.init_video()
        self.bullets = set()
        # Simulation stuff
        self.tick = 0
        self.last_sim = 0

        # Add bots
        self.robots = []
        for robot_class in self._robots:
            robot = robot_class(self, randint(0, 360))
            robot.set_position((randint(20, w - 20), randint(20, h - 20)))
            robot.on_init()
            self.robots.append(robot)
        self.overlay = Overlay(self.app, self.robots)

    def on_clean_up(self):
        # Remove all bullets
        for bullet in self.bullets.copy():
            bullet.clean_up()
        for robot in self.robots:
            robot.on_battle_ended(BattleEndedEvent(self, self.app.console))
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
        for bullet in self.bullets:
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

    def collide_bullets(self):
        bullets = list(self.bullets)
        if len(bullets) > 1:
            c = np.array([b.center for b in bullets])
            r = np.array([b.radius for b in bullets])
            where = np.argwhere(np.any(test_circles(c, r), 0))
            to_remove = [bullets[idx] for idx in where.flatten().tolist()]
            self.bullets.difference_update(to_remove)

    def get_sim_times(self):
        if len(self.sim_times) > 0:
            return sum(self.sim_times) / len(self.sim_times)
        else:
            return -1

    def on_round_end(self):
        pass

    def step(self):
        self.last_sim = time.time()
        for bullet in self.bullets.copy():
            bullet.delta(self.tick)
        for robot in self.alive_robots:
            robot.collide_bullets()
        self.delta()
        self.collide_walls()
        for robot in self.alive_robots:
            robot.collide_robots(self.robots)
        for robot in self.alive_robots:
            robot.collide_scan(self.alive_robots)
        self.collide_bullets()
        if self.check_round_over():
            self.is_finished = True
            self.on_round_end()
            self.on_clean_up()

    def delta(self):
        for robot in self.alive_robots:
            robot.delta(self.tick)

    def collide_walls(self):
        for robot in self.alive_robots:
            if not self.rect.contains(robot.rect):
                robot.collided_wall(self.size)

        for bullet in self.bullets.copy():
            if not self.rect.contains(bullet.rect):
                bullet.clean_up()

    def on_loop(self):
        s = time.time()
        if ((s - self.last_sim) >= self.sim_interval) and self.simulate:
            self.sim_times.append(time.time() - s)
            self.tick += 1
            self.step()
            # print(round(self.get_sim_times(), 5), round(1 / self.get_sim_times()), self.tick)

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
            print("Simulate", self.simulate)
        elif event.key == pygame.K_l:
            self.step()


class MultiBattle(object):
    def __init__(self, app, size, robots, battles):
        self.battles = [Battle(app, size, robots[:]) for b in range(battles)]

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

        self._robots = robots
        self.robots = None

    def set_sim_rate(self, r):
        self.sim_rate = int(r)
        self.sim_interval = 1.0 / self.sim_rate

    def init_grid(self, screen):
        w, h = screen.get_size()
        w, h = w/2, h/2
        screens = []
        for i in range(2):
            for j in range(2):
                screens.append(screen.subsurface((i*w,j*h, (i+1)*w, (j+1)*h)))


    def init_video(self):

        self.surface = pygame.Surface(self.size)
        self.rect = self.surface.get_rect()
        self.surface = self.surface.convert()
        size = w, h = self.surface.get_size()
        self.bg = pygame.Surface(size)
        self.bg = self.bg.convert()
        pygame.draw.rect(self.bg, (255, 0, 0), self.bg.get_rect(), 1)
        self.surface.blit(self.bg, (0, 0))

    def on_init(self):
        # Draw stuff
        self.init_video()

    def on_render(self, screen):
        self.surface.blit(self.bg, (0, 0))
        # for battle in self.battles: #TODO render each battle in its own size
        self.battles[0].on_render(screen)

    def on_battles_ended(self):
        pass

    def step(self):
        for battle in self.battles:
            battle.last_sim = time.time()
            for bullet in battle.bullets.copy():
                bullet.delta(battle.tick)
            for robot in battle.alive_robots:
                robot.collide_bullets()

        # Allows a hook for updating all battles simultaneously
        self.delta()

        for battle in self.battles:
            battle.collide_walls()
            for robot in battle.alive_robots:
                robot.collide_robots(battle.robots)
            for robot in battle.alive_robots:
                robot.collide_scan(battle.alive_robots)
            battle.collide_bullets()
            if battle.check_round_over():
                battle.is_finished = True
                battle.on_round_end()
                battle.on_clean_up()

    def delta(self):
        for battle in self.battles:
            battle.delta()

    def on_event(self, event):
        for b in self.battles:
            b.on_event(event)

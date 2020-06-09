import math
import time
from random import randint

import numpy as np
import pygame

from robots.robot.events import BattleEndedEvent
from robots.robot.parts import Bullet
from robots.robot.utils import test_circles, Simable
from robots.ui import Overlay, Canvas


class Battle(Canvas, Simable):
    def __init__(self, app, size, robots):
        Canvas.__init__(self, size=size)
        Simable.__init__(self)
        self.app = app
        self._robots = robots
        self.robots = None
        self.sim_rate = 1

    @property
    def alive_robots(self):
        return [r for r in self.robots if not r.dead]

    def init_video(self, screen=None):
        self.screen = screen
        self.init_canvas()
        Bullet.init_video()

    def on_init(self):
        # Draw stuff
        self.bullets = set()
        # Simulation stuff

        w, h = self.size
        # Add bots
        self.robots = []
        for robot_class in self._robots:
            robot = robot_class(self, randint(0, 360))
            robot.set_position((randint(20, w - 20), randint(20, h - 20)))
            robot.on_init()
            robot.init_video()
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
        super(Battle, self).on_resize(size)
        self.overlay.on_resize(size)

    def render(self):
        for robot in self.robots:
            robot._draw(self.canvas)
        for bullet in self.bullets:
            bullet.draw(self.canvas)
        self.overlay.on_render(self.canvas)

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

    def on_round_end(self):
        pass

    def step(self):
        self.last_sim = time.time()
        for bullet in self.bullets.copy():
            bullet.delta(self.tick)
            if not np.all(((0, 0) <= bullet.center) & (bullet.center <= self.size)):
                self.bullets.remove(bullet)
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
            if not np.all(((20, 20) <= robot.position) & (robot.position <= np.array(self.size) - (20, 20))):
                robot.collided_wall(self.size)

        for bullet in self.bullets.copy():
            if not self.rect.contains(bullet.rect):
                bullet.clean_up()

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


class MultiBattle(Simable):
    def __init__(self, app, size, robots, num_battles=4):
        Simable.__init__(self)
        self._robots = robots
        self.battles = None
        self. num_battles = num_battles
        self.app = app
        self.size = size

    def init_grid(self, screen, c=5, r=4):
        w, h = screen.get_size()
        w, h = w // c, h // r
        screens = []
        for i in range(c):
            for j in range(r):
                shape = (int(i * w), int(j * h), int(w), int(h))
                screens.append(screen.subsurface(shape))
        return screens

    def init_video(self, screen):
        self.screen = screen
        self.screens = self.init_grid(self.screen)

    def on_resize(self, size):
        # Alter this to actually change the allotted screen sizes
        pass

    def on_init(self):
        self.battles = [Battle(self.app, self.size, self._robots[:]) for _ in range(self.num_battles)]
        for i, battle in enumerate(self.battles):
            battle.on_init()
            battle.init_video(self.screens[i])

    def on_render(self, screen):
        for i, battle in enumerate(self.battles):  # TODO render each battle in its own size
            battle.on_render()
            resized = pygame.transform.smoothscale(battle.canvas, self.screens[i].get_size())
            resizedpos = resized.get_rect(top=0, left=0)
            self.screens[i].blit(resized, resizedpos)

    def on_battles_ended(self):
        pass

    def step(self):
        if any(not b.is_finished for b in self.battles):
            for battle in self.battles:
                if not battle.is_finished:
                    battle.last_sim = time.time()
                    for bullet in battle.bullets.copy():
                        bullet.delta(battle.tick)
                    for robot in battle.alive_robots:
                        robot.collide_bullets()

            # Allows a hook for updating all battles simultaneously
            self.delta()

            for battle in self.battles:
                if not battle.is_finished:
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
        else:
            self.on_battles_ended()
            self.on_init()

    def delta(self):
        for battle in self.battles:
            battle.delta()

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
        for b in self.battles:
            b.on_event(event)

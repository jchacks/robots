import time
from random import randint

import numpy as np
import pygame

from robots.robot.events import BattleEndedEvent
from robots.robot.renderers import BulletRenderer, RobotRenderer
from robots.robot.utils import test_circles, Simable
from robots.ui import Overlay, Canvas


class BattleDisplay(Canvas):
    def __init__(self, screen, battle):
        Canvas.__init__(self, screen=screen, size=battle.size, background_color="black")
        self.bullet_r = BulletRenderer()
        self.robot_r = RobotRenderer()
        self.battle = None
        self.overlay = None
        self.set_battle(battle)

    def set_battle(self, battle):
        self.battle = battle
        for robot in battle.robots:
            self.robot_r.track(robot)
        self.overlay = Overlay(battle.size, self.battle)
        self.bullet_r.items = self.battle.bullets
        self.on_resize(battle.size)

    def render(self):
        self.robot_r.render(self.canvas)
        self.bullet_r.render(self.canvas)
        self.overlay.on_render(self.canvas)

    def on_resize(self, size):
        super(BattleDisplay, self).on_resize(size)
        self.overlay.on_resize(size)


class Battle(Simable):
    def __init__(self, *, size=(600, 400), robots):
        Simable.__init__(self)
        self.robots = [rc(self) for rc in robots]
        self.size = size
        self.sim_rate = 1
        self.done = False
        self.bullets = set()
        self.reset()

    @property
    def alive_robots(self):
        return [r for r in self.robots if not r.dead]

    def initial_bearing(self, index):
        return randint(0, 360)

    def initial_position(self, index):
        w, h = self.size
        return (randint(20, w - 20), randint(20, h - 20))

    def reset(self):
        self.bullets.clear()
        for i, robot in enumerate(self.robots):
            robot.set_bearing(self.initial_bearing(0))
            robot.set_position(self.initial_position(0))
            robot.reset()

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
        for robot in self.robots:
            robot.on_battle_ended(BattleEndedEvent(self))

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
            self.reset()

    def delta(self):
        for robot in self.alive_robots:
            robot.delta(self.tick)

    def collide_walls(self):
        for robot in self.alive_robots:
            if not np.all(((20, 20) <= robot.position) & (robot.position <= np.array(self.size) - (20, 20))):
                robot.collided_wall(self.size)

        for bullet in self.bullets.copy():
            r = bullet.radius
            if not np.all((r <= bullet.center) & (bullet.center <= np.array(self.size) - r)):
                self.bullets.remove(bullet)


class MultiBattle(Simable):
    def __init__(self, app, size, robots, num_battles=4):
        Simable.__init__(self)
        self._robots = robots
        self.battles = None
        self.num_battles = num_battles
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
        self.screens = self.init_grid(self.screen, 10, 8)

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
                battle.last_sim = time.time()
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
                        for bullet in battle.bullets.copy():
                            bullet.delta(battle.tick)
                        for robot in battle.alive_robots:
                            robot.collide_bullets()
            # Allows a hook for updating all battles simultaneously
            self.delta()
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

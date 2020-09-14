import numpy as np
import time
from random import randint

from robots.robot.events import BattleEndedEvent, WinEvent
from robots.robot.utils import test_circles, Simable


class BattleSettings(object):
    pass


class Battle(Simable):
    def __init__(self, *, size=(600, 400), robots):
        Simable.__init__(self)
        self.robots = [rc(self) for rc in robots]
        self.dirty = True
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
        return randint(20, w - 20), randint(20, h - 20)

    def reset(self):
        self.bullets.clear()
        for i, robot in enumerate(self.robots):
            robot.set_bearing(self.initial_bearing(0))
            robot.gun.set_bearing(self.initial_bearing(0))
            robot.radar.set_bearing(self.initial_bearing(0))
            robot.set_position(self.initial_position(0))
            robot.reset()

    def check_round_over(self):
        alive = sum(not robot.dead for robot in self.robots)
        if alive > 1:
            return False
        return True

    def collide_bullets(self):
        """
        Collide bullets with all other bullets.
        :return:
        """
        bullets = list(self.bullets)
        if len(bullets) > 1:
            c = np.array([b.center for b in bullets])
            r = np.array([b.radius for b in bullets])
            where = np.argwhere(np.any(test_circles(c, r), 0))
            to_remove = [bullets[idx] for idx in where.flatten().tolist()]
            self.bullets.difference_update(to_remove)

    def on_round_end(self):
        for robot in self.robots:
            if not robot.dead:
                robot.on_win(WinEvent())
            robot.on_battle_ended(BattleEndedEvent(self))

    def _step(self):
        self.is_finished = False
        self.last_sim = time.time()
        self.collide_walls()
        for robot in self.alive_robots:
            robot.collide_robots(self.robots)
        for robot in self.alive_robots:
            robot.collide_scan(self.alive_robots)
        self.collide_bullets()
        for bullet in self.bullets.copy():
            bullet.delta(self.tick)
        for robot in self.alive_robots:
            robot.collide_bullets()
        if self.check_round_over():
            self.is_finished = True
            self.on_round_end()
            self.reset()

    def step(self, *args):
        self._step()
        self.delta(*args)
        self.dirty = True

    def delta(self, *args):
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

    def to_dict(self):
        return {
            "tick": self.tick,
            "robots": [r.to_dict() for r in self.robots],
            "bullets": [(b.radius, list(b.center), list(b.direction)) for b in list(self.bullets)],
        }


class MultiBattle(Simable):
    def __init__(self, size, robots, num_battles=4):
        Simable.__init__(self)
        self.robots = robots
        self.dirty = True
        self.size = size
        self.num_battles = num_battles
        self.battles = [Battle(size=self.size, robots=self.robots) for _ in range(self.num_battles)]

    def reset(self):
        for battle in self.battles:
            battle.reset()

    def step(self, *args, **kwargs):
        for battle in self.battles:
            battle._step()
            if battle.check_round_over():
                battle.is_finished = True
                battle.on_round_end()
                battle.reset()
        # Allows a hook for updating all battles simultaneously
        res = self.delta(*args, **kwargs)
        self.dirty = True
        return res

    def delta(self, *args):
        for battle in self.battles:
            battle.delta()
        return True

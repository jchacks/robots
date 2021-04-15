import numpy as np
import time
from random import randint

from robots.robot.events import BattleEndedEvent, WinEvent
from robots.engine.utils import test_circles


class BattleSettings(object):
    def __init__(self, robots, size=(600, 400)) -> None:
        self.robots = robots
        self.size = size

class Battle(object):
    def __init__(self, *, size=(600, 400), robots):
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

    def check_round_over(self):
        alive = sum(not robot.dead for robot in self.robots)
        if alive > 1:
            return False
        return True

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


# class MultiBattle(App):
#     """
#     Class that extends the Normal App class to render a multi Battle window
#     for when a multibattle is being used instead of a normal `Battle`
#     """

#     def __init__(self, *args, rows=None, columns=None, **kwargs):
#         super(MultiBattleApp, self).__init__(*args, **kwargs)
#         self.rows = rows
#         self.columns = columns

#     def init_window(self):
#         self.battle_display = MultiBattleWindow(self.screen, self.battle, rows=self.rows, columns=self.columns)

#     def create_default_battle(self):
#         return MultiBattle(size=(400, 400), robots=[TestRobot, TestRobot], num_battles=2)

#     def on_render(self):
#         if (time.time() - self.last_render) >= self.render_interval:
#             self.last_render = time.time()
#             self.battle_display.on_render(self.screen)
#             self.console.on_render(self.screen)
#             pygame.display.flip()


class MultiBattle(object):
    def __init__(self, size, robots, num_battles=4):
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

from RoboArena import *
from robots.app import App, Battle
import random
import time


class RandomRobot(PyRobot):
    def run(self):
        self.moving = random.randint(-1, 1)
        self.base_turning = random.randint(-1, 1)
        self.turret_turning = random.randint(-1, 1)
        if random.randint(0, 1):
            self.fire(3.0)

    def on_hit_robot(self):
        print(f"{self} on_hit_robot")

    def on_bullet_hit(self):
        print(f"{self} on_bullet_hit")

    def on_hit_by_bullet(self):
        print(f"{self} on_hit_by_bullet")


robots = [RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))]
eng = Engine(robots=robots)
eng.init()

with_app = False
if not with_app:
    steps = int(1e8)
    s = time.perf_counter_ns()
    for i in range(steps):
        eng.step()
    f = time.perf_counter_ns()

else:
    steps = int(1e5)
    app = App()
    app.child = Battle((600, 400), eng=eng)
    s = time.perf_counter_ns()
    for i in range(steps):
        app.step()
    f = time.perf_counter_ns()

t = f - s
ts = t * 1e-9
print(f"{steps}steps {t}ns {ts}s {ts/steps}s/f {steps/ts}f/s")

from robots.engine_c.engine import *
from robots.app import App, Battle
import random


class RandomRobot(PyRobot):
    def run(self):
        # print("Running", self)
        self.moving = 1
        self.base_turning = 1
        self.turret_turning = -1
        if random.randint(0, 1):
            self.fire(random.randint(1, 3))

num_engines = 1000
engines = []
for i in range(num_engines):
    eng = Engine(robots=[RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))])
    eng.init()
    engines.append(eng)
print(f"Created {len(engines)} engines")

import time
frames = int(1e4)
start = time.perf_counter_ns()
for i in range(frames):
    for eng in engines:
        eng.step()
duration = (time.perf_counter_ns() - start)/1e9
print(frames*num_engines/duration, duration)

eng = engines[0]
frames = int(1e7)
start = time.perf_counter_ns()
for i in range(frames):
    eng.step()
duration = (time.perf_counter_ns() - start)/1e9
print(frames/duration, duration)

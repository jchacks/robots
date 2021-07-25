from robots.engine_c.engine import *
from robots.app import App, Battle
import random

import time
# app = App()

class RandomRobot(Robot):
    def run(self):
        self.moving = 1
        self.base_turning = 1
        self.turret_turning = -1
        if random.randint(0, 1):
            self.fire(random.randint(1, 3))

robots = [RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))]
eng = Engine(robots=robots)

# app.child = Battle(robots, (600, 400), eng=eng)
# app.child.set_tick_rate(-1)
# app.run()


print(eng)
eng.step()
print([(b.uid, b.owner_uid) for b in eng.bullets])


start = time.perf_counter_ns()
for i in range(int(1e6)):
    eng.step()

duration = (time.perf_counter_ns() - start)/1e9
print(100000/(duration), duration)
print(eng.get_bullets())


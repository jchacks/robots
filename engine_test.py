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

robots = [RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))]
eng = Engine(robots=robots)
eng.init_robots()

app = App()
app.child = Battle(robots, (600, 400), eng=eng)
app.child.set_tick_rate(3)
app.run()


# print(eng)
# print([(b.uid, b.owner_uid) for b in eng.bullets])
# for i in range(int(20)):
#     eng.step()


# frames = int(1e5)
# start = time.perf_counter_ns()
# for i in range(frames):
#     eng.step()
# print(eng.bullets)
# duration = (time.perf_counter_ns() - start)/1e9
# print(frames/duration, duration)


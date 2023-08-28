from RoboArena import *
from robots.app import App, Battle
import random


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

app = App()
app.child = Battle((600, 400), eng=eng)
app.console.add_command(
    "sim", app.child.set_tick_rate, help="Sets the Simulation rate."
)
app.child.set_tick_rate(1)
app.run()

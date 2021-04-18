from robots.app import App, Battle
from robots.robot import Robot
from robots.robot.utils import *
import random

app = App()

class RandomRobot(Robot):
    def run(self):
        self.moving = Move.FORWARD
        self.base_turning = Turn.LEFT
        self.turret_turning = Turn.RIGHT
        if random.randint(0, 1):
            self.fire(random.randint(1, 3))


robots = [RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))]
app.child = Battle(robots, (600,400))
app.run()
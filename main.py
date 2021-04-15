from robots.config import BattleSettings
from robots.app import App
from robots.robot import Robot
from robots.robot.utils import *
import random


class RandomRobot(Robot):
    def run(self):
        self.moving = Move.FORWARD
        self.base_turning = Turn.LEFT
        if random.randint(0, 1):
            self.fire(random.randint(1, 3))


battle_settings = BattleSettings([RandomRobot((255, 0, 0)), RandomRobot((0, 255, 0))])
app = App(battle_settings)
app.run()
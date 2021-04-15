import time
from robots.battle import BattleSettings
from robots.ui.ui import BattleWindow
from robots.engine import Engine
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


app = App()
bw = BattleWindow(app.screen, battle_settings.size)
app.children = [bw]


import threading as th

def do():
    while True:
        eng = Engine(battle_settings)
        eng.init()
        bw.set_battle(eng)
        eng.run()
        del eng

thread = th.Thread(target=do)
thread.start()
app.run()

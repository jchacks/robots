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
eng = Engine(battle_settings)
eng.init()

app = App()
app.on_init()
app.children.append(BattleWindow(app.screen, eng))

app.on_render()
for i in range(1000):
    eng.run()
    app.on_render()
    for event in app.get_events():
        app.on_event(event)
    app.on_render()
    time.sleep(0.1)

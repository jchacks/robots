import random

from robots import AdvancedRobot


class RandomRobot(AdvancedRobot):
    def do(self):
        self.move_forward(random.randint(50, 500))
        self.turn_left(random.randint(0, 360))
        if random.randint(0, 1):
            self.fire(random.randint(1, 3))

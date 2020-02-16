from robot import Robot
import random


class RandomRobot(Robot):
    def do(self):
        self.move_forward(random.randint(0, 20))
        self.turn_left(random.randint(0, 50))
        if random.randint(0, 1):
            self.fire(random.randint(1, 3))

    def on_scanned(self, scanned):
        pass

    def on_hit_robot(self, event):
        pass

    def on_hit_by_bullet(self, event):
        pass
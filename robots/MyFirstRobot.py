from robot import Robot


class MyFirstRobot(Robot):
    def do(self):
        self.move_forward(1000)
        self.turn_left(360)

    def on_scanned(self, scanned):
        self.fire(1)

    def on_hit_robot(self, event):
        pass

    def on_hit_by_bullet(self, event):
        pass
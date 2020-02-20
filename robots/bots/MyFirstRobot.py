from robots import AdvancedRobot


class MyFirstRobot(AdvancedRobot):
    def __init__(self, *args, **kwargs):
        super(MyFirstRobot, self).__init__(*args, **kwargs)
        self.radar.locked = True
        self.gun.locked = True

    def do(self, tick):
        self.move_forward(1000)
        self.turn_left(360)

    def on_scanned_robot(self, scanned):
        self.fire(1)

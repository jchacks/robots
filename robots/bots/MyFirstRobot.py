from robots import AdvancedRobot


class MyFirstRobot(AdvancedRobot):
    def __init__(self, *args, **kwargs):
        super(MyFirstRobot, self).__init__(*args, **kwargs)
        self.radar.color = 'yellow'
        self.gun.color = 'blue'
        self.base.color = 'red'

        self.radar.locked = True
        self.gun.locked = True

    def do(self, tick):
        self.move_forward(100)
        self.turn_left(360)

    def on_scanned_robot(self, scanned):
        self.fire(1)

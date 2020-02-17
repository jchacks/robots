from robots import AdvancedRobot


class TestRobot(AdvancedRobot):
    def __init__(self, *args, **kwargs):
        super(TestRobot, self).__init__(*args, **kwargs)
        self.radar.locked = True
        self.gun.locked = True

    def do(self):
        self.turn_left(360)

    def on_scanned(self, scanned):
        print(scanned)
        self.fire(3)

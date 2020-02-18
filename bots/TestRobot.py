from pygame.draw import circle

from robots import AdvancedRobot


class TestRobot(AdvancedRobot):
    def on_init(self):
        super(TestRobot, self).on_init()
        self.set_max_rotation(1)
        self.radar.locked = True
        self.gun.locked = True
        self.scans = []

    def do(self, tick):
        self.turn_left(360)
        self.move_forward(1)

    def on_scanned_robot(self, scanned):
        self.scans.append((self.position, scanned))
        self.fire(3)
        print(self.scans)

    def draw(self, surface):
        for pos, scan in self.scans:
            circle(surface, (255, 255, 0), ((pos + scan.bearing) * scan.distance).astype(int), 2)

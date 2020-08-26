from pygame.draw import circle

from robots import AdvancedRobot


class TestRobot(AdvancedRobot):
    def reset(self):
        super(TestRobot, self).reset()
        self.radar.locked = True
        self.gun.locked = True
        self.scans = []

    def do(self, tick):
        self.turn_left(360)

    def on_scanned_robot(self, scanned):
        self.scans.append((self.position, scanned[0]))
        self.fire(3)

    def draw(self, surface):
        for pos, scan in self.scans:
            print(scan)
            circle(surface, (255, 255, 0), pos + (scan.direction * (scan.distance/2)).astype(int), 2)

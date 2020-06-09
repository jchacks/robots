from pygame.draw import circle

from robots import AdvancedRobot


class DoNothing(AdvancedRobot):
    def on_init(self):
        super(DoNothing, self).on_init()
        self.radar.locked = True
        self.gun.locked = True
        self.scans = []

    def do(self, tick):
        pass

    def on_scanned_robot(self, scanned):
        self.scans.append((self.position, scanned[0]))
        self.fire(3)

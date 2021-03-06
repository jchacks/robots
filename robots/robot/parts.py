import os

from robots.robot.utils import LogicalObject, Rotatable

__all__ = [
    "Bullet",
    "Radar",
    "Gun",
    "Base",
]

data_dir = os.path.join(os.path.dirname(__file__), "../../data/")


class Bullet(LogicalObject):
    MAX_POWER = 3.0
    MIN_POWER = 0.1

    def __init__(self, robot, power):
        LogicalObject.__init__(self, robot.gun.bearing)
        self.robot = robot
        self.power: float = max(min(self.MAX_POWER, power), self.MIN_POWER)
        self.radius = 3
        self.speed = 20 - (3 * self.power)
        self.damage = 4 * self.power
        if self.power > 1:
            self.damage += 2 * (self.power - 1)

        color_level = int(255 * (1 - (self.power / self.MAX_POWER)))
        self.color = (255, color_level, color_level)

    @property
    def int_center(self):
        return self.center.astype("int16")

    @property
    def rotation_speed(self):
        return 0

    def delta(self, tick):
        self.center += self.velocity

    @property
    def velocity(self):
        return self.direction * self.speed

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.robot}, {self.center}, {self.bearing}, {self.power}, {self.color}>"


class Gun(Rotatable):
    def __init__(self, robot):
        super(Gun, self).__init__(robot.bearing)
        self.robot = robot
        self.locked = False
        self.heat = 1.0
        self.set_max_rotation(2)

    @property
    def tip_location(self):
        return self.robot.center + (self.direction * 28)

    def delta(self):
        if self.locked:
            self.bearing = self.robot.bearing
        else:
            self.bearing = (self.bearing + self.get_bearing_delta() + self.robot.get_bearing_delta()) % 360

        self.heat = max(self.heat - 0.1, 0)

    @property
    def rotation_speed(self):
        return 20


class Radar(Rotatable):
    def __init__(self, robot):
        super(Radar, self).__init__(robot.bearing)
        self.robot = robot
        self.locked = False
        self.last_bearing = robot.bearing

    def delta(self):
        self.last_bearing = self.bearing
        if self.locked:
            self.bearing = self.robot.gun.bearing
        else:
            self.bearing = (
                self.bearing
                + self.get_bearing_delta()
                + self.robot.get_bearing_delta()
                + self.robot.gun.get_bearing_delta()
            ) % 360

    @property
    def scan_endpoint(self):
        return self.robot.center + (self.direction * 1200)

    @property
    def rotation_speed(self):
        return 5  # 45


class Base(Rotatable):
    def __init__(self, robot):
        super(Base, self).__init__(robot.bearing)
        self.robot = robot

    def delta(self):
        self.bearing = self.robot.bearing

    @property
    def rotation_speed(self):
        return 0

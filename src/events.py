
class Event(object):
    pass


class ScannedRobotEvent(Event):
    def __init__(self, robot):
        self.energy = robot.energy


class HitByRobotEvent(Event):
    pass


class HitByBulletEvent(Event):
    def __init__(self, bullet):
        self.damage = bullet.damage


class HitBulletEvent(Event):
    def __init__(self, bullet):
        self.damage = bullet.damage


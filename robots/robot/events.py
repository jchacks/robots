import numpy as np

__all__ = [
    'BattleEndedEvent',
    'BulletHitBulletEvent',
    'BulletHitEvent',
    'BulletMissedEvent',
    'CustomEvent',
    'DeathEvent',
    'HitByBulletEvent',
    'HitRobotEvent',
    'HitWallEvent',
    'KeyEvent',
    'MessageEvent',
    'MouseEvent',
    'PaintEvent',
    'RobotDeathEvent',
    'RoundEndedEvent',
    'ScannedRobotEvent',
    'SkippedTurnEvent',
    'StatusEvent',
    'WinEvent',
]


class Event(object):
    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self.__dict__)


class BattleEndedEvent(Event):
    def __init__(self, battle):
        self.battle = battle


class BulletHitBulletEvent(Event):
    pass


class BulletHitEvent(Event):
    def __init__(self, bullet, robot):
        self.damage = bullet.damage
        self.robot = robot.name


class BulletMissedEvent(Event):
    pass


class CustomEvent(Event):
    pass


class DeathEvent(Event):
    pass


class HitByBulletEvent(Event):
    def __init__(self, bullet):
        self.damage = bullet.damage


class HitRobotEvent(Event):
    def __init__(self, robot):
        self.energy = robot.energy
        self.position = robot.center


class HitWallEvent(Event):
    pass


class KeyEvent(Event):
    pass


class MessageEvent(Event):
    pass


class MouseEvent(Event):
    pass


class PaintEvent(Event):
    pass


class RobotDeathEvent(Event):
    pass


class RoundEndedEvent(Event):
    pass


class ScannedRobotEvent(Event):
    def __init__(self, scanner, robot):
        d = (robot.center - scanner.center)
        h = np.sqrt(np.sum(d ** 2))
        self.direction = d / h
        self.distance = h
        self.energy = robot.energy
        self.heading = robot.bearing
        self.velocity = robot.velocity


class SkippedTurnEvent(Event):
    pass


class StatusEvent(Event):
    def __init__(self, battle, robot):
        self.num_other = sum(1 for robot in battle.robots if not robot.dead) - 1


class WinEvent(Event):
    pass

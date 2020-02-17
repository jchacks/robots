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
    pass


class BattleEndedEvent(Event):
    pass


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
    def __init__(self, robot):
        self.energy = robot.energy


class SkippedTurnEvent(Event):
    pass


class StatusEvent(Event):
    pass


class WinEvent(Event):
    pass

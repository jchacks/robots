
ROBOT_RADIUS = 24
BULLET_RADIUS = 3
MAX_SPEED = (-8.0, 8.0)
MAX_POWER = 3.0
MIN_POWER = 0.1

class BattleSettings(object):
    def __init__(self, robots, size=(600, 400), rounds=-1) -> None:
        self.robots = robots
        self.size = size
        self.num_rounds = rounds

from enum import Enum

class Turn(Enum):
    NONE = 0
    LEFT = -1
    RIGHT = 1


class Move(Enum):
    NONE = 0
    FORWARD = 1
    BACK = -1


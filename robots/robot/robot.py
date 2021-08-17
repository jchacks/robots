import logging
import numpy as np
from abc import ABC, abstractmethod
from robots.robot.events import *
from robots.robot.utils import Move, Turn
from typing import List

logger = logging.getLogger(__name__)


class Robot(ABC):
    def __init__(self, base_color, turret_color=None, radar_color=None) -> None:
        # Other args useful for storing custom information

        # Attributes are set by engine.
        self.energy = 100
        self.position = None
        self.base_rotation = None
        self.turret_rotation = None
        self.radar_rotation = None
        self.velocity = 0.0
        self.turret_heat = 0.0

        self.base_turning_velocity = 0.0
        self.turret_turning_velocity = 0.0
        self.radar_turning_velocity = 0.0

        self.alive = False

        # Set by user and read by engine.
        self.base_color = base_color
        self.turret_color = turret_color if turret_color is not None else base_color
        self.radar_color = radar_color if radar_color is not None else base_color

        self.should_fire = False
        self.fire_power = 3.0
        self.moving = Move.NONE
        self.base_turning = Turn.NONE
        self.turret_turning = Turn.NONE
        self.radar_turning = Turn.NONE

    def init(self, *args, **kwargs):
        pass

    def get_visible_attrs(self):
        """Used for information available to
        other robots on scan for instance"""
        return {
            "energy": self.energy,
            "position": self.position.copy(),
            "direction": self.direction,
            "turret_direction": self.turret_direction,
            "velocity": self.velocity,
        }

    @property
    def direction(self):
        return np.cos(self.base_rotation), np.sin(self.base_rotation)

    @property
    def turret_direction(self):
        return np.cos(self.turret_rotation), np.sin(self.turret_rotation)

    @property
    def heat_pctg(self):
        return self.turret_heat / (1 + 3 / 5)

    @property
    def energy_pctg(self):
        return self.energy / 100

    def __repr__(self):
        return (
            f"{self.__class__.__name__}<"
            f"Velocity: {self.velocity}, "
            f"Rotation:  {self.base_rotation} degs, "
            f"Position: {self.position}, "
            f"Energy:   {self.energy}>"
        )

    def run(self):
        pass

    def fire(self, power):
        self.fire_power = power
        self.should_fire = True

    def on_battle_ended(self, event: BattleEndedEvent):
        pass

    def on_bullet_hit_bullet(self, event: BulletHitBulletEvent):
        pass

    def on_bullet_hit(self, event: BulletHitEvent):
        pass

    def on_bullet_missed(self, event: BulletMissedEvent):
        pass

    def on_custom_event(self, event: CustomEvent):
        pass

    def on_death(self, event: DeathEvent):
        pass

    def on_hit_by_bullet(self, event: List[HitByBulletEvent]):
        pass

    def on_hit_robot(self, event: HitRobotEvent):
        pass

    def on_hit_wall(self, event: HitWallEvent):
        pass

    def on_key(self, event: KeyEvent):
        pass

    def on_message(self, event: MessageEvent):
        pass

    def on_paint(self, event: PaintEvent):
        pass

    def on_robot_death(self, event: RobotDeathEvent):
        pass

    def on_round_ended(self, event: RoundEndedEvent):
        pass

    def on_scanned_robot(self, event: List[ScannedRobotEvent]):
        pass

    def on_skipped_turn(self, event: SkippedTurnEvent):
        pass

    def on_status(self, event: StatusEvent):
        pass

    def on_win(self, event: WinEvent):
        pass


class AdvancedRobot(Robot, ABC):
    """Allows for queuing of commands."""

    def turn(self, angle):
        self.left_to_turn
        self.base_rotation

    def run(self):
        self.left_to_move -= self.velocity
        self.left_to_turn -= self.base_turning_velocity
        if self.left_to_turn == 0 and self.left_to_move == 0:
            self.do()

    @abstractmethod
    def do(self):
        pass

    @property
    def moving(self):
        if self.left_to_move > 0:
            return Move.FORWARD
        elif self.left_to_move < 0:
            return Move.BACK
        else:
            return Move.NONE

    @moving.setter
    def moving(self, move):
        pass

    @property
    def turning(self):
        if self.left_to_turn > 0:
            return Turn.LEFT
        elif self.left_to_turn < 0:
            return Turn.RIGHT
        else:
            return Turn.NONE

    @turning.setter
    def turning(self, turn):
        pass

    def move_forward(self, dist: float):
        self.left_to_move = dist

    def turn_left(self, angle: float):
        self.left_to_turn = angle

    def turn_right(self, angle: float):
        self.left_to_turn = -angle

    def __hash__(self):
        return id(self)

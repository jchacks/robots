import logging
import numpy as np
from abc import ABC
from robots.robot.events import *
from robots.robot.utils import Move, Turn
from typing import List

logger = logging.getLogger(__name__)


class Robot(ABC):
    def __init__(self, base_color, turret_color=None, radar_color=None) -> None:
        # Attributes are set by engine.
        self.energy = 100
        self.position = None
        self.bearing = None
        self.turret_bearing = None
        self.radar_bearing = None
        self.velocity = 0.0
        self.dead = False

        # Set by user and read by engine.
        self.base_color = base_color
        self.turret_color = turret_color if turret_color is not None else base_color
        self.radar_color = radar_color if radar_color is not None else base_color

        self.should_fire = False
        self.fire_power = 3
        self.moving = Move.NONE
        self.base_turning = Turn.NONE
        self.turret_turning = Turn.NONE
        self.radar_turning = Turn.NONE

    def __repr__(self):
        return f"{self.__class__.__name__}<"\
            f"Velocity: {self.velocity}, " \
            f"Bearing:  {self.bearing/np.pi}pi rads, " \
            f"Position: {self.position}, "\
            f"Energy:   {self.energy}>"

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


# TODO old style to reimplement in engines
class AdvancedRobot(Robot):
    """
    Subclasses Robot allowing for simultaneous movement of all parts (Base, Turret, Radar).
    """

    def delta(self, tick):
        if not self.dead:
            if self.energy < 0.0:
                self.dead = True
            else:
                # TODO check that the order of operations executes correctly i.e. velocity updated then self.rotation_speed
                if not self.commands:
                    self.do(tick)
                    self.commands = True

                self._speed = np.clip(self._speed + self.acceleration, -8.0, 8.0)
                self.left_to_move = max(0, self.left_to_move - self._speed)

                self.center = self.center + self.velocity
                self.bearing = (self.bearing + self.get_bearing_delta()) % 360
                self.left_to_turn = max(0, self.left_to_turn - self.rotation_speed)
                self.base.delta()
                self.gun.delta()
                self.radar.delta()
                if self.should_fire:
                    self.fire(self.fire_power)

        if self.moving is Move.NONE and self.turning is Turn.NONE:
            self.commands = False

    def reset(self):
        super(AdvancedRobot, self).reset()
        self.left_to_move = 0.0
        self.left_to_turn = 0.0

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

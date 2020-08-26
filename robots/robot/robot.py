import logging
from abc import ABC, abstractmethod
from typing import List

import numpy as np
import pygame

from robots.robot.events import *
from robots.robot.parts import *
from robots.robot.utils import Move, LogicalObject, Turn
from robots.robot.utils import test_circle_circle, test_circle_to_circles

logger = logging.getLogger(__name__)


class Robot(LogicalObject, ABC):
    """
    Abstract Robot class to be subclassed by any custom robots.
    Controls movement, collision and rendering of robots.
    """

    def __init__(self, battle, bearing=0.0):
        LogicalObject.__init__(self, bearing, (36, 36))
        self.name = self.__class__.__name__
        self.battle = battle
        self.radius = 22
        self.radar = Radar(self)
        self.gun = Gun(self)
        self.base = Base(self)
        self.set_color(None)
        self.reset()

    def reset(self):
        """
        Init logical values
        :return: None
        """
        self.energy = 100
        self._speed = 0.0
        self.dead = False
        self.should_fire = False
        self.fire_power = 3
        self.commands = False
        self.moving = Move.NONE
        self.base.turning = Turn.NONE
        self.gun.turning = Turn.NONE
        self.radar.turning = Turn.NONE
        super(Robot, self).reset()

    def set_color(self, color):
        self.radar.color = color
        self.gun.color = color
        self.base.color = color

    @abstractmethod
    def do(self, tick: int):
        """To be implemented in subclasses controlling the logic of the Robot"""
        pass

    def set_position(self, center):
        self.center = center

    @property
    def position(self):
        return self.center.astype(int)

    def _add_energy(self, energy):
        self.energy += energy
        self.energy = min(self.energy, 100.0)

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

    def delta(self, tick):
        """
        Tick update:
            * Position
            * Speed
            * Rotation
        :param tick: Tick of the simulation
        :return: None
        """
        if not self.dead:
            if self.energy < 0.0:
                self.dead = True
            else:
                self.do(tick)
                self._speed = np.clip(self._speed + self.acceleration, -8.0, 8.0)
                self.center = self.center + self.velocity
                self.bearing = (self.bearing + self.get_bearing_delta()) % 360
                self.base.delta()
                self.gun.delta()
                self.radar.delta()
                if self.should_fire:
                    self.fire(self.fire_power)
                self.should_fire = False

    @property
    def velocity(self):
        return self.direction * self._speed

    def set_fire(self, firepower):
        self.should_fire = True
        self.fire_power = firepower

    def fire(self, firepower):
        if self.gun.heat == 0:
            b = Bullet(self, firepower)
            self.battle.bullets.add(b)
            b.center = self.gun.tip_location
            self.gun.heat = 1 + firepower / 5
            self.energy -= firepower
            self.should_fire = False

    @property
    def rotation_speed(self):
        return 10 - 0.75 * abs(self._speed)

    @property
    def acceleration(self):
        if self._speed > 0:
            if self.moving == Move.FORWARD:
                return 1.0
            else:
                return -2.0
        elif self._speed < 0:
            if self.moving == Move.BACK:
                return -1.0
            else:
                return 2.0
        elif self.moving is not Move.NONE:
            return 1.0
        else:
            return 0.0

    def _draw(self, surface):
        if not self.dead:
            self._group.update()
            self._group.draw(surface)
            self.radar.draw(surface)
            if self.draw_bbs:
                self.draw_rect(surface)
                self.draw_debug(surface)
        try:
            self.draw(surface)
        except NotImplementedError:
            pass

    def draw_rect(self, surface):
        r = pygame.Surface((self.rect.w, self.rect.h))  # the size of your rect
        r.set_alpha(128)  # alpha level
        r.fill((255, 0, 0))  # this fills the entire surface
        surface.blit(r, (self.rect.left, self.rect.top))

    def draw_debug(self, surface):
        """
        Draw debug graphics with bounding boxes and direction.
        :param surface: The surface upon which to draw
        :return: None
        """
        middle = (self.rect.w // 2, self.rect.h // 2)
        debug_overlay = pygame.Surface((self.rect.w, self.rect.h))
        debug_overlay.set_colorkey((0, 0, 0))
        debug_overlay.set_alpha(128)
        pygame.draw.circle(debug_overlay, (0, 0, 255), middle, self.radius)
        pygame.draw.line(debug_overlay, (255, 0, 255), middle,
                         (middle + (self.direction * 10)).astype(int), 1)
        surface.blit(debug_overlay, (self.rect.left, self.rect.top))

    def draw(self, surface):
        """ Override this method to draw any custom graphics """
        raise NotImplementedError

    def collide_bullets(self):
        """
        Collision method for testing collision of self with other robot's bullets.
        If a collision occurs a on_hit_by_bullet event is propagated.
        :return: None
        """
        events = []
        if not self.dead and len(self.battle.bullets):
            bullets = [(b, b.center, b.radius) for b in self.battle.bullets if b.robot is not self]
            if bullets:
                bs, cs, rs = zip(*bullets)
                bs, cs, rs = np.stack(bs), np.stack(cs), np.stack(rs)
                colls = test_circle_to_circles(self.center, self.radius, cs, rs)
                for bullet in bs[colls]:
                    self._add_energy(-bullet.damage)
                    bullet.robot._add_energy(3 * bullet.power)
                    self.battle.bullets.remove(bullet)
                    events.append(HitByBulletEvent(bullet))
                if not events:
                    logger.debug("%s scanned events %s." % (self, events))
                    self.on_hit_by_bullet(events)

    def collided_wall(self, battle_size):
        self.center = self.center - self.velocity
        offset = self.radius // 2 + 4
        bounds = (offset, offset), (battle_size[0] - offset, battle_size[1] - offset)
        self.center = np.clip(self.center + self.velocity, *bounds)
        self.energy -= max(abs(self._speed) * 0.5 - 1, 0)
        self._speed = 0
        self.on_hit_wall(self.velocity)

    def collide_robots(self, robots):
        if not self.dead:
            for robot in robots:
                if robot is not self:
                    if test_circle_circle(self.center, robot.center, self.radius, robot.radius):
                        self.energy -= 0.6
                        robot.energy -= 0.6
                        norm = (self.center - robot.center)
                        if np.sum(norm) == 0:
                            norm = np.array([0.0, 1.0])
                        norm = (norm / np.sum(norm ** 2)) * 15
                        self.center = self.center + norm
                        robot.center = robot.center - norm
                        self._speed = 0
                        robot._speed = 0

                        self.on_hit_robot(HitRobotEvent(robot))
                        robot.on_hit_robot(HitRobotEvent(self))
                        break

            # robot_colls = {robot: robot.rect for robot in bots}
            # robot, coll = self.rect.collidedict(robot_colls)
            # if not robot is self:

    def collide_scan(self, robots):
        scanned = []
        for robot in robots:
            if robot is not self and not robot.dead:
                scanned.append(ScannedRobotEvent(self, robot))
            # TODO change back
            #     if test_segment_circle(self.center, self.radar.scan_endpoint, robot.center, robot.radius):
            #         scanned.append(ScannedRobotEvent(self, robot))

        if scanned:
            logger.debug("%s scanned events %s." % (self, scanned))
            self.on_scanned_robot(scanned)


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


class SimpleRobot(Robot):
    """
    Subclasses Robot allowing simple chain of commands to be executed.
    """

    def delta(self, tick):
        if not self.commands:
            self.do(tick)
            self.commands = True


class SignalRobot(Robot):
    """
    API changed not sure if this is needed.
    """

    @abstractmethod
    def do(self, tick: int, action):
        """To be implemented in subclasses controlling the logic of the Robot"""
        pass

    @abstractmethod
    def get_state(self):
        """ Returns information about the current world state. """
        pass

    # def delta(self, tick, action):
    #     if self.energy < 0.0:
    #         self.destroy()
    #     else:
    #         self.do(action)
    #         self._speed = np.clip(self._speed + self.acceleration, -8.0, 8.0)
    #         self.center = self.center + self.velocity
    #         self.bearing = (self.bearing + self.get_bearing_delta()) % 360
    #         self.base.delta()
    #         self.gun.delta()
    #         self.radar.delta()
    #         if self.should_fire:
    #             self.fire(self.fire_power)
    #         self.should_fire = False

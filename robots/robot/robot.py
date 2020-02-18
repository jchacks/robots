from abc import ABC, abstractmethod

import numpy as np
import pygame
from pygame.sprite import OrderedUpdates

from robot.events import *
from robot.parts import *
from robot.utils import Move, LogicalObject, test_segment_circle, Turn


class Robot(LogicalObject, ABC):
    def __init__(self, battle, center, bearing=0.0):
        LogicalObject.__init__(self, center, bearing)
        self.name = self.__class__.__name__
        self.battle = battle
        self.center = np.array(center, np.float64)
        self.bearing = bearing
        self.radius = 36 // 2
        self.rect = pygame.Rect(0, 0, 36, 36)  # named rect for colliders
        self.rect.center = self.center
        print("rect", self.rect)
        self.dead = False
        self._speed = 0.0

        self.draw_bbs = True
        self.radar = Radar(self)
        self.gun = Gun(self)
        self.base = Base(self)

        self.should_fire = False
        self.fire_power = 3

    def on_init(self):
        self.energy = 100
        self._group = OrderedUpdates(self.base, self.gun, self.radar)
        self.commands = False
        self.left_to_move = 0.0
        self.left_to_turn = 0.0
        self.radar.on_init()
        self.gun.on_init()
        self.base.on_init()

    def _do(self):
        if not self.commands:
            self.do()
            self.commands = True

    @abstractmethod
    def do(self):
        pass

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

    def on_hit_by_bullet(self, event: HitByBulletEvent):
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

    def on_scanned_robot(self, event: ScannedRobotEvent):
        pass

    def on_skipped_turn(self, event: SkippedTurnEvent):
        pass

    def on_status(self, event: StatusEvent):
        pass

    def on_win(self, event: WinEvent):
        pass

    @property
    def moving(self):
        if self.left_to_move > 0:
            return Move.FORWARD
        elif self.left_to_move < 0:
            return Move.BACK
        else:
            return Move.NONE

    @property
    def turning(self):
        if self.left_to_turn > 0:
            return Turn.LEFT
        elif self.left_to_turn < 0:
            return Turn.RIGHT
        else:
            return Turn.NONE

    @abstractmethod
    def delta(self):
        pass

    @property
    def velocity(self):
        return self.direction * self._speed

    def destroy(self):
        self.base.clean_up()
        self._group.empty()
        self.dead = True

    def fire(self, firepower):
        self.should_fire = True
        self.fire_power = firepower

    def _fire(self, firepower):
        if self.gun.heat == 0:
            print("Firing")
            Bullet(self, firepower)
            self.gun.heat = 1 + firepower / 5
            self.energy -= firepower
            self.should_fire = False

    @property
    def rotation_speed(self):
        return (10 - 0.75 * abs(self._speed)) * float(self.turning.value)

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
        self.draw()

    def draw_rect(self, surface):
        r = pygame.Surface((self.rect.w, self.rect.h))  # the size of your rect
        r.set_alpha(128)  # alpha level
        r.fill((255, 0, 0))  # this fills the entire surface
        surface.blit(r, (self.rect.left, self.rect.top))

    def draw_debug(self, surface):
        debug_overlay = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        debug_overlay.set_alpha(125)
        pygame.draw.circle(debug_overlay, (0, 0, 255), self.center.astype(int), 2)
        pygame.draw.line(debug_overlay, (255, 0, 255), self.center.astype(int),
                         (self.center + (self.direction * 10)).astype(int), 1)
        surface.blit(debug_overlay, (self.rect.left, self.rect.top))

    def draw(self):
        pass

    def collide_bullets(self):
        events = []
        if not self.dead:
            bases_colls = {bullet: bullet.rect for bullet in Bullet.bullets}
            hits = self.rect.collidedictall(bases_colls)
            for bullet, coll in hits:
                if not bullet.robot is self:
                    self.energy -= bullet.damage
                    bullet.robot.energy += 3 * bullet.power
                    bullet.clean_up()
                    events.append(HitByBulletEvent(bullet))
        for event in events:
            self.on_hit_by_bullet(event)

    def collide_wall(self):
        if not self.dead:
            if not self.battle.rect.contains(self.rect):
                self.center += -self.velocity
                offset = max(self.rect.w // 2, self.rect.h // 2) + 4
                bounds = (offset, offset), (self.battle.size[0] - offset, self.battle.size[1] - offset)
                self.center = np.clip(self.center + self.velocity, *bounds)
                self.energy -= max(abs(self._speed) * 0.5 - 1, 0)
                self._speed = 0
                self.on_hit_wall(self.velocity)

    def collide_robots(self, robots):
        if not self.dead:
            for robot in robots:
                if robot is not self:
                    res = pygame.sprite.collide_circle(self, robot)
                    if res:
                        self.energy -= 0.6
                        robot.energy -= 0.6
                        norm = (self.center - robot.center)
                        norm = (norm / np.sum(norm ** 2)) * 10
                        self.center = self.center + norm
                        robot.center = robot.center - norm
                        self.on_hit_robot(HitRobotEvent(robot))
                        robot.on_hit_robot(HitRobotEvent(self))
                        break

            # robot_colls = {robot: robot.rect for robot in bots}
            # robot, coll = self.rect.collidedict(robot_colls)
            # if not robot is self:

    def collide_scan(self, robots):
        scanned = []
        if not self.dead:
            for robot in robots:
                if robot is not self and not robot.dead:
                    if test_segment_circle(self.center, self.radar.scan_endpoint, robot.center, robot.radius):
                        scanned.append(ScannedRobotEvent(robot))
        for scan in scanned:
            self.on_scanned_robot(scan)


class AdvancedRobot(Robot):
    def __init__(self, *args, **kwargs):
        super(AdvancedRobot, self).__init__(*args, **kwargs)

    def update_logic(self):
        if not self.dead:
            if self.energy < 0.0:
                self.destroy()
            else:
                self._do()

                self._speed = np.clip(self._speed + self.acceleration, -8.0, 8.0)
                self.left_to_move = max(0, self.left_to_move - self._speed)

                self.center = self.center + self.velocity
                self.rect.center = self.center
                self.bearing = self.get_delta_bearing(self.turning.value)
                self.left_to_turn = max(0, self.left_to_turn - self.rotation_speed)

                self.base.delta()
                self.gun.delta()
                self.radar.delta()
                if self.should_fire:
                    self._fire(self.fire_power)

        if self.moving is Move.NONE and self.turning is Turn.NONE:
            self.commands = False

    def move_forward(self, dist: float):
        self.left_to_move = dist

    def turn_left(self, angle: float):
        self.left_to_turn = angle


class SimpleRobot(Robot):
    def update_logic(self):
        pass

from pygame import sprite, display, mouse
from utils import GameObject, Turn, Move, Rotatable, LogicalObject
import numpy as np
from pygame.sprite import OrderedUpdates, RenderUpdates, Group
import pygame


class Bullet(GameObject):
    class_group = RenderUpdates()

    def __init__(self, robot, power):
        self.robot = robot
        GameObject.__init__(self, self.robot.gun.tip_location, 0.0, 'blast.png')
        self.power = power
        self.bearing = self.robot.gun.bearing
        self.speed = 20 - (3 * self.power)
        self.damage = 4 * self.power
        if self.power > 1:
            self.damage += 2 * (self.power - 1)
        self.class_group.add(self)

    @classmethod
    def draw(cls, surface):
        cls.class_group.update()
        cls.class_group.draw(surface)

    def delta(self):
        self.center = self.center + self.velocity
        if (self.center[0] < 0) or (self.center[1] < 0) or \
                (self.center[0] > self.robot.app.size[0]) or \
                (self.center[1] > self.robot.app.size[1]):
            self.clean_up()

    @property
    def velocity(self):
        return self.direction * self.speed

    def clean_up(self):
        print("Cleaning")
        self.class_group.remove(self)


class Gun(GameObject):
    def __init__(self, robot):
        GameObject.__init__(self, robot.center, robot.bearing, 'gunGrey.png')
        self.robot = robot
        self.locked = False
        self.heat = 1.0
        self.turning = Turn.NONE
        self.set_max_rotation(2)

    @property
    def tip_location(self):
        return self.center + (self.direction * 28)

    def delta(self):
        self.center = self.robot.center
        if self.locked:
            self.bearing = self.robot.bearing
        else:
            self.bearing = self.get_delta_bearing(self.turning.value)

        self.heat = max(self.heat - 0.1, 0)

    @property
    def rotation_speed(self):
        return 20


class Radar(GameObject):
    def __init__(self, robot):
        GameObject.__init__(self, robot.center, robot.bearing, 'radar.png')
        self.robot = robot
        self.locked = False
        self.turning = Turn.NONE
        self.last_bearing = robot.bearing

    def delta(self):
        self.last_bearing = self.bearing
        self.center = self.robot.center
        if self.locked:
            self.bearing = self.robot.gun.bearing
        else:
            self.bearing = self.get_delta_bearing(self.turning.value)

    @property
    def scan_endpoint(self):
        return self.center + (self.direction * 1200)

    def intersect_scan(self, rect):
        p = self.center.copy()
        for i in range(1200):
            p += self.direction
            if rect.collidepoint(p):
                return True
        else:
            return False

    @property
    def rotation_speed(self):
        return 45

    def draw(self, surface):
        rads = np.pi * self.last_bearing / 180
        last_direction = np.stack([np.sin(rads), np.cos(rads)], axis=-1)
        pygame.draw.line(surface, (0, 255, 0), self.center, self.center + (last_direction * 1200))
        pygame.draw.line(surface, (0, 255, 0), self.center, self.scan_endpoint)


class Base(GameObject):
    class_group = Group()

    def __init__(self, robot):
        GameObject.__init__(self, robot.center, robot.bearing, 'baseGrey.png')
        self.robot = robot
        self.class_group.add(self)

    def clean_up(self):
        self.class_group.remove(self)


class Robot(LogicalObject):
    def __init__(self, app, center, bearing=0.0):
        LogicalObject.__init__(self, center, bearing)
        self.app = app
        self.center = center
        self.bearing = bearing
        self.dead = False
        self._speed = 0.0

        self.radar = Radar(self)
        self.gun = Gun(self)
        self.base = Base(self)

        self.should_fire = False
        self.fire_power = 3

        self.init()

    def init(self):
        self.energy = 100
        self._group = OrderedUpdates(self.base, self.gun, self.radar)
        self.commands = False
        self.left_to_move = 0.0
        self.left_to_turn = 0.0

    def _do(self):
        if not self.commands:
            self.commands = True
            self.do()
            self.commands = False

    def do(self):
        self.move_forward(100)
        self.turn_left(100)

    def on_scanned(self, scanned):
        print(scanned)

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

    def update_logic(self):
        print(self, self.energy)
        if not self.dead:
            if self.energy < 0.0:
                self.destroy()
            else:
                self._speed = np.clip(self._speed + self.acceleration, -8.0, 8.0)
                self.center = np.clip(self.center + self.velocity, [0, 0], self.app.size)

                self.bearing = self.get_delta_bearing(self.turning.value)

                self.gun.delta()
                self.radar.delta()
                # print(self._speed, self.center, self.rotation, self.gun.rotation, self.radar.rotation)
                if self.should_fire:
                    self.fire(self.fire_power)

        if self.moving is Move.NONE and self.turning is Turn.NONE:
            self.commands = False


    @property
    def velocity(self):
        return self.direction * self._speed

    def destroy(self):
        self.base.clean_up()
        self._group.empty()
        self.dead = True

    def fire(self, firepower):
        if self.gun.heat == 0:
            print("Firing")
            Bullet(self, firepower)
            self.gun.heat = 1 + firepower / 5

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

    def move_forward(self, dist: float):
        self.left_to_move = dist

    def turn_left(self, angle: float):
        self.left_to_turn = angle

    def draw(self, surface):
        if not self.dead:
            # self.draw_rect(surface)
            # self.gun.draw_rect(surface)
            self._group.update()
            self._group.draw(surface)
            self.radar.draw(surface)

    def collide_bullets(self):
        if not self.dead:
            hits = pygame.sprite.spritecollide(self.base, Bullet.class_group, dokill=False)
            for bullet in hits:
                if not bullet.robot is self:
                    self.energy -= bullet.damage
                    bullet.robot.energy += 3 * bullet.power
                    bullet.clean_up()

    def collide_robots(self):
        if not self.dead:
            hits = pygame.sprite.spritecollide(self.base, Base.class_group, dokill=False)
            for base in hits:
                if not base is self.base:
                    self.energy -= 0.6
                    base.robot.energy -= 0.6
                    norm = (self.center - base.robot.center)
                    norm = (norm / np.sum(norm ** 2)) * 10
                    self.center = self.center + norm
                    base.robot.center = base.robot.center - norm

    def collide_scan(self, robots):
        scanned = []
        if not self.dead:
            for robot in robots:
                if robot is not self:
                    if self.radar.intersect_scan(robot.base.rect):
                        scanned.append(robot)
        self.on_scanned(scanned)


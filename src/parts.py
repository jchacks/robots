from abc import ABC

from utils import GameObject, Turn
import numpy as np
import numpy as np
import pygame
from pygame.sprite import RenderUpdates, Group

from utils import GameObject, Turn


class Bullet(GameObject, ABC):
    class_group = RenderUpdates()

    def __init__(self, robot, power):
        self.robot = robot
        GameObject.__init__(self, self.robot.gun.tip_location, 0.0, 'blast.png', scale_factor=power / 3)
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

    @classmethod
    def collide_bullets(cls):
        group = cls.class_group.copy()
        for bullet in group:
            group.remove(bullet)
            other_bullet = pygame.sprite.spritecollideany(bullet, group)
            if other_bullet is not None:
                cls.class_group.remove(bullet)
                cls.class_group.remove(other_bullet)


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
        self.coll = self.rect.copy()
        self.coll.inflate_ip(-2, -2)
        self.robot = robot
        self.class_group.add(self)

    def clean_up(self):
        self.class_group.remove(self)

    def delta(self):
        self.coll.center = self.robot.center
        self.center = self.robot.center
        self.bearing = self.robot.bearing

    def draw_rect(self, surface):
        r = pygame.Surface((self.coll.w, self.coll.h))  # the size of your rect
        r.set_alpha(128)  # alpha level
        r.fill((255, 0, 0))  # this fills the entire surface
        surface.blit(r, (self.coll.left, self.coll.top))

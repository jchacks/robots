import numpy as np
import pygame
from pygame.sprite import Group

from robot.utils import LogicalObject, GameObject, Turn, load_image, scale_image, Colors

__all__ = ['Bullet', 'Radar', 'Gun', 'Base', ]


class Bullet(LogicalObject):
    bullets = set()
    draw_trajectory = True
    _image, _rect = None, None

    def __init__(self, robot, power):
        LogicalObject.__init__(self, robot.gun.tip_location, robot.gun.bearing)
        self.robot = robot
        self.power = power
        self.image, self.rect = scale_image(self._image, self._rect, self.power / 3)
        self.rect.center = self.center
        self.speed = 20 - (3 * self.power)
        self.damage = 4 * self.power
        if self.power > 1:
            self.damage += 2 * (self.power - 1)
        self.bullets.add(self)

    @classmethod
    def on_init(cls):
        cls._image, cls._rect = load_image('blast.png', -1)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
        if self.draw_trajectory:
            pygame.draw.line(surface, Colors.Y, self.center, self.center + self.direction * 1000)

    @property
    def rotation_speed(self):
        return 0

    def delta(self, tick):
        self.center += self.velocity
        self.rect.center = self.center
        if (self.center[0] < 0) or (self.center[1] < 0) or \
                (self.center[0] > self.robot.battle.size[0]) or \
                (self.center[1] > self.robot.battle.size[1]):
            self.clean_up()

    @property
    def velocity(self):
        return self.direction * self.speed

    def clean_up(self):
        self.bullets.remove(self)

    @classmethod
    def collide_bullets(cls):
        to_remove = set()
        for bullet in cls.bullets:
            group = cls.bullets.copy()
            group.remove(bullet)
            other_bullet = pygame.sprite.spritecollideany(bullet, group)
            if other_bullet is not None:
                to_remove.add(bullet)
                to_remove.add(other_bullet)
        cls.bullets.difference_update(to_remove)


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
        c = self.center.copy()
        for i in range(10, 1200, 3):
            p = c + (i * self.direction)
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

    def on_init(self):
        super(Base, self).on_init()
        self.class_group.add(self)

    def clean_up(self):
        self.class_group.remove(self)

    def delta(self):
        super(Base, self).delta()
        self.center = self.robot.center  # TODO propagate these changes down instead of fetching them
        self.bearing = self.robot.bearing

    @property
    def rotation_speed(self):
        return 0

    def draw_rect(self, surface):
        r = pygame.Surface((self.rect.w, self.rect.h))  # the size of your rect
        r.set_alpha(128)  # alpha level
        r.fill((255, 0, 0))  # this fills the entire surface
        surface.blit(r, (self.rect.left, self.rect.top))

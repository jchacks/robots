import os

import numpy as np
import pygame

from robots.robot.utils import LogicalObject, GameObject, load_image, scale_image, Colors, test_circles

__all__ = ['Bullet', 'Radar', 'Gun', 'Base', ]
data_dir = os.path.join(os.path.dirname(__file__), '../../data/')


class Bullet(LogicalObject):
    # bullet_positions = Vector()
    # bullet_velocities = Vector()
    draw_trajectory = True
    _image, _rect = None, None

    def __init__(self, battle, robot, power):
        LogicalObject.__init__(self, robot.gun.bearing, (10, 10))
        self.battle = battle
        self.robot = robot
        self.power = power
        self.radius = 5 * self.power / 3
        self.image, self.rect = scale_image(self._image, self._rect, self.power / 3)
        self.speed = 20 - (3 * self.power)
        self.damage = 4 * self.power
        if self.power > 1:
            self.damage += 2 * (self.power - 1)
        self.battle.bullets.add(self)

    @classmethod
    def init_video(cls):
        cls._image, cls._rect = load_image(data_dir + 'blast.png', -1)

    def draw(self, surface):
        if self.draw_trajectory:
            pygame.draw.line(surface, Colors.Y, self.center, self.center + self.direction * 1000)
        surface.blit(self.image, self.center - self.radius)

    @property
    def rotation_speed(self):
        return 0

    def delta(self, tick):
        self.center += self.velocity

    @property
    def velocity(self):
        return self.direction * self.speed

    def clean_up(self):
        self.battle.bullets.remove(self)



class Gun(GameObject):
    def __init__(self, robot):
        GameObject.__init__(self, robot.bearing, data_dir + 'gunGrey.png')
        self.robot = robot
        self.locked = False
        self.heat = 1.0
        self.set_max_rotation(2)

    def on_init(self):
        super(Gun, self).on_init()
        self.center = self.robot.center

    @property
    def tip_location(self):
        return self.center + (self.direction * 28)

    def delta(self):
        self.center = self.robot.center
        if self.locked:
            self.bearing = self.robot.bearing
        else:
            self.bearing = (self.bearing + self.get_bearing_delta() + self.robot.get_bearing_delta()) % 360

        self.heat = max(self.heat - 0.1, 0)

    @property
    def rotation_speed(self):
        return 20


class Radar(GameObject):
    def __init__(self, robot):
        GameObject.__init__(self, robot.bearing, data_dir + 'radar.png')
        self.robot = robot
        self.locked = False
        self.last_bearing = robot.bearing

    def on_init(self):
        GameObject.on_init(self)
        self.center = self.robot.center

    def delta(self):
        self.last_bearing = self.bearing
        self.center = self.robot.center
        if self.locked:
            self.bearing = self.robot.gun.bearing
        else:
            self.bearing = (self.bearing + self.get_bearing_delta() + + self.robot.get_bearing_delta() + + self.robot.gun.get_bearing_delta()) % 360

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
        return 5  # 45

    def draw(self, surface):
        rads = np.pi * self.last_bearing / 180
        last_direction = np.stack([np.sin(rads), np.cos(rads)], axis=-1)
        pygame.draw.line(surface, (0, 128, 0), self.center, self.center + (last_direction * 1200))
        pygame.draw.line(surface, (0, 255, 0), self.center, self.scan_endpoint)


class Base(GameObject):
    def __init__(self, robot):
        GameObject.__init__(self, robot.bearing, data_dir + 'baseGrey.png')
        self.robot = robot

    def on_init(self):
        super(Base, self).on_init()
        self.center = self.robot.center

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

import pygame
import os
from pygame.locals import *
from pygame.sprite import Sprite
import numpy as np
from enum import Enum
from abc import ABC


class Turn(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = -1


class Move(Enum):
    NONE = 0
    FORWARD = 1
    BACK = -1


class Colors(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    TURQ = (0, 255, 255)


def rot_center(image, rect, angle):
    """rotate an image while keeping its center"""
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect


def scale_image(image, rect, factor):
    """rotate an image while keeping its center"""
    size = image.get_size()
    scale_image = pygame.transform.scale(image, (round(size[0] * factor), round(size[1] * factor)))
    scale_rect = scale_image.get_rect(center=rect.center)
    return scale_image, scale_rect


def test_segment_circle(start, stop, center, radius):
    ax, ay = start
    bx, by = stop
    cx, cy = center
    ax -= cx
    ay -= cy
    bx -= cx
    by -= cy
    a = (bx - ax) ** 2 + (by - ay) ** 2
    b = 2 * (ax * (bx - ax) + ay * (by - ay))
    c = ax ** 2 + ay ** 2 - radius ** 2
    disc = b ** 2 - 4 * a * c
    if disc <= 0:
        return False
    sqrtdisc = np.sqrt(disc)
    t1 = (-b + sqrtdisc) / (2 * a)
    t2 = (-b - sqrtdisc) / (2 * a)
    if ((0 < t1) and (t1 < 1)) or ((0 < t2) and (t2 < 1)):
        return True
    return False


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()


class Rotatable(ABC):
    def __init__(self, bearing):
        self.bearing = bearing
        self._max_rotation = None

    def set_max_rotation(self, rot):
        self._max_rotation = rot

    def get_delta_bearing(self, direction: float):
        rotation_speed = self.rotation_speed
        if self._max_rotation:
            rotation_speed = min(self._max_rotation, rotation_speed)
        return self.bearing + (rotation_speed * float(direction)) % 360

    @property
    def rotation_speed(self):
        raise NotImplementedError


class LogicalObject(Rotatable):
    def __init__(self, center, bearing):
        Rotatable.__init__(self, bearing)
        self.center = np.array(center, dtype=np.float64)

    @property
    def direction(self):
        rads = np.pi * self.bearing / 180
        return np.stack([np.sin(rads), np.cos(rads)], axis=-1)

    def delta(self):
        raise NotImplementedError


class GameObject(Sprite, LogicalObject):
    def __init__(self, center: tuple, bearing: float, filename, scale_factor=None):
        Sprite.__init__(self)
        LogicalObject.__init__(self, center, bearing)
        self.scale_factor = scale_factor
        self.filename = filename

        # colorImage = pygame.Surface(self.image.get_size()).convert_alpha()
        # colorImage.fill((0, 0, 255))
        # self.image.blit(colorImage, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def on_init(self):
        self.image, self.rect = load_image(self.filename, -1)
        if self.scale_factor:
            self.image, self.rect = scale_image(self.image, self.rect, self.scale_factor)
        self.rect.center = self.center
        self.orig_image = self.image

    def draw_rect(self, surface):
        r = pygame.Surface((self.rect.w, self.rect.h))
        r.set_alpha(128)
        r.fill((255, 0, 0))
        surface.blit(r, (self.rect.left, self.rect.top))

    def update(self, *args):
        self.image, self.rect = rot_center(self.orig_image, self.rect, self.bearing)
        self.rect.center = self.center  # visual update rect

    def delta(self):
        pass

    def draw(self, surface):
        pass

import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Union

import numba as nb
import numpy as np
import pygame
from pygame.locals import *
from pygame.sprite import Sprite

__all__ = [
    'Turn', 'Move', 'Colors', 'rot_center', 'scale_image',
    'load_image', 'test_segment_circle',
    'Rotatable', 'LogicalObject', 'GameObject'
]


class Turn(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = -1


class Move(Enum):
    NONE = 0
    FORWARD = 1
    BACK = -1


class Colors(object):
    RED = R = (255, 0, 0)
    GREEN = G = (0, 255, 0)
    BLUE = B = (0, 0, 255)
    BLACK = K = (0, 0, 0)
    WHITE = W = (255, 255, 255)
    CYAN = C = (0, 255, 255)
    MAGENTA = M = (255, 0, 255)
    YELLOW = Y = (255, 255, 0)
    ORANGE = O = (255, 128, 0)
    LIME = L = (128, 255, 0)


def rot_center(image, rect, angle):
    """rotate an image while keeping its center"""
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect


def scale_image(image, rect, factor):
    """rotate an image while keeping its center"""
    size = image.get_size()
    scale_image = pygame.transform.scale(image, (int(round(size[0] * factor)), int(round(size[1] * factor))))
    scale_rect = scale_image.get_rect(center=rect.center)
    return scale_image, scale_rect


@nb.njit
def test_segment_circle(start, stop, center, radius):
    start = start - center
    stop = stop - center
    a = np.sum((stop - start) ** 2)
    b = 2 * np.sum(start * (stop - start))
    c = np.sum(start ** 2) - radius ** 2
    disc = b ** 2 - 4 * a * c
    if disc <= 0:
        return False
    sqrtdisc = np.sqrt(disc)
    t1 = (-b + sqrtdisc) / (2 * a)
    t2 = (-b - sqrtdisc) / (2 * a)
    if ((0 < t1) and (t1 < 1)) or ((0 < t2) and (t2 < 1)):
        return True
    return False


@nb.njit
def test_circle_circle(c1, c2, r1, r2):
    return np.sum((c1 - c2) ** 2) <= (r1 + r2) ** 2


@nb.njit
def test_circles(cs, rs):
    distances = np.sum((np.expand_dims(cs, 1) - np.expand_dims(cs, 0)) ** 2, axis=2)
    radius_diffs = (np.expand_dims(rs, 1) - np.expand_dims(rs, 0)) ** 2
    bool_in = (distances <= radius_diffs)
    return bool_in ^ np.identity(len(cs), nb.bool_)


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
        self.turning = Turn.NONE

    def on_init(self):
        self.turning = Turn.NONE

    def set_bearing(self, angle):
        self.bearing = angle

    def set_max_rotation(self, rot):
        self._max_rotation = rot

    def get_bearing_delta(self):
        rotation_speed = self.rotation_speed
        if self._max_rotation:
            rotation_speed = min(self._max_rotation, rotation_speed)
        return self.bearing + (rotation_speed * self.turning.value) % 360

    def set_rotation(self, direction: Union[float, Turn]):
        self.turning = direction

    @property
    @abstractmethod
    def rotation_speed(self):
        raise NotImplementedError


class LogicalObject(Rotatable, ABC):
    def __init__(self, bearing, dimensions=None):
        Rotatable.__init__(self, bearing)
        self._dimensions = dimensions
        self._center = np.array((np.nan, np.nan), dtype=np.float64)
        if self._dimensions:
            self.rect = pygame.Rect(0, 0, *self._dimensions)

    def on_init(self):
        Rotatable.on_init(self)

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, center):
        self._center[:] = center
        self.rect.center = center

    @property
    def direction(self):
        rads = np.pi * self.bearing / 180
        return np.stack([np.sin(rads), np.cos(rads)], axis=-1)

    @abstractmethod
    def delta(self, tick):
        raise NotImplementedError


class GameObject(Sprite, LogicalObject):
    def __init__(self, bearing: float, filename, scale_factor=None):
        Sprite.__init__(self)
        LogicalObject.__init__(self, bearing)
        self.scale_factor = scale_factor
        self.filename = filename

        # colorImage = pygame.Surface(self.image.get_size()).convert_alpha()
        # colorImage.fill((0, 0, 255))
        # self.image.blit(colorImage, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def on_init(self):
        self.image, self.rect = load_image(self.filename, -1)
        print(self, self.rect)
        LogicalObject.on_init(self)
        if self.scale_factor:
            self.image, self.rect = scale_image(self.image, self.rect, self.scale_factor)
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

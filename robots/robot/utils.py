from collections import deque
from enum import Enum

import numba as nb
import numpy as np
import os
import pygame
import time
from abc import ABC, abstractmethod
from pygame.sprite import Sprite
from typing import Union

__all__ = [
    "Turn",
    "Move",
    "Colors",
    "rot_center",
    "scale_image",
    "load_image",
    "test_segment_circle",
    "test_circle_to_circles",
    "Rotatable",
    "LogicalObject",
    "GameObject",
    "Simable",
    "test_circles",
]


class Vector(object):
    def __init__(
        self,
        item_shape,
        initial_size=10,
        dtype="float32",
        mask=None,
    ):
        if mask is True:
            self.initial_size = initial_size
            self._mask = np.zeros(initial_size, dtype="bool")
        else:
            self._mask = mask
            self.initial_size = mask.shape[0]

        self.item_shape = item_shape
        self.dtype = dtype
        self._data = np.zeros((initial_size, *item_shape), dtype=self.dtype)

    @property
    def data(self):
        return self._data[self._mask]

    @data.setter
    def data(self, new_data):
        self._data[self._mask] = new_data

    def append(self, item):
        if not (~self._mask).any():
            self._mask = np.concatenate([self._mask, np.zeros(self.initial_size, dtype="bool")])
            self._data = np.concatenate([self._data, np.zeros((self.initial_size, *self.item_shape), dtype=self.dtype)])
        pos = np.argmin(self._mask)
        self._data[pos] = item
        self._mask[pos] = True
        return pos

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        self._mask[key] = False

    def __mul__(self, other):
        return self.data * other

    def __add__(self, other):
        return self.data + other

    def __truediv__(self, other):
        return self.data / other


class Turn(Enum):
    NONE = 0
    LEFT = -1
    RIGHT = 1


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
    """
    Test the collision of a line segment with a circle
    :param start: start of line segment (x,y)
    :param stop: stop of line segment (x,y)
    :param center:
    :param radius:
    :return:
    """
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
    """
    Test the collision of two circles
    :param c1: Numpy Array (2,) center of circle1
    :param c2: Numpy Array (2,) center of circle2
    :param r1: radius of circle1
    :param r2: radius of circle2
    :return: Boolean value of the test
    """
    return np.sum((c1 - c2) ** 2) <= (r1 + r2) ** 2


@nb.njit
def test_circles(cs, rs):
    """
    Test collision of all circles against each other.
    :param cs: Numpy Array (n,2) of circle centers
    :param rs: Numpy Array (n,) of circle radii
    :return:
    """
    distances = np.sum((np.expand_dims(cs, 1) - np.expand_dims(cs, 0)) ** 2, axis=2)
    radius_diffs = (np.expand_dims(rs, 1) + np.expand_dims(rs, 0)) ** 2
    bool_in = distances <= radius_diffs
    return bool_in ^ np.identity(len(cs), nb.bool_)


@nb.njit
def test_circle_to_circles(c, r, cs, rs):
    """
    Test collision of a 'single' circle to multiple 'other' circles.
    :param c: Center of single circle
    :param r: Radius of single circle
    :param cs: Numpy Array (n,2) of other circles centers
    :param rs: Numpy Array (n,) of other circles radii
    :return: Boolean Array of collisions
    """
    distances = np.sum((c - cs) ** 2, axis=1)
    radius_diffs = (r + rs) ** 2
    return distances <= radius_diffs


def load_image(name):
    """
    Load an image for pygame
    :param name: Filename in data folder
    :param colorkey: Colorkey value
    :return: (image, rectangle)
    """
    fullname = os.path.join("data", name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print("Cannot load image:", name)
        raise SystemExit(message)
    return image, image.get_rect()


class Rotatable(ABC):
    def __init__(self, bearing):
        self.bearing = bearing
        self._max_rotation = None

    def reset(self):
        self.turning = Turn.NONE

    def set_bearing(self, angle):
        self.bearing = angle

    def set_max_rotation(self, rot):
        self._max_rotation = rot

    def get_bearing_delta(self):
        rotation_speed = self.rotation_speed
        if self._max_rotation:
            rotation_speed = min(self._max_rotation, rotation_speed)
        return rotation_speed * self.turning.value

    def set_rotation(self, direction: Union[float, Turn]):
        self.turning = direction

    @property
    def direction(self):
        rads = np.pi * self.bearing / 180
        return np.stack([np.sin(rads), np.cos(rads)], axis=-1)

    @abstractmethod
    def delta(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def rotation_speed(self):
        raise NotImplementedError


class LogicalObject(Rotatable, ABC):
    """
    Abstract class that has all attributes necessary for movement, rotation and collision
    """

    def __init__(self, bearing, dimensions=None):
        Rotatable.__init__(self, bearing)
        self._dimensions = dimensions
        self._center = np.array((np.nan, np.nan), dtype=np.float64)

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, center):
        self._center[:] = center

    @abstractmethod
    def delta(self):
        raise NotImplementedError


class Simable(object):
    def __init__(self):
        self.tick = 0
        self.last_sim = 0
        self.is_finished = False
        self.sim_rate = -1
        self.sim_interval = 1.0 / self.sim_rate
        self.simulate = True
        self.sim_times = deque(maxlen=1000)

    def set_sim_rate(self, r):
        self.sim_rate = int(r)
        self.sim_interval = 1.0 / self.sim_rate

    def get_sim_times(self):
        if len(self.sim_times) > 0:
            return sum(self.sim_times) / len(self.sim_times)
        else:
            return -1

    @abstractmethod
    def step(self):
        pass

    def on_loop(self):
        """
        Simulation function that limits simulation rate.
        :return:
        """
        s = time.time()
        if ((s - self.last_sim) >= self.sim_interval) and self.simulate:
            self.tick += 1
            start_step = time.time()
            self.step()
            self.sim_times.append(time.time() - start_step)
            self.last_sim = s


class GroupedLogicalObject(object):
    centers = Vector((2,), mask=True)
    bearings = Vector((1,), mask=centers._mask)
    speeds = Vector((1,), mask=centers._mask)

    def __init__(self, center, speed, bearing):
        self._center = self.centers.append(*center)
        self._speed = self.speeds.append(speed)
        self._bearing = self.bearings.append(bearing)

    @classmethod
    def directions(cls):
        rads = np.pi * cls.bearings / 180
        return np.stack([np.sin(rads), np.cos(rads)], axis=-1)

    @classmethod
    def delta(cls, tick):
        cls.centers.data = cls.centers + (cls.speeds * cls.directions())


class GameObject(Sprite):
    def __init__(self, filename, scale_factor=None):
        Sprite.__init__(self)
        self.scale_factor = scale_factor
        self.filename = filename
        self.color = None
        self.image = None
        self.rect = None

    def init_video(self):
        self.image, self.rect = load_image(self.filename)

        if isinstance(self.color, str):
            self.color = pygame.Color(self.color)
        elif isinstance(self.color, tuple):
            self.color = pygame.Color(*self.color)
        else:
            self.color = None

        if self.color:
            grey = self.image.convert()
            grey.set_colorkey((0, 255, 255))  # Image color key

            base_color = pygame.Surface(self.image.get_size()).convert_alpha()
            base_color.fill(self.color)

            mask = pygame.Surface(self.image.get_size()).convert_alpha()
            mask.fill((255, 255, 255, 0))
            mask.blit(self.image, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            base_color.blit(grey, (0, 0))
            base_color.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.image = base_color
        else:
            self.image = self.image.convert_alpha()

        if self.scale_factor:
            self.image, self.rect = scale_image(self.image, self.rect, self.scale_factor)
        self.orig_image = self.image

    def draw_rect(self, surface):
        r = pygame.Surface((self.rect.w, self.rect.h))
        r.set_alpha(128)
        r.fill((255, 0, 0))
        surface.blit(r, (self.rect.left, self.rect.top))

    def update(self, center, bearing=None):
        if bearing and bearing != 0.0:
            self.image, self.rect = rot_center(self.orig_image, self.rect, bearing)
        self.rect.center = center  # visual update rect

    def delta(self):
        pass

    def draw(self, surface):
        pass

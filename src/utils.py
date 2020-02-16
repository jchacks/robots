import pygame
import os
from pygame.locals import *
from pygame.sprite import Sprite
import numpy as np
from enum import Enum


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


class Rotatable:
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


class GameObject(Sprite, LogicalObject):
    def __init__(self, center: tuple, bearing: float, image):
        Sprite.__init__(self)
        LogicalObject.__init__(self, center, bearing)
        self.image, self.rect = load_image(image, -1)

        # colorImage = pygame.Surface(self.image.get_size()).convert_alpha()
        # colorImage.fill((0, 0, 255))
        # self.image.blit(colorImage, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.orig_image = self.image

    def draw_rect(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), self.rect)

    def update(self, *args):
        self.image, self.rect = rot_center(self.orig_image, self.rect, self.bearing)
        self.rect.center = self.center

    def draw(self, surface):
        pass

import pygame
import os
import math


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


def rot_center(image, rect, rads):
    """rotate an image while keeping its center"""
    rot_image = pygame.transform.rotate(image, -rads * 180 / math.pi)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image, rot_rect


def scale_image(image, rect, factor):
    """rotate an image while keeping its center"""
    size = image.get_size()
    scale_image = pygame.transform.scale(
        image, (int(round(size[0] * factor)), int(round(size[1] * factor)))
    )
    scale_rect = scale_image.get_rect(center=rect.center)
    return scale_image, scale_rect

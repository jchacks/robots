import numpy as np
import os
import pygame
from abc import abstractmethod
import math
from robots.ui.utils import load_image, Colors, rot_center

data_dir = os.path.join(os.path.dirname(__file__), "../../data/")


class Renderer(object):
    """
    Tracking objects for rendering specific types of Entities
    """

    def __init__(self):
        self.items = set()
        self.orig_sprites = dict()
        self.scale_factor = None

    def track(self, item, sprites=None):
        self.items.add(item)
        if sprites:
            self.orig_sprites[item] = sprites

    def untrack(self, item):
        self.items.remove(item)
        try:
            del self.orig_sprites[item]
        except KeyError:
            pass

    @abstractmethod
    def render(self, surface):
        pass


class BulletRenderer(Renderer):
    def __init__(self, draw_trajectories=True):
        super(BulletRenderer, self).__init__()
        self.draw_trajectories = draw_trajectories

    def render(self, surface):
        for item in self.items.copy():
            try:
                # if self.draw_trajectories:
                #     pygame.draw.line(surface, Colors.Y, item.position, item.position + item.velocity * 1000)
                pygame.draw.circle(surface, (255, 0, 0), item.position, 3, 0)
            except Exception as e:
                print(f"Error {e}, for bullet {item}")


def change_image_color(image, color):
    if isinstance(color, str):
        color = pygame.Color(color)
    elif isinstance(color, tuple):
        color = pygame.Color(*color)
    else:
        color = None

    if color:
        grey = image.convert()
        grey.set_colorkey((0, 162, 232))  # Image color key

        base_color = pygame.Surface(image.get_size()).convert_alpha()
        base_color.fill(color)

        mask = pygame.Surface(image.get_size()).convert_alpha()
        mask.fill((255, 255, 255, 0))
        mask.blit(image, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        base_color.blit(grey, (0, 0))
        base_color.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        image = base_color
    else:
        image = image.convert_alpha()

    return image


def draw_rect(surface, rect, color=(255, 0, 0), alpha=255):
    r = pygame.Surface((rect.w, rect.h))  # the size of your rect
    r.set_alpha(alpha)  # alpha level
    r.fill(color)  # this fills the entire surface
    surface.blit(r, (rect.left, rect.top))


def draw_robot_debug(surface, robot):
    """
    Draw debug graphics with bounding boxes and direction.
    :param surface: The surface upon which to draw
    :return: None
    """
    middle = (robot.rect.w // 2, robot.rect.h // 2)
    debug_overlay = pygame.Surface((robot.rect.w, robot.rect.h))
    debug_overlay.set_colorkey((0, 0, 0))
    debug_overlay.set_alpha(128)
    pygame.draw.circle(debug_overlay, (0, 0, 255), middle, robot.radius)
    pygame.draw.line(
        debug_overlay,
        (255, 0, 255),
        middle,
        (middle + (robot.direction * 10)).astype(int),
        1,
    )
    surface.blit(debug_overlay, (robot.rect.left, robot.rect.top))


class RobotRenderer(Renderer):
    def __init__(self):
        super(RobotRenderer, self).__init__()
        image, rect = load_image(data_dir + "radar.png")
        image = image.convert_alpha()
        image.set_colorkey(image.get_at((0, 0)), pygame.RLEACCEL)
        image = image.convert_alpha()
        self._radar = image, rect

        image, rect = load_image(data_dir + "gun.png")
        image = image.convert()
        image.set_colorkey(image.get_at((0, 0)), pygame.RLEACCEL)
        image = image.convert_alpha()
        self._gun = image, rect

        image, rect = load_image(data_dir + "base.png")
        image = image.convert_alpha()
        image.set_colorkey(image.get_at((0, 0)), pygame.RLEACCEL)
        image = image.convert_alpha()
        self._base = image, rect

    def track(self, item):
        radar = change_image_color(self._radar[0], item.radar_color), self._radar[1]
        gun = change_image_color(self._gun[0], item.turret_color), self._radar[1]
        base = change_image_color(self._base[0], item.base_color), self._radar[1]
        self.orig_sprites[item] = (radar, gun, base)
        super(RobotRenderer, self).track(item)

    def render(self, surface):
        for robot in self.items:
            self.draw_base(surface, robot)
            self.draw_gun(surface, robot)
            self.draw_radar(surface, robot)

    def draw_radar(self, surface, robot):
        rads = robot.radar_rotation 
        image, rect = self.orig_sprites[robot][0]
        image, rect = rot_center(image, rect, rads - (math.pi / 2))
        rect.center = robot.position
        surface.blit(image, rect)
        direction = np.array([np.cos(rads), np.sin(rads)])
        endpoint = robot.position + (direction * 1200)
        pygame.draw.line(surface, (0, 255, 0), robot.position, endpoint)

    def draw_gun(self, surface, robot):
        image, rect = self.orig_sprites[robot][1]
        image, rect = rot_center(image, rect, robot.turret_rotation - (math.pi / 2))
        rect.center = robot.position
        surface.blit(image, rect)

    def draw_base(self, surface, robot):
        image, rect = self.orig_sprites[robot][2]
        image, rect = rot_center(image, rect, robot.base_rotation - (math.pi / 2))
        rect.center = robot.position
        surface.blit(image, rect)

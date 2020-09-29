import numpy as np
import os
import pygame
from abc import abstractmethod

from robots.robot.utils import load_image, Colors, rot_center

data_dir = os.path.join(os.path.dirname(__file__), "../data/")


class Renderer(object):
    """
    Tracking objects for rendering specific types of Entities
    """

    def __init__(self):
        self.items = set()
        self.orig_sprites = dict()
        self.curr_sprites = dict()
        self.scale_factor = None

    def track(self, item):
        self.items.add(item)

    def untrack(self, item):
        self.items.remove(item)
        try:
            del self.orig_sprites[item]
            del self.curr_sprites[item]
        except KeyError:
            pass

    @abstractmethod
    def render(self, surface):
        pass


class BulletRenderer(Renderer):
    def __init__(self):
        super(BulletRenderer, self).__init__()
        self.draw_trajectories = True
        # self._image, self._rect = load_image(data_dir + "blast.png")
        # self._image = self._image.convert()
        # self._image.set_colorkey(self._image.get_at((0, 0)), pygame.RLEACCEL)

    def render(self, surface):
        for item in self.items.copy():
            try:
                if self.draw_trajectories:
                    pygame.draw.line(surface, Colors.Y, item.center, item.center + item.direction * 1000)
                    pygame.draw.circle(surface, item.color, item.int_center, 3, 0)
                # surface.blit(self._image, item.center - item.radius)
            except Exception as e:
                print(f"Error {e}, for bullet {item}")


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

    def change_color(self, image, color):
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

    def draw_rect(self, surface, robot):
        r = pygame.Surface((robot.rect.w, robot.rect.h))  # the size of your rect
        r.set_alpha(128)  # alpha level
        r.fill((255, 0, 0))  # this fills the entire surface
        surface.blit(r, (robot.rect.left, robot.rect.top))

    def draw_debug(self, surface, robot):
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
        pygame.draw.line(debug_overlay, (255, 0, 255), middle, (middle + (robot.direction * 10)).astype(int), 1)
        surface.blit(debug_overlay, (robot.rect.left, robot.rect.top))

    def track(self, item):
        radar = self.change_color(self._radar[0], item.radar.color), self._radar[1]
        gun = self.change_color(self._gun[0], item.gun.color), self._radar[1]
        base = self.change_color(self._base[0], item.base.color), self._radar[1]
        self.orig_sprites[item] = (radar, gun, base)
        super(RobotRenderer, self).track(item)

    def render(self, surface):
        for robot in self.items:
            self.draw_base(surface, robot)
            self.draw_gun(surface, robot)
            self.draw_radar(surface, robot)

    def draw_radar(self, surface, robot):
        radar = robot.radar
        image, rect = self.orig_sprites[robot][0]
        image, rect = rot_center(image, rect, radar.bearing)
        rect.center = robot.center
        surface.blit(image, rect)

        rads = np.pi * radar.last_bearing / 180
        last_direction = np.stack([np.sin(rads), np.cos(rads)], axis=-1)
        pygame.draw.line(surface, (0, 128, 0), robot.center, robot.center + (last_direction * 1200))
        pygame.draw.line(surface, (0, 255, 0), robot.center, radar.scan_endpoint)

    def draw_gun(self, surface, robot):
        image, rect = self.orig_sprites[robot][1]
        image, rect = rot_center(image, rect, robot.gun.bearing)
        rect.center = robot.center
        surface.blit(image, rect)

    def draw_base(self, surface, robot):
        image, rect = self.orig_sprites[robot][2]
        image, rect = rot_center(image, rect, robot.bearing)
        rect.center = robot.center
        surface.blit(image, rect)

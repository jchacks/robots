import os
from abc import abstractmethod

import pygame
import pygame.locals as pl

__all__ = ['Overlay', 'Console']


class Overlay(object):
    def __init__(self, size, battle):
        self._robots = battle.robots
        w, h = size
        self.bar_dims = (100, 4)
        self.bar_dims = min(100, int(w * 100 / 400)), min(4, int(h * 4 / 400))
        if pygame.font:
            self.font_size = 36
            self.font_size = min(36, int(h * 36 / 400))
            self.font = pygame.font.Font(None, self.font_size)

    def set_battle(self, battle):
        self._robots = battle.robots

    def on_resize(self, size):
        w, h = size
        self.bar_dims = min(100, int(w * 100 / 400)), min(4, int(h * 4 / 400))
        self.font_size = min(36, int(h * 36 / 400))
        self.font = pygame.font.Font(None, self.font_size)

    def on_render(self, screen):
        offset = 0
        for robot in self._robots:
            offset = self.draw(screen, robot, offset)

    def draw(self, screen, robot, offset):
        text = self.font.render(str(robot.__class__.__name__), 1, (255, 255, 255))
        textpos = text.get_rect(left=0, top=offset)
        screen.blit(text, textpos)

        backgr = pygame.Surface(self.bar_dims)
        backgr.fill((255, 0, 0))
        if robot.energy > 0:
            energy = pygame.Surface((robot.energy * self.bar_dims[0] / 100, 2))
            energy.fill((0, 255, 0))
            backgr.blit(energy, (0, 1))

        backgrpos = backgr.get_rect(left=0, top=textpos.bottom + 2)
        screen.blit(backgr, backgrpos)
        return backgrpos.bottom + 5


class Console(object):
    def __init__(self, font_family=None, font_size=20):
        self.active = False
        self.font_size = font_size
        self.font_family = font_family
        self.buffer = "PyRoboCode console: v1.0\nType 'help' for detailed commands..."
        self.input = ""
        self.cursor_pos = 0
        self.commands = {}
        self.help = {}

    def on_init(self, screen):
        if self.font_family is not None and not os.path.isfile(self.font_family):
            self.font_family = pygame.font.match_font(self.font_family)
            print(self.font_family)

        self.font_object = pygame.font.Font(self.font_family, self.font_size)

        self.surface = pygame.Surface(screen.get_size())
        self.surface.convert()
        self.surface.set_alpha(128)

        self.bg = pygame.Surface(screen.get_size())
        self.bg = self.bg.convert()
        pygame.draw.rect(self.bg, (255, 0, 0), self.bg.get_rect(), 1)
        self.surface.blit(self.bg, (0, 0))

    def put_text(self, text):
        self.buffer = self.buffer + '\n' + text

    def on_resize(self, size):
        pass

    def on_render(self, screen):
        if self.active:
            self.surface.blit(self.bg, (0, 0))
            lines = self.buffer.split('\n')
            lines.append('> ' + self.input)
            for i, line in enumerate(lines[::-1]):
                text = self.font_object.render(line, True, (255, 255, 255))
                textpos = text.get_rect(left=0, bottom=self.surface.get_height() - i * (self.font_size + 2))
                self.surface.blit(text, textpos)
            screen.blit(self.surface, self.surface.get_bounding_rect())

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pl.K_ESCAPE:
                self.active = False
            # self.cursor_visible = True  # So the user sees where he writes
            elif event.key == pl.K_BACKSPACE:
                self.input = self.input[:max(self.cursor_pos - 1, 0)] + self.input[self.cursor_pos:]
                self.cursor_pos = max(self.cursor_pos - 1, 0)
            elif event.key == pl.K_DELETE:
                self.input = self.input[:self.cursor_pos] + self.input[self.cursor_pos + 1:]
            elif event.key == pl.K_RETURN:
                command, self.input = self.input, ""
                if len(command) > 0:
                    self.put_text(command)
                    self.handle_command(command.split(' '))
                self.cursor_pos = 0
                return command
            elif event.key == pl.K_RIGHT:
                self.cursor_pos = min(self.cursor_pos + 1, len(self.input))

            elif event.key == pl.K_LEFT:
                self.cursor_pos = max(self.cursor_pos - 1, 0)

            elif event.key == pl.K_END:
                self.cursor_pos = len(self.input)

            elif event.key == pl.K_HOME:
                self.cursor_pos = 0

            else:
                self.input = self.input[:self.cursor_pos] + event.unicode + self.input[self.cursor_pos:]
                self.cursor_pos += len(event.unicode)

    def handle_command(self, command):
        command, *args = command
        if command in ['h', 'help']:
            self.put_text("HELP:\n" + '\n\t'.join('%s: %s' % (c, h) for c, h in self.help.items()))
        else:
            try:
                res = self.commands[command](*args)
                if res is not None:
                    self.put_text(res)
            except KeyError:
                self.put_text("Command: '%s' not found." % command)

    def add_command(self, command: str, action: callable, help=None):
        self.commands[command] = action
        if help:
            self.help[command] = help


class Canvas(object):
    def __init__(self, *, screen, size=None, background_color=None):
        self.screen = screen
        self.size = size
        self.ratio = self.size[0] / self.size[1]
        self.scale_size = None

        if isinstance(background_color, str):
            self.bg_color = pygame.Color(background_color)
        elif isinstance(background_color, tuple):
            self.bg_color = pygame.Color(*background_color)
        else:
            self.bg_color = None

        self.canvas = pygame.Surface(self.size).convert()
        self.rect = self.canvas.get_rect()
        self.bg = pygame.Surface(self.size).convert()
        if self.bg_color:
            self.bg.fill(self.bg_color)
        pygame.draw.rect(self.bg, (255, 0, 0), self.bg.get_rect(), 1)
        self.canvas.blit(self.bg, (0, 0))

    def on_resize(self, size):
        print('New Size', size)
        nw, nh = size
        w, h = self.size
        r = min(nw / w, nh / h)
        w = int(w * r)
        h = int(h * r)
        self.scale_size = w, h

    @abstractmethod
    def render(self):
        pass

    def on_render(self, screen=None):
        self.canvas.blit(self.bg, (0, 0))
        if screen is None:
            screen = self.screen
        self.render()
        if self.scale_size and self.scale_size != self.size:
            resized = pygame.transform.smoothscale(self.canvas, self.scale_size)
            resizedpos = resized.get_rect(centerx=screen.get_width() / 2, centery=screen.get_height() / 2)
            screen.blit(resized, resizedpos)
        else:
            screen.blit(self.canvas, (0, 0))

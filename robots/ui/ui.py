import os
import pygame
import pygame.locals as pl
from abc import abstractmethod

from robots.ui.renderers import BulletRenderer, RobotRenderer

__all__ = ["Overlay", "Console", "BattleWindow", "MultiBattleWindow"]


def draw_fillbar(bar_dims, pctg, bg_col=(255, 0, 0), fill_col=(0, 255, 0)):
    backgr = pygame.Surface(bar_dims)
    backgr.fill(bg_col)
    if pctg > 0.0:
        fill = pygame.Surface((pctg * bar_dims[0], bar_dims[1]))
        fill.fill(fill_col)
        backgr.blit(fill, (0, 0))
    return backgr


class Overlay(object):
    def __init__(self, size):
        w, h = size
        self.bar_dims = (100, 4)
        self.bar_dims = (
            max(50, min(100, int(w * self.bar_dims[0] / 400))),
            max(2, min(4, int(h * self.bar_dims[1] / 400))),
        )
        if pygame.font:
            self.font_size = max(12, min(36, int(h * 36 / 500)))
            self.font = pygame.font.Font(None, self.font_size)

    def set_battle(self, battle):
        self._robots = battle.robots

    def on_resize(self, size):
        w, h = size
        self.bar_dims = max(25, min(100, int(w * 100 / 400))), max(1, min(4, int(h * 4 / 400)))
        self.font_size = max(12, min(36, int(h * 36 / 500)))
        self.font = pygame.font.Font(None, self.font_size)

    def on_render(self, screen):
        offset = 0
        for robot in self._robots:
            offset = self.draw(screen, robot, offset)

    def draw_fillbar(self, bar_dims, pctg):
        backgr = pygame.Surface(bar_dims)
        backgr.fill((255, 0, 0))
        if pctg > 0.0:
            energy = pygame.Surface((pctg * bar_dims[0], 4))
            energy.fill((0, 255, 0))
            backgr.blit(energy, (0, 0))
        return backgr

    def draw(self, screen, robot, offset):
        color = robot.base_color if robot.base_color is not None else "white"
        color = pygame.Color(color)

        text = self.font.render(str(robot.__class__.__name__), 1, color)
        textpos = text.get_rect(left=0, top=offset)
        screen.blit(text, textpos)

        bar = draw_fillbar(self.bar_dims, robot.energy/100)
        barpos = bar.get_rect(left=0, top=textpos.bottom + 2)
        screen.blit(bar, barpos)

        bar = draw_fillbar(self.bar_dims, robot.turret_heat/(1+3/5), (0, 0, 255), (255, 0, 0))
        barpos = bar.get_rect(left=0, top=barpos.bottom + 1)
        screen.blit(bar, barpos)

        return barpos.bottom + 5


class Console(object):
    def __init__(self, screen, font_family=None, font_size=20):
        self.active = False
        self.font_size = font_size
        self.font_family = font_family
        self.buffer = "PyRoboCode console: v0.1\nType 'help' for detailed commands..."
        self.input = ""
        self.cursor_pos = 0
        self.commands = {}
        self.help = {}

        if self.font_family is not None and not os.path.isfile(self.font_family):
            self.font_family = pygame.font.match_font(self.font_family)
            print(self.font_family)

        self.font_object = pygame.font.Font(self.font_family, self.font_size)

        self.surface = pygame.Surface(screen.get_size())
        self.surface.convert_alpha()
        self.surface.set_alpha(128)

        self.bg = pygame.Surface(screen.get_size())
        self.bg = self.bg.convert()
        pygame.draw.rect(self.bg, (255, 0, 0), self.bg.get_rect(), 1)
        self.surface.blit(self.bg, (0, 0))

    def put_text(self, text):
        self.buffer = self.buffer + "\n" + text

    def on_resize(self, size):
        pass

    def on_render(self, screen):
        if self.active:
            self.surface.blit(self.bg, (0, 0))
            lines = self.buffer.split("\n")
            lines.append("> " + self.input)
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
                self.input = self.input[: max(self.cursor_pos - 1, 0)] + self.input[self.cursor_pos:]
                self.cursor_pos = max(self.cursor_pos - 1, 0)
            elif event.key == pl.K_DELETE:
                self.input = self.input[: self.cursor_pos] + self.input[self.cursor_pos + 1:]
            elif event.key == pl.K_RETURN:
                command, self.input = self.input, ""
                if len(command) > 0:
                    self.put_text(command)
                    self.handle_command(command.split(" "))
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
                self.input = self.input[: self.cursor_pos] + event.unicode + self.input[self.cursor_pos:]
                self.cursor_pos += len(event.unicode)

    def handle_command(self, command):
        command, *args = command
        if command in ["h", "help"]:
            self.put_text("HELP:\n" + "\n\t".join("%s: %s" % (c, h) for c, h in self.help.items()))
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
    def __init__(self, *, size=None, background_color=None):
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
        nw, nh = size
        w, h = self.size
        r = min(nw / w, nh / h)
        w = int(w * r)
        h = int(h * r)
        self.scale_size = w, h

    @abstractmethod
    def render(self):
        pass

    def on_render(self, screen):
        self.canvas.blit(self.bg, (0, 0))
        self.render()
        if self.scale_size and self.scale_size != self.size:
            resized = pygame.transform.smoothscale(self.canvas, self.scale_size)
            resizedpos = resized.get_rect(centerx=screen.get_width() / 2, centery=screen.get_height() / 2)
            screen.blit(resized, resizedpos)
        else:
            screen.blit(self.canvas, (0, 0))


class BattleWindow(Canvas):
    def __init__(self, size):
        Canvas.__init__(self, size=size, background_color="grey")
        self.size = size
        self.bullet_r = BulletRenderer()
        self.robot_r = RobotRenderer()
        self.battle = None
        self.overlay = Overlay(self.size)

    def set_battle(self, battle):
        self.battle = battle
        self.overlay.set_battle(battle)
        for robot in battle.robots:
            self.robot_r.track(robot)
        self.bullet_r.items = self.battle.bullets
        self.on_resize(self.size)

    def render(self):
        if self.battle:
            self.robot_r.render(self.canvas)
            self.bullet_r.render(self.canvas)
            self.overlay.on_render(self.canvas)

    def on_resize(self, size):
        super(BattleWindow, self).on_resize(size)
        self.overlay.on_resize(size)

    def handle_event(self, event):
        if event.key == pygame.K_w:
            self.battle.sim_rate += 10
            self.battle.sim_interval = 1.0 / self.battle.sim_rate
            print(self.battle.sim_rate, self.battle.sim_interval)
        elif event.key == pygame.K_s:
            self.battle.sim_rate = max(1, self.battle.sim_rate - 10)
            self.battle.sim_interval = 1.0 / self.battle.sim_rate
            print(self.battle.sim_rate, self.battle.sim_interval)
        elif event.key == pygame.K_p:
            self.battle.simulate = not self.battle.simulate
            print("Simulate", self.battle.simulate)
        elif event.key == pygame.K_l:
            self.battle.step()


class MultiBattleWindow(Canvas):
    def __init__(self, screen, multibattle, *, background_color="black", rows=None, columns=None):
        Canvas.__init__(self, screen=screen, size=screen.get_size(), background_color=background_color)
        self.multibattle = multibattle
        self.battle_windows = None
        self.overlay = None
        self.r = rows
        self.c = columns
        self.init_grid()

    def init_grid(self):
        c, r = self.c, self.r
        assert bool(c) ^ bool(r)
        self.battle_windows = []
        tw, th = self.size
        bw, bh = self.multibattle.size
        if c:
            w = tw // c
            h = int(w * bh / bw)
            r = th // h
        else:
            h = th // r
            w = int(h * bw / bh)
            c = tw // w

        for i in range(min(c * r, len(self.multibattle.battles))):
            shape = (int((i * w) % (w * c)), int(i // c * h), int(w), int(h))
            self.battle_windows.append(BattleWindow(self.screen.subsurface(shape), self.multibattle.battles[i]))

    def on_render(self, screen=None):
        for i, window in enumerate(self.battle_windows):
            window.on_render()

    def on_resize(self, size):
        self.size = size
        self.init_grid()

    def handle_event(self, event):
        for b in self.multibattle.battles:
            if event.key == pygame.K_w:
                b.sim_rate += 10
                b.sim_interval = 1.0 / b.sim_rate
                print(b.sim_rate, b.sim_interval)
            elif event.key == pygame.K_s:
                b.sim_rate = max(1, b.sim_rate - 10)
                b.sim_interval = 1.0 / b.sim_rate
                print(b.sim_rate, b.sim_interval)
            elif event.key == pygame.K_p:
                b.simulate = not b.simulate
                print("Simulate", b.simulate)

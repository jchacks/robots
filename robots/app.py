import os
import time

import pygame

from robots.battle import Battle
from robots.bots.DoNothing import DoNothing
from robots.bots.MyFirstRobot import MyFirstRobot
from robots.bots.RandomRobot import RandomRobot
from robots.bots.TestRobot import TestRobot
from robots.ui import Console

os.environ['SDL_VIDEO_CENTERED'] = '1'


class App(object):
    def __init__(self, dimensions=(600, 400), battle=None):
        self._running = True
        self.screen = None
        self.rect = None
        self.size = dimensions

        self.render = True
        self.last_render = 0
        self.render_rate = 30
        self.render_interval = 1.0 / self.render_rate
        if battle:
            self.battle = battle
        else:
            print("Creating default battle")
            self.battle: Battle = self.create_default_battle()
        self.console = con = Console('consolas', font_size=14)
        con.add_command('sim', self.set_sim_rate, help='Sets the simulation rate to given integer, -1 for unlimited')
        con.add_command('fps',  self.set_frame_rate, help='Sets the FPS to given integer, -1 for unlimited')
        con.add_command('close', None, help='Closes the application')

    def create_default_battle(self):
        return Battle(self, (400, 400), [TestRobot, TestRobot])

    def set_frame_rate(self, r):
        self.render_rate = int(r)
        self.render_interval = 1 / self.render_rate

    def set_sim_rate(self, r):
        self.battle.sim_rate = int(r)
        self.battle.sim_interval = 1 / self.battle.sim_rate

    def on_init(self):
        pygame.init()
        pygame.font.init()
        self._running = True
        self.init_screen()
        self.console.on_init(self.screen)
        self.battle.init_video(self.screen)
        self.battle.on_init()
        return True

    def init_screen(self):
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()

    def init_logic(self):
        pass

    def on_resize(self, size):
        self.size = size
        self.init_screen()
        self.battle.on_resize(size)

    def render_text(self, text):
        if pygame.font:
            font = pygame.font.Font(None, 36)
            text = font.render(str(text), 1, (255, 255, 255))
            textpos = text.get_rect(right=self.screen.get_width(), top=0)
            self.screen.blit(text, textpos)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.VIDEORESIZE:
            self.on_resize(event.dict['size'])
        elif event.type == pygame.KEYDOWN:
            if self.console.active:
                self.console.handle_event(event)
            else:
                if event.key == pygame.K_RETURN:
                    self.console.active = True
                elif event.key == pygame.K_r:
                    self.render = not self.render
                else:
                    self.battle.on_event(event)

    def on_command(self, command):
        command, *args = command.split(' ')
        if command == 'sim':
            self.battle.sim_rate = int(args[0])
            self.battle.sim_interval = 1 / self.battle.sim_rate
        elif command == 'fps':
            self.render_rate = int(args[0])
            self.render_interval = 1 / self.render_rate

    def on_render(self):
        if (time.time() - self.last_render) >= self.render_interval:
            self.last_render = time.time()
            # self.screen.blit(self.bg, (0, 0))
            self.battle.on_render(self.screen)
            # self.render_text(int(1 / max(0.00000000000001, time.time() - self.battle.last_sim)))
            self.console.on_render(self.screen)
            pygame.display.flip()

    def on_loop(self):
        if self.battle:
            self.battle.on_loop()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if not self.on_init():
            self._running = False
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            if self.render:
                self.on_render()
            if not self.render and not self.battle.simulate:
                time.sleep(0.1)

        self.on_cleanup()


class HeadlessApp(object):
    def __init__(self):
        self._running = True
        self.console = Console()

    def on_init(self):
        pygame.init()
        self._running = True
        if not self.battle:
            print("Battle is None creating default")
            self.battle = Battle(self, (1280, 720), [MyFirstRobot, RandomRobot])
        self.battle.on_init()
        return True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def on_command(self, command):
        command, *args = command.split(' ')
        if command == 'sim':
            self.battle.sim_rate = int(args[0])
            self.battle.sim_interval = 1 / self.battle.sim_rate
        elif command == 'fps':
            self.render_rate = int(args[0])
            self.render_interval = 1 / self.render_rate

    def on_loop(self):
        if self.battle:
            self.battle.on_loop()
            for robot in self.battle.robots:
                print(robot.__class__, robot.energy)

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if not self.on_init():
            self._running = False
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            if not self.battle.simulate:
                time.sleep(0.1)

        self.on_cleanup()

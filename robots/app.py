import os
import time
from abc import abstractmethod

import pygame

from robots.engine.engine import Engine
from robots.ui.ui import Console, BattleWindow

os.environ["SDL_VIDEO_CENTERED"] = "0"
os.environ["DISPLAY"] = ":0"


class App(object):
    """Root rendering class"""

    def __init__(self, settings, size=(600, 400), fps_target=30):
        self._running = True
        self.screen = None
        self.rect = None
        self.size = size
        self.settings = settings

        self.render = True
        self.simulate = True
        self.last_render = 0
        self.render_rate = fps_target
        self.render_interval = 1.0 / self.render_rate

        pygame.init()
        pygame.font.init()
        self._running = True
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()

        self.eng = Engine(settings)
        self.eng.init()
        self.bw = BattleWindow(self.screen, settings.size)    
        self.bw.set_battle(self.eng)

        self.console = con = Console(self.screen, "'Fira Code'", font_size=14)

        con.add_command("fps", self.set_frame_rate, help="Sets the FPS to given integer, -1 for unlimited")
        con.add_command("close", None, help="Closes the application")

    def set_frame_rate(self, r):
        self.render_rate = int(r)
        self.render_interval = 1 / self.render_rate

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
            self.on_resize(event.dict["size"])
        elif event.type == pygame.KEYDOWN:
            if self.console.active:
                # console scope
                self.console.handle_event(event)
            else:
                # window scope
                if event.key == pygame.K_RETURN:
                    self.console.active = True
                elif event.key == pygame.K_r:
                    self.render = not self.render

    def on_command(self, command):
        command, *args = command.split(" ")
        if command == "fps":
            self.render_rate = int(args[0])
            self.render_interval = 1 / self.render_rate
        else:
            #self.bw.on_command()
            pass

    def on_render(self):
        if (time.time() - self.last_render) >= self.render_interval:
            self.last_render = time.time()
            self.bw.on_render(self.screen)
            self.console.on_render(self.screen)
            pygame.display.flip()

    def on_resize(self, size):
        print("resize")
        self.size = size
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()
        for child in self.children:
            child.on_resize(size)

    def on_cleanup(self):
        pygame.quit()

    @abstractmethod
    def step(self):
        pass

    def run(self):
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            if self.render:
                self.on_render()
            if self.simulate:
                self.eng.step()
            if not self.render:
                time.sleep(0.1)

            if self.eng.is_finished():
                self.eng.init()
        self.on_cleanup()

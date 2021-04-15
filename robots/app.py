import os
import pygame
import time

from robots.battle import Battle, MultiBattle
from robots.bots.TestRobot import TestRobot
from robots.ui.ui import Console, BattleWindow, MultiBattleWindow

os.environ["SDL_VIDEO_CENTERED"] = "0"
os.environ["DISPLAY"] = ":0"


class App(object):
    def __init__(self, size=(600, 400), fps_target=60):
        self._running = True
        self.screen = None
        self.rect = None
        self.size = size

        self.render = True
        self.last_render = 0
        self.render_rate = fps_target
        self.render_interval = 1.0 / self.render_rate

        self.children = []
        self.console = con = Console("consolas", font_size=14)

        con.add_command("fps", self.set_frame_rate, help="Sets the FPS to given integer, -1 for unlimited")
        con.add_command("close", None, help="Closes the application")

    def set_frame_rate(self, r):
        self.render_rate = int(r)
        self.render_interval = 1 / self.render_rate

    def on_init(self):
        pygame.init()
        pygame.font.init()
        self._running = True
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()
        self.console.on_init(self.screen)
        return True

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
            for child in self.children:
                # child.on_command()
                pass

    def on_render(self):
        if (time.time() - self.last_render) >= self.render_interval:
            self.last_render = time.time()
            for child in self.children:
                child.on_render(self.screen)
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

    def get_events(self):
        return pygame.event.get()

    def run(self):
        if not self.on_init():
            self._running = False
        while self._running:
            for event in self.get_events():
                self.on_event(event)
            if self.render:
                self.on_render()
            if not self.render:
                time.sleep(0.1)

        self.on_cleanup()


class MultiBattleApp(App):
    """
    Class that extends the Normal App class to render a multi Battle window
    for when a multibattle is being used instead of a normal `Battle`
    """

    def __init__(self, *args, rows=None, columns=None, **kwargs):
        super(MultiBattleApp, self).__init__(*args, **kwargs)
        self.rows = rows
        self.columns = columns

    def init_window(self):
        self.battle_display = MultiBattleWindow(self.screen, self.battle, rows=self.rows, columns=self.columns)

    def create_default_battle(self):
        return MultiBattle(size=(400, 400), robots=[TestRobot, TestRobot], num_battles=2)

    def on_render(self):
        if (time.time() - self.last_render) >= self.render_interval:
            self.last_render = time.time()
            self.battle_display.on_render(self.screen)
            self.console.on_render(self.screen)
            pygame.display.flip()


class HeadlessApp(object):
    def __init__(self, dimensions=(600, 400), battle=None, simulate=True, fps_target=30):
        self._running = True
        self.screen = None
        self.rect = None
        self.size = dimensions
        self.battle_display = None

        self.simulate = simulate
        self.battle = battle

    def run(self):
        while self._running:
            if self.simulate:
                self.battle.on_loop()
            # if self.render and self.battle.dirty:
            #     self.battle.dirty = False
            #     self.on_render()
            if not self.battle.simulate:
                time.sleep(0.1)

    def set_sim_rate(self, r):
        if r == 0:
            return "Cannot set sim rate to 0"
        self.battle.sim_rate = int(r)
        self.battle.sim_interval = 1 / self.battle.sim_rate

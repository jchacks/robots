from robots.ui.components import Console, BattleWindow
from robots.engine.engine import Engine
import pygame
import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


os.environ["SDL_VIDEO_CENTERED"] = "0"
os.environ["DISPLAY"] = ":0"


class Battle(object):
    def __init__(self, robots, size, num_rounds=-1) -> None:
        self.eng = Engine(robots, size)
        self.eng.init()
        self.bw = BattleWindow(size)
        self.bw.set_battle(self.eng)
        self.num_rounds = num_rounds
        self.running = True

    def set_tick_rate(self, rate):
        self.eng.set_rate(rate)

    def step(self):
        if self.running:
            if not self.eng.is_finished() and time.time() >= self.eng.next_sim:
                self.eng.next_sim = time.time() + self.eng.interval
                self.eng.step()
            # If finished do something
            elif self.eng.is_finished():
                if self.num_rounds > 0:
                    self.num_rounds -= 1
                    self.eng.init()
                elif self.num_rounds < 0:
                    self.eng.init()
                elif self.num_rounds == 0:
                    self.running = False
        return self.running

    def on_render(self, screen):
        self.bw.on_render(screen)

    def on_resize(self, size):
        self.bw.on_resize(size)

    def on_command(self, command, args):
        if command == "sim":
            self.eng.set_rate(args[0])
        print("Battle", command)

    def handle_event(self, event):
        print("Battle", event)


class App(object):
    """Root rendering class"""

    def __init__(self, size=(600, 400), fps_target=30):
        self._running = True
        self.screen = None
        self.rect = None
        self.size = size

        self.quit_on_finish = True
        self.render = True
        self.simulate = True
        self.last_render = 0
        self.render_rate = fps_target
        self.render_interval = 1.0 / self.render_rate

        pygame.init()
        pygame.display.set_caption(f"PyRobo - PID {os.getpid()}")
        pygame.font.init()
        self._running = True
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()

        self.child = None
        self.console = con = Console(self.screen, "consolas", font_size=14)

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
                else:
                    self.child.handle_event(event)

    def on_command(self, command):
        command, *args = command.split(" ")
        if command == "fps":
            self.render_rate = int(args[0])
            self.render_interval = 1 / self.render_rate
        else:
            self.child.on_command(command, args)

    def on_render(self):
        if (time.time() - self.last_render) >= self.render_interval:
            self.last_render = time.time()
            if self.child:
                self.child.on_render(self.screen)
            self.console.on_render(self.screen)
            pygame.display.flip()

    def on_resize(self, size):
        print("resize")
        self.size = size
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.rect = self.screen.get_rect()
        self.bg = pygame.Surface(self.screen.get_size())
        self.bg = self.bg.convert()
        if self.child:
            self.child.on_resize(size)

    def on_cleanup(self):
        pygame.quit()

    def step(self):
        for event in pygame.event.get():
            self.on_event(event)
        if self.render:
            self.on_render()
        if self.child.running:
            self.child.step()
        elif self.quit_on_finish:
            self._running = False

    def run(self):
        while self._running:
            self.step()
        self.on_cleanup()

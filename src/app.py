import pygame
from robot import Robot, Bullet
import threading as th
import time


class Battle(object):
    def __init__(self, size, robots):
        self.size = size
        self.robots = robots
        self.iterations = 10


class App(object):
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1080, 800
        self.robots = None
        self.last_render = 0
        self.last_sim = 0
        self.render_rate = 120
        self.sim_rate = 60
        self.render_interval = 1.0 / self.render_rate
        self.sim_interval = 1.0 / self.sim_rate
        self.render = True
        self.simulate = False

    def on_init(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.bg = background = pygame.Surface(self.screen.get_size())
        background = background.convert()
        if pygame.font:
            font = pygame.font.Font(None, 36)
            text = font.render("Pummel The Chimp, And Win $$$", 1, (10, 10, 10))
            textpos = text.get_rect(centerx=background.get_width() / 2)
            background.blit(text, textpos)
        self.screen.blit(background, (0, 0))
        pygame.display.flip()

        background.fill((250, 250, 250))
        self._running = True
        self.robots = [Robot(self, (200.0, 200.0), 0.0), Robot(self, (200.0, 600.0), 180.0)]

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self.sim_rate += 10
                self.sim_interval = 1.0 / self.sim_rate
                print(self.sim_rate, self.sim_interval)
            elif event.key == pygame.K_s:
                self.sim_rate = max(1, self.sim_rate - 10)
                self.sim_interval = 1.0 / self.sim_rate
                print(self.sim_rate, self.sim_interval)

            elif event.key == pygame.K_p:
                self.simulate = not self.simulate

            elif event.key == pygame.K_l:
                self.on_loop()

    def on_loop(self):
        if time.time() - self.last_sim >= self.sim_interval:
            self.last_sim = time.time()
            for bullet in Bullet.class_group:
                bullet.delta()
            for robot in self.robots:
                robot.collide_bullets()
            for robot in self.robots:
                robot.update_logic()
            for robot in self.robots:
                robot.collide_robots()
            for robot in self.robots:
                robot.collide_scan(self.robots)

    def on_render(self):
        if (time.time() - self.last_render >= self.render_interval):
            self.last_render = time.time()
            self.screen.blit(self.bg, (0, 0))
            for robot in self.robots:
                robot.draw(self.screen)
            Bullet.draw(self.screen)
            pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False
        while self._running:
            s = time.time()
            for event in pygame.event.get():
                self.on_event(event)
            if self.simulate:
                self.on_loop()
            if self.render:
                self.on_render()
            # print(time.time()-s)

        self.on_cleanup()


if __name__ == "__main__":
    app = App()
    app.on_execute()

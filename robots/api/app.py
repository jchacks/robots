import time
from robots.battle import Battle
from robots.bots.MyFirstRobot import MyFirstRobot
from robots.bots.RandomRobot import RandomRobot

import tornado.ioloop
import tornado.web

DATA_DIR = '../../data/'

class ApiApp(object):
    def __init__(self):
        self._running = True
        self.battle = Battle(size=(1280, 720), robots=[MyFirstRobot, RandomRobot])
        self.battle.reset()
        self.last_data = 0
        self.data_interval = 1 / 1
        self.data = None

    def run(self):
        while self._running:
            s = time.time()
            if (s - self.last_data) >= self.data_interval:
                self.battle.on_loop()
                self.last_data = s
                self.battle.to_dict()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class WebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
        print("WebSocket closed")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", WebSocket)
    ])

if __name__ == "__main__":
    battle = ApiApp()
    battle.run()

    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()



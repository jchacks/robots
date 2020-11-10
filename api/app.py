import asyncio
import json
import time
from threading import Thread

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from robots.app import App, Battle
from robots.bots import MyFirstRobot, RandomRobot

import tornado

from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler

tornado.ioloop.IOLoop.configure("tornado.platform.asyncio.AsyncIOLoop")
io_loop = tornado.ioloop.IOLoop.current()
asyncio.set_event_loop(io_loop.asyncio_loop)

FPS = 30
interval = 1 / FPS
last_sent = 0
clients = []


def bcint(message):
    for client in clients:
        client.write_message(message)


class WSHandler(WebSocketHandler):
    def open(self):
        print("new connection")
        clients.append(self)

    def on_message(self, message):
        print("message received:  %s" % message)

    def on_close(self):
        print("connection closed")
        clients.remove(self)

    def check_origin(self, origin):
        return True


class BattleHandler(RequestHandler):
    def initialize(self, game):
        self.game = game

    def get(self):
        print(self.game.battle.size)
        self.write(json.dumps(list(self.game.battle.size)))


game = App((600, 400), battle=Battle(size=(600, 400), robots=[MyFirstRobot.MyFirstRobot, RandomRobot.RandomRobot]))
game.set_sim_rate(30)

app = Application(
    [
        (r"/battle", BattleHandler, dict(game=game)),
        (r"/connect", WSHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./", "default_filename": "index.html"}),
    ]
)


def thread():
    while True:
        global last_sent
        if time.time() - last_sent > interval and len(clients) > 0:
            data = game.battle.to_dict()
            io_loop.asyncio_loop.call_soon_threadsafe(bcint, json.dumps(data))
            last_sent = time.time()
        time.sleep(0.001)


if __name__ == "__main__":
    th = Thread(target=game.run, daemon=True)
    th.start()

    th = Thread(target=thread, daemon=True)
    th.start()

    app.listen(4000)
    io_loop.start()

import time
from threading import Thread

import tornado
import asyncio
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler
tornado.ioloop.IOLoop.configure("tornado.platform.asyncio.AsyncIOLoop")
io_loop = tornado.ioloop.IOLoop.current()
asyncio.set_event_loop(io_loop.asyncio_loop)


FPS = 5
interval = 1 / FPS
last_sent = 0
clients = []


def bcint(message):
    for client in clients:
        client.write_message(message)
        print("broadcasted")


def broadcast(message):
    global last_sent
    if time.time() - last_sent > interval and len(clients) > 0:
        io_loop.asyncio_loop.call_soon_threadsafe(bcint, message)
        last_sent = time.time()


class WSHandler(WebSocketHandler):
    def open(self):
        print('new connection')
        clients.append(self)

    def on_message(self, message):
        print('message received:  %s' % message)

    def on_close(self):
        print('connection closed')
        clients.remove(self)

    def check_origin(self, origin):
        return True


app = Application([
    (r"/connect", WSHandler),
    (r"/(.*)", tornado.web.StaticFileHandler,
        {"path": './', "default_filename": "index.html"}),
])

if __name__ == '__main__':
    def thread():
        while True:
            broadcast('abc')
            time.sleep(1)

    th = Thread(target=thread)
    th.start()

    app.listen(6000)
    io_loop.start()

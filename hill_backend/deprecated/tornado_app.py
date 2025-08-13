import os
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
from motor.motor_tornado import MotorClient
from bson import json_util
from logzero import logger


class WebpageHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("hello world")


class ChangesHandler(tornado.websocket.WebSocketHandler):

    connected_clients = set()

    def check_origin(self, origin):
        return True

    def open(self):
        print('open')
        ChangesHandler.connected_clients.add(self)

    def on_close(self):
        print('close')
        ChangesHandler.connected_clients.remove(self)

    @classmethod
    def send_updates(cls, message):
        for connected_client in cls.connected_clients:
            connected_client.write_message({'haha':message})

    @classmethod
    def on_change(cls, change):
        logger.debug(change)
        message = f"{change['operationType']}: {change['fullDocument']['name']}"
        ChangesHandler.send_updates(message)


change_stream = None


async def watch(collection):
    global change_stream

    async with collection.watch(full_document='updateLookup') as change_stream:
        async for change in change_stream:
            ChangesHandler.on_change(change)


def main():
    client = MotorClient("")
    collection = client["test_db"]["username"]

    app = tornado.web.Application(
        [(r"/ws", ChangesHandler), (r"/", WebpageHandler)]
    )

    app.listen(8000)

    loop = tornado.ioloop.IOLoop.current()
    loop.add_callback(watch, collection)
    try:
        loop.start()
    except KeyboardInterrupt:
        pass
    finally:
        if change_stream is not None:
            change_stream.close()


if __name__ == "__main__":
    main()
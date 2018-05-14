import threading
import asyncio
import json
import sys
import uvloop
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from .singleton import Singleton
from .manager import Manager
from .logger import Logger

class Client(metaclass=Singleton):
#class Client(object):
    def __init__(self, host, port, authkey, *args, **kwargs):
        self.has_data = threading.Event()
        self.logger = Logger(__name__)
        self.workers = 20

        self.create_manager(host, port, authkey)
        self.create_event_loop()
        self.executor = ThreadPoolExecutor()
        self.deque = deque()

    def create_manager(self, host, port, authkey):
        Manager.register('get_queue')
        self.manager = Manager(address=(host,port), authkey=authkey)
        self.manager.connect()
        self.queue = self.manager.get_queue()

    def runner(self):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        tasks = []
        for i in range(self.workers):
            tasks.append(asyncio.ensure_future(self.get()))
        self.loop.run_until_complete(asyncio.gather(*tasks))

    def create_event_loop(self):
        t = threading.Thread(target=self.runner)
        #t.setDaemon(True)
        t.start()

    def transmit(self, data):
        self.deque.append(data)
        self.has_data.set()

    async def get(self):
        while True:
            try:
                await self.put(self.deque.popleft())
            except IndexError:
                await self.clear()
                await self.wait()

    async def clear(self):
        await self.loop.run_in_executor(self.executor, self._clear)

    def _clear(self):
        self.has_data.clear()

    async def wait(self):
        await self.loop.run_in_executor(self.executor, self._wait)

    def _wait(self):
        self.has_data.wait()

    async def put(self, data):
        try:
            try:
                data['call_params'] = json.dumps(data['call_params'])
            except:
                data['call_params'] = json.dumps(sys.exc_info())

            await self.loop.run_in_executor(self.executor, self.send, json.dumps(data).encode('utf-8'))
        except:
            self.logger.error(str(sys.exc_info()))

    def send(self, val):
        self.queue.put(val) # Queue is thread-safe and the operation is atomic. No sync primitives required

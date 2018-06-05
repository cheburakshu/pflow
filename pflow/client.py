import threading
import asyncio
import json
import sys
import uvloop
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import pickle

from .singleton import Singleton
from .manager import Manager
from .logger import Logger
from .kafka import Kafka

try:
    import ujson as json
except:
    import json as json

class Client(metaclass=Singleton):
#class Client(object):
    def __init__(self, host=None, port=None, authkey=None, kafka_available=False, min_records=1000, *args, **kwargs):
        self.has_data = threading.Event()
        self.logger = Logger(__name__)
        self.deque = deque()
        self.outbox = deque()
        self.min_records = min_records
        self.overflow_error = False

        if kafka_available:
            self.kafka_available = True
            self.kafka = Kafka()
        else:
            self.kafka_available = False
            self.create_manager(host, port, authkey)

        self.executor = ThreadPoolExecutor()
        self.create_event_loop()

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
                await self.check_to_send()
                await self.wait()

    async def clear(self):
        await self.loop.run_in_executor(self.executor, self._clear)

    def _clear(self):
        self.has_data.clear()

    async def wait(self):
        await self.loop.run_in_executor(self.executor, self._wait)

    def _wait(self):
        self.has_data.wait()

    async def empty(self):
        await self.loop.run_in_executor(self.executor, self._empty)

    def _empty(self):
        self.outbox.clear()

    async def put(self, data):
        try:
            try:
                data['call_params'] = json.dumps(data['call_params']) if not self.overflow_error else None
            except OverflowError:
                data['call_params'] = None
                self.overflow_error = True
            except:
                data['call_params'] = None
            self.outbox.append(data)
            await self.check_to_send()
        except OverflowError:
            self.logger.warn('OverflowError, not parsing call params anymore')
            self.overflow_error = True
        except:
            self.logger.error(str(sys.exc_info()))

    async def check_to_send(self):
            if len(self.outbox) >= self.min_records: 
# The below line takes 4 minutes for a million calls one by one, hence the outbox approach.
                await self.loop.run_in_executor(self.executor, self.send, json.dumps(self.outbox).encode('utf-8'))
                await self.empty()
            else:
                await asyncio.sleep(0)
        except OverflowError:
            self.logger.warn('OverflowError, not parsing call params anymore')
            self.overflow_error = True
        except:
            self.logger.error(str(sys.exc_info()))

    def send(self, val):
        if self.kafka_available:
            self.kafka.produce(val)
        else:
            self.queue.put(val) # Queue is thread-safe and the operation is atomic. No sync primitives required

from multiprocessing import Process, Queue, cpu_count, RLock
import threading
import uvloop
import asyncio
import sanic

from .manager import Manager
from .server import Server
from .kafka import Kafka

class App(Server):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.queue = Queue()
        self.SANIC_PORT = 8000
        Manager.register('get_queue', callable=lambda: self.queue)
        self.manager = Manager(address=('',50000), authkey=b'abracadabra')
        self.NUMBER_OF_PROCESSES = cpu_count() * 2
        self.manager_thread = threading.Thread(target=self.start_manager,args=())

    def starting(self):
        self.start_workers()
        self.manager_thread.start()
        #self.sanic_thread.start()

    def start_workers(self):
        self.workers = []
        for _ in range(self.NUMBER_OF_PROCESSES):
            self.workers.append(Process(target=self.worker, args=(self.queue,)))
        self.workers.append(Process(target=self.start_sanic_server, args=(self.SANIC_PORT,)))

        for w in self.workers:
            w.start()

    def start_manager(self):
        server = self.manager.get_server()
        server.serve_forever()

    def start_sanic_server(self, port):
        app = sanic.Sanic()
        kafka = Kafka()

        @app.route('/sensor/<data>', methods=['POST',])
        async def sensor_handler(request, data):
            kafka.produce(request.body)
            return sanic.response.json({'message':'Success'})

        app.run(host='0.0.0.0', port=port)

    def worker(self, q):
        kafka = Kafka()
        for data in iter(q.get, None):
            kafka.produce(data)

    def stop_workers(self):
        for w in self.workers:
            self.queue.put(None)
            w.join()


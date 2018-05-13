from multiprocessing import Process, Queue, cpu_count, RLock
import threading

from .manager import Manager
from .server import Server
from .kafka import Kafka

class App(Server):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.queue = Queue()
        Manager.register('get_queue', callable=lambda: self.queue)
        self.manager = Manager(address=('',50000), authkey=b'abracadabra')
        self.NUMBER_OF_PROCESSES = cpu_count()
        self.manager_thread = threading.Thread(target=self.start_manager,args=())

    def starting(self):
        self.start_workers()
        self.manager_thread.start()

    def start_workers(self):
        self.workers = []
        for _ in range(self.NUMBER_OF_PROCESSES):
            self.workers.append(Process(target=self.worker, args=(self.queue,)))

        for w in self.workers:
            w.start()

    def start_manager(self):
        server = self.manager.get_server()
        server.serve_forever()

    def worker(self, q):
        kafka = Kafka()
        for data in iter(q.get, None):
            kafka.produce(data)

    def stop_workers(self):
        for w in self.workers:
            self.queue.put(None)
            w.join()


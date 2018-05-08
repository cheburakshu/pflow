from multiprocessing import Process, Queue, cpu_count
from .manager import Manager
from .kafka import Kafka

class Server(object):
    def __init__(self, *args, **kwargs):
        self.queue = Queue()
        Manager.register('get_queue', callable=lambda: self.queue)
        self.manager = Manager(address=('',50000), authkey=b'abracadabra')
        self.NUMBER_OF_PROCESSES = cpu_count()


    def start(self):
        self.workers = [Process(target=self.work, args=(self.queue,)) for _ in range(self.NUMBER_OF_PROCESSES)]
        for w in self.workers:
            w.start()
        server = self.manager.get_server()
        server.serve_forever()

    def work(self, q):
        kafka = Kafka()
        for val in iter(q.get, None):
            data = kafka.serialize(val)
            if data:
                kafka.produce(data)

    def stop(self):
        for w in self.workers:
            self.queue.put(None)
            w.join()

    def restart(self):
        pass

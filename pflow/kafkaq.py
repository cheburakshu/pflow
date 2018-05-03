import queue
import threading
from confluent_kafka import Producer
import time
import json
import sys

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

#Python3
class KafkaQ(metaclass=Singleton):
    def __init__(self,*args,**kwargs):
        self.q = queue.Queue()
        #self.producer = Producer({'bootstrap.servers': 'localhost'})
        self.lock = threading.RLock()
        self.create_threads()

    def enqueue(self, val):
        self.q.put(val)

    def dequeue(self):
        return self.q.get()

    def consumer(self):
        val = self.dequeue() # This line is thread-safe.
        with self.lock:
            data = self.serialize(val)
            if data:
                self.kafka_producer(data)

    def serialize(self, val):
        try:
            val['call_param'] = json.dumps(val['local']) #, cls=CustomEncoder)
        except:
            val['call_param'] = str(sys.exc_info())

        del val['local'] 

        try:
            return json.dumps(val).encode('utf-8')
        except:
            return None

    def kafka_producer(self, data):
        return
        self.producer.produce('logstash', data)

    def kafka_flush(self):
        return
        while True:
            time.sleep(60)
            with self.lock:
                producer.flush()

    def create_threads(self):
        # Create 10 consumer threads
        for _ in range(10):
            t = threading.Thread(target=self.consumer)
            t.setDaemon(True)
            t.start()

        # Create 1 thread to flush kafka 
        for _ in range(1):
            t = threading.Thread(target=self.kafka_flush)
            t.setDaemon(True)
            t.start()

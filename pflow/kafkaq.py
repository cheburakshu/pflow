import queue
import threading
from confluent_kafka import Producer
import time
import json
import sys
import logging
from .singleton import Singleton

#Python3
class KafkaQ(metaclass=Singleton):
    def __init__(self,*args,**kwargs):
        self.q = queue.Queue()
        self.producer = Producer({'bootstrap.servers': 'localhost'})
        self.lock = threading.RLock()
        self.create_threads()
        self.logger = logging.Logger(__name__)

    def enqueue(self, val):
        self.q.put(val)

    def dequeue(self):
        return self.q.get()

    def consumer(self):
        while True:
            val = self.dequeue() # This line is thread-safe.
            with self.lock:
                data = self.serialize(val)
                #self.logger.info(data)
                if data:
                    self.kafka_producer(data)

    def serialize(self, val):
        if val.__contains__('local'):
            try:
                val['call_param'] = json.dumps(val['local']) #, cls=CustomEncoder)
                del val['local'] 
            except:
                val['call_param'] = str(sys.exc_info())

        try:
            return json.dumps(val).encode('utf-8')
        except:
            return None

    def kafka_producer(self, data):
        self.producer.produce('logstash', data)
        self.producer.flush()

    def kafka_flush(self):
        while True:
            time.sleep(60)
            with self.lock:
                self.producer.flush()

    def create_threads(self):
        # Create 10 consumer threads
        for _ in range(5):
            t = threading.Thread(target=self.consumer)
            #t.setDaemon(True)
            t.start()

        # Create 1 thread to flush kafka 
        for _ in range(1):
            t = threading.Thread(target=self.kafka_flush)
            #t.setDaemon(True)
            t.start()

import queue
import threading
from confluent_kafka import Producer
import time
import json
import sys
import logging
from .singleton import Singleton

#Python3
class Kafka(object):
    def __init__(self,*args,**kwargs):
        self.producer = Producer({'bootstrap.servers': 'localhost'})
        self.lock = threading.RLock()
        self.logger = logging.Logger(__name__)

    def serialize(self, val):
        with self.lock:
            if val.__contains__('local'):
                try:
                    val['call_param'] = json.dumps(val['local']) #, cls=CustomEncoder)
                    del val['local'] 
                except:
                    val['call_param'] = str(sys.exc_info())

            try:
                return json.dumps(val).encode('utf-8')
            except:
                return json.dumps(sys.exc_info()).encode('utf-8')

    def produce(self, data):
        with self.lock:
            print(data)
            self.producer.poll(0)
            self.producer.produce('logstash', data)
            print('data sent')
            print(self.producer.flush())
            print('data flushed')


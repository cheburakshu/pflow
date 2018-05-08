import threading
from .singleton import Singleton
from .manager import Manager

class Client(metaclass=Singleton):
#class Client(object):
    def __init__(self, host, port, authkey, *args, **kwargs):
        Manager.register('get_queue')
        self.manager = Manager(address=(host,port), authkey=authkey)
        self.manager.connect()
        self.queue = self.manager.get_queue()
        self.lock = threading.RLock() # Threads using the client can use for sync

    def send(self, val):
        self.queue.put(val) # Queue is thread-safe

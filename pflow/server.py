from multiprocessing import Process, Queue, cpu_count, RLock
from threading import Event, Thread
#from .manager import Manager
#from .kafka import Kafka
from .serverstate import ServerState
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class Server(object):
    '''
    Following Oracle documentation of server states as https://docs.oracle.com/cd/E13222_01/wls/docs81/adminguide/overview_lifecycle.html
    CURRENT STATE -> NEXT STATE(S)
    SHUTDOWN -> STARTING
    STARTING -> STANDBY, RUNNING
    STANDBY -> RESUMING, SHUTTING DOWN
    RESUMING -> RUNNING
    RUNNING -> SUSPENDING
    SUSPENING -> STANDBY
    SHUTTING DOWN -> SHUTDOWN

    Implementing the following first, others will be implemented later.
    SHUTDOWN -> STARTING
    STARTING -> RUNNING
    RUNNING -> SHUTTING DOWN
    SHUTTING DOWN -> SHUTDOWN
    '''
    def __init__(self, *args, **kwargs):
        self.state_machine = ServerState()
        self.current_state = self.target_state = self.state_machine.INITIAL_STATE
        self.lock = RLock()
        self.state_change = Event()

        #self.queue = Queue()
        #Manager.register('get_queue', callable=lambda: self.queue)
        #self.manager = Manager(address=('',50000), authkey=b'abracadabra')
        #self.NUMBER_OF_PROCESSES = cpu_count()

    def start_transition_manager(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        tasks = []
        for state in self.state_machine.VALID_STATES:
            tasks.append(asyncio.ensure_future(self.marshall(state, loop)))
        loop.run_until_complete(asyncio.gather(*tasks))

    async def marshall(self, responder_state, loop):
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, self.responder, responder_state)

    def responder(self, responder_state):
        while True:
            if self.current_state == responder_state and self.current_state != self.target_state:
                self.state_change.wait()
                inputs = self.state_machine.get_state_transition(self.current_state, self.target_state)
                print(responder_state, inputs)
                for input in inputs:
                    next_state = self.state_machine.get_next_state(self.current_state, input)
                    try:
                        self.__getattribute__(next_state.lower())()
                        self.current_state = next_state
                        print(responder_state, next_state)
                    except:
                        logger.warning(next_state)
                    if self.current_state == self.target_state:
                        break
                self.state_change.clear()
            else:
                self.state_change.wait()

    def shutdown(self):
        pass

    def starting(self):
        print('starting called')
        pass

    def standby(self):
        print('standby called')
        pass

    def running(self):
        print('running called')
        pass

    def suspending(self):
        print('suspending called')
        pass

    def shutting_down(self):
        print('shutting down called')
        pass

    def start(self, *args, **kwargs):
        with self.lock:
            self.input = self.state_machine.START
            self.target_state = self.state_machine.RUNNING

    def stop(self, *args, **kwargs):
        with self.lock:
            self.input = self.state_machine.STOP
            self.target_state = self.state_machine.SHUTDOWN

    def restart(self, *args, **kwargs):
        with self.lock:
            self.input = self.state_machine.SUSPEND
            self.target_state = self.state_machine.RUNNING
#    def start(self):
#        self.workers = [Process(target=self.work, args=(self.queue,)) for _ in range(self.NUMBER_OF_PROCESSES)]
#        for w in self.workers:
#            w.start()
#        server = self.manager.get_server()
#        server.serve_forever()
#
#    def work(self, q):
#        kafka = Kafka()
#        for val in iter(q.get, None):
#            data = kafka.serialize(val)
#            if data:
#                kafka.produce(data)
#
#    def stop(self):
#        for w in self.workers:
#            self.queue.put(None)
#            w.join()
#
#    def restart(self):
#        pass

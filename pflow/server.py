from multiprocessing import Process, Queue, cpu_count, RLock
from threading import Event, Thread
#from .manager import Manager
#from .kafka import Kafka
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .serverstate import ServerState
from .logger import Logger

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
        self.logger = Logger(__name__)

        #self.queue = Queue()
        #Manager.register('get_queue', callable=lambda: self.queue)
        #self.manager = Manager(address=('',50000), authkey=b'abracadabra')
        #self.NUMBER_OF_PROCESSES = cpu_count()

    def start_transition_manager(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        tasks = []
        self.logger.info('Starting Transition Mananger')
        for state in self.state_machine.VALID_STATES:
            tasks.append(asyncio.ensure_future(self.marshall(state, loop)))
        try:
            loop.run_until_complete(asyncio.gather(*tasks))
        except KeyboardInterrupt:
            self.logger.warn('Received keyboardInterrupt. Shutting down loop.')
            loop.stop()

    async def marshall(self, responder_state, loop):
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, self.responder, responder_state)

    def responder(self, responder_state):
        while True:
            self.logger.info('State responder for {} is waiting for signal..'.format(responder_state))
            self.state_change.wait()
            with self.lock:
                if self.current_state == responder_state and self.current_state != self.target_state:
                    self.logger.info('State responder for {} is clearing signal..'.format(responder_state))
                    self.state_change.clear()
                else:
                    continue
            self.logger.info('Getting inputs for state transition from {0} to {1}'.format(self.current_state, self.target_state))
            inputs = self.state_machine.get_state_transition(self.current_state, self.target_state)
            for input in inputs:
                next_state = self.state_machine.get_next_state(self.current_state, input)
                try:
                    self.__getattribute__(next_state.lower())()
                    with self.lock:
                        self.current_state = next_state
                        self.logger.info('Current state is {}'.format(next_state))
                    self.logger.info(responder_state)
                except:
                    self.logger.warning(next_state)
                if self.current_state == self.target_state:
                    break

    def shutdown(self):
        pass

    def starting(self):
        pass

    def standby(self):
        pass

    def running(self):
        pass

    def suspending(self):
        pass

    def shutting_down(self):
        pass

    def start(self, *args, **kwargs):
        self.logger.info('Starting server...')
        with self.lock:
            self.logger.info('Setting target state...')
            self.target_state = self.state_machine.RUNNING
            self.state_change.set()
        self.logger.info('Calling State Transition Manager')
        self.start_transition_manager()

    def stop(self, *args, **kwargs):
        with self.lock:
            self.target_state = self.state_machine.SHUTDOWN
            self.state_change.set()
        self.start_transition_manager()

    def restart(self, *args, **kwargs):
        with self.lock:
            self.target_state = self.state_machine.RUNNING
        self.start_transition_manager()
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

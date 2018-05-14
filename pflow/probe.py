import sys
import datetime
import json
import asyncio

from collections import deque
from functools import lru_cache
from .client import Client

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return {'__datetime__': o.isoformat()}
        return {'__{}__'.format(o.__class__.__name__): o.__dict__}

client = None

@lru_cache(maxsize=2048)
def get_client():
# Client is a singleton, instantiated on its first call/load
    return Client('localhost', 50000, b'abracadabra', kafka_available=True)

def profile(sensor=None):
    global client
    try:
        if not client:
            client = get_client()
        # asyncio is unreasonably slow. So, switching to deque.
        #asyncio.run_coroutine_threadsafe(client.transmit({
        #    'call_time': datetime.datetime.utcnow().isoformat(),
        #    'caller': sys._getframe().f_back.f_back.f_code.co_name,
        #    'receiver': sys._getframe().f_back.f_code.co_name,
        #    'call_params': sys._getframe().f_back.f_locals,
        #    'file': sys._getframe().f_back.f_globals.get('__file__'),
        #    'sensor': sensor
        #    }), client.loop)
        client.transmit({
            'call_time': datetime.datetime.utcnow().isoformat(),
            'caller': sys._getframe().f_back.f_back.f_code.co_name,
            'receiver': sys._getframe().f_back.f_code.co_name,
            'call_params': sys._getframe().f_back.f_locals,
            'file': sys._getframe().f_back.f_globals.get('__file__'),
            'sensor': sensor
            })
    except:
        client.logger.error(sys.exc_info())

import sys
import datetime
import json
from kafka import KafkaProducer
from functools import lru_cache

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return {'__datetime__': o.isoformat()}
        return {'__{}__'.format(o.__class__.__name__): o.__dict__}

def profile():
    try:
        data = dict()
        frame = sys._getframe().f_back
        now = datetime.datetime.utcnow().isoformat()

        data['timestamp'] = now
        data['caller'] = frame.f_back.f_code.co_name
        data['callee'] = frame.f_code.co_name
        data['param'] = frame.f_locals

        bdata = json.dumps(data, cls=CustomEncoder, sort_keys=True).encode('utf-8')
        send(bdata)
    except:
        print(sys.exc_info())

@lru_cache(maxsize=2048)
def create_producer():
    return KafkaProducer()

def send(data):
    producer = create_producer() #KafkaProducer()
    producer.send('profile', data)
    producer.flush()
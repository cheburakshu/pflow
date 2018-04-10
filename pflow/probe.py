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

        data['call_time'] = now
        data['caller'] = frame.f_back.f_code.co_name
        data['receiver'] = frame.f_code.co_name

        try:
            data['call_param'] = json.dumps(frame.f_locals, cls=CustomEncoder, sort_keys=True)
        except:
             data['call_param'] = str(sys.exc_info())

        bdata = json.dumps(data, cls=CustomEncoder, sort_keys=True).encode('utf-8')
        send(bdata)
    except:
        print(sys.exc_info())

@lru_cache(maxsize=2048)
def create_producer():
    return KafkaProducer()

def send(data):
    producer = create_producer() #KafkaProducer()
    producer.send('logstash', data)
    producer.flush()

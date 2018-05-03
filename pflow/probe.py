import sys
import datetime
import json
from functools import lru_cache
from confluent_kafka import Producer

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
            data['call_param'] = json.dumps(frame.f_locals) #, cls=CustomEncoder)
        except:
             data['call_param'] = str(sys.exc_info())

        bdata = json.dumps(data).encode('utf-8')
        send(bdata)
    except:
        print(sys.exc_info())

@lru_cache(maxsize=2048)
def create_producer():
    p = Producer({'bootstrap.servers': 'localhost'}) #return KafkaProducer()
    return p

def send(data):
    producer = create_producer() #KafkaProducer()
    producer.poll(0)
    producer.produce('logstash', data)
    #producer.flush()

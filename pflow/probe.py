import sys
import datetime
import json
from .kafkaq import KafkaQ

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
        data['local'] = frame.f_locals

        kafkaQ = KafkaQ()
        kafkaQ.enqueue(data)
    except:
        print(sys.exc_info())

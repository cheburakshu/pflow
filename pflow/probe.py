import sys
import datetime
import json
import os

from .client import Client

class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return {'__datetime__': o.isoformat()}
        return {'__{}__'.format(o.__class__.__name__): o.__dict__}

def profile(sensor=None):
    try:
        #host = os.environ.get('PFLOW_HOST')
        #port = os.environ.get('PFLOW_PORT')
        #auth = os.environ.get('PFLOW_AUTH')
        client = Client('localhost', 50000, b'abracadabra')
        with client.lock:
            data = dict()
            frame = sys._getframe().f_back
            now = datetime.datetime.utcnow().isoformat()
    
            data['call_time'] = now
            data['caller'] = frame.f_back.f_code.co_name
            data['receiver'] = frame.f_code.co_name
            #data['local'] = frame.f_locals
            try:
                data['call_params'] = json.dumps(frame.f_locals, cls=CustomEncoder)
            except:
                data['call_params'] = json.dumps(sys.exc_info())

            if sensor:
                data['sensor'] = sensor
                 
            encoded_data = json.dumps(data).encode('utf-8')

            client.send(encoded_data)
    except:
        print(sys.exc_info())

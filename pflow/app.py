from .server import Server

class App(Server):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def running(self):
        print('app running')


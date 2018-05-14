from .client import Client

# Client is a singleton, instantiated on its first call/load
client = Client('localhost', 50000, b'abracadabra')

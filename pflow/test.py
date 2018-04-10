import probe
class T():
    def __init__(self,*args,**kwargs):
        self.one = '1'
        self.two = '2'
        pass

    def x(self):
        return 'x'

def c(t):
    probe.profile()
    pass

def a(b):
    probe.profile()
    t = T()
    c(t)
    print(b)

a(1)

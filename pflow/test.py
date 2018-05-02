import probe
import datetime
class T():
    def __init__(self,*args,**kwargs):
        self.one = '1'
        self.two = '2'
        pass

    def x(self):
        return 'x'

def d():
    pass

def c(t,d,n,l,p):
    probe.profile()
    pass

def a(b):
    probe.profile()
    t = T()
    n = datetime.datetime.utcnow().isoformat()
    l = [1,2,3]
    p = (1,3,4)
    c(t,d,n,l,p)
    print(b)

a(1)

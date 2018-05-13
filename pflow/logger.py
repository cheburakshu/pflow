import logging
from functools import lru_cache

@lru_cache(maxsize=2048)
class Logger(object):
    def __init__(self, name, level=logging.INFO, *args, **kwargs):
        format = '%(asctime)s: %(name)s: %(process)d: %(levelname)-8s: %(threadName)-11s: %(message)s'
        logging.basicConfig(format=format, level=level)
        self._logger = logging.getLogger(name=name)

    def setLogger(self,_name):
        self._logger = logging.getLogger(_name)

    def getLogger(self):
        return self._logger
       
    def debug(self,message):
        #LEVEL 10
        self.getLogger().debug(message)
    
    def info(self,message):
        #LEVEL 20
        self._logger.info(message)

    def warn(self,message):
        #LEVEL 30
        self._logger.warning(message)

    def error(self,message):
        #LEVEL 40
        self._logger.error(message)

    def critical(self,message):
        #LEVEL 50
        self._logger.critical(message)

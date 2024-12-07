import os
import logging
import logging.config
from enum import Enum
from datetime import datetime

class LogLevel(Enum):
    Debug = 0
    Info = 1
    Warning = 2
    Error = 3
    Exception = 4

class DSLogger:
    __InternalDic = dict()  # static
    
    def __init__(self, loggerName):
        self.logger = logging.getLogger(loggerName)

    def InitConfig(Config_Path, serviceName, componentName):
        logging.config.fileConfig(Config_Path)
        DSLogger.AddFieldToInternalDic("serviceName", serviceName)
        DSLogger.AddFieldToInternalDic("componentName", componentName)
    
    def AddFieldToInternalDic(key, value):
        if key and value:
            DSLogger.__InternalDic[key] = value

    def RemoveFieldFromInternalDic(key):
        if DSLogger.__InternalDic and key in DSLogger.__InternalDic.keys():
            DSLogger.__InternalDic.pop(key,None)

    def PrintLog(self, level, msg, externalDic=dict()):
        if not isinstance(level, LogLevel):
            raise TypeError("level must be an instance of LogLevel Enum")
        if externalDic is None or not isinstance(externalDic, dict):
            raise TypeError("externalDic must be an instance of dictionary")
        if not msg:
            raise ValueError("log msg can not be empty")

        if DSLogger.__InternalDic:
            externalDic.update(DSLogger.__InternalDic)

        if level == LogLevel.Debug:
            self.logger.debug(msg, extra = externalDic)
        if level == LogLevel.Info:
            self.logger.info(msg, extra = externalDic)
        if level == LogLevel.Warning:
            self.logger.warning(msg, extra = externalDic)
        if level == LogLevel.Error:
            self.logger.error(msg, extra = externalDic)
        if level == LogLevel.Exception:
            # call logger.error with exc_info = True, which attaches the last raised exception information
            self.logger.exception(msg, extra = externalDic)
        time = (datetime.now()).strftime("%H:%M:%S")
        print(time,': ',msg)
    
    def Flush(self):
        logging.shutdown()
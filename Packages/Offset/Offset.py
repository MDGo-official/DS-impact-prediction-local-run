import json
import copy
import pathlib
import sys
import os

import numpy as np
import pandas as pd

from Utils import IO, LogLevel, DSLogger
from SignalProcessing import *



class Offset:
    def __init__(self, basefolder, signal, on_ws_info_obj, event_type):
        try:
            self.logger = DSLogger('Offset_Module')
            self.logger.PrintLog(LogLevel.Info, "Offset: module initialize")

            # read configs:
            self.configs = IO.read_config(basefolder, 'offset')

            # Read Data
            self.on_ws_info_obj = on_ws_info_obj
            self.event_type = event_type

        except Exception as ex:
            self.logger.PrintLog(LogLevel.Error, "OnWS: Failed in __init__! Exception: " + str(ex))
            raise ex

    def run(self):
        try:
            a0 = self.on_ws_info_obj["A0"]
            if a0 is None:
                return None
            max_axis = np.argmax(a0)
            offset_float = [-x if abs(x) < self.configs["offset_max_value"] else np.sign(-x)*self.configs["offset_max_value"] for x in a0]
            offset_float[max_axis] = 0
            offset_bit = SignalProcessing.offset_to_bit(offset_float)
            disable_axis = [False,False,False]
            disable_axis[max_axis] = True
            return {"Offsets": offset_bit, "Disabled_axes": disable_axis}

        except Exception as ex:
            self.logger.PrintLog(LogLevel.Error, "Offset: Failed! Exception: " + str(ex))
            raise ex

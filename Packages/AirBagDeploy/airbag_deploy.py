import os
import numpy as np
import pandas as pd
from Utils import IO, LogLevel, DSLogger

class AirBagDeploy:
    def __init__(self, base_folder, signal, calib_info_obj, crash_info_obj, OffSet, car_type=None):
        self.logger = DSLogger("AirBagDeploy_log")
        self.logger.PrintLog(LogLevel.Info, "AirBagDeploy: module initialization")
        self.base_folder = base_folder
        self.config = IO.read_config(self.base_folder, 'airbag')
        self.crash_info_obj = crash_info_obj
        self.DV = crash_info_obj["DV"]
        self.mechanism = crash_info_obj["mechanism"]
        self.car_type = car_type

    def run(self):
        self.logger.PrintLog(LogLevel.Info, "AirBagDeploy: run prediction")
        ab_object = {}
        if self.mechanism == "Rear":
            for axis in ["X", "Y"]:
                if axis == "X":
                    ab_object["Front_AB"] = {}
                    ab_object["Front_AB"]["Deployed"] = False
                    ab_object["Front_AB"]["Value"] = self.DV[axis]
                else:
                    ab_object["Side_AB"] = {}
                    ab_object["Side_AB"]["Deployed"] = True if self.DV[axis] >= self.config[axis] else False
                    ab_object["Side_AB"]["Value"] = self.DV[axis]
        else:
            for axis in ["X", "Y"]:
                if axis == "X":
                    ab_object["Front_AB"] = {}
                    ab_object["Front_AB"]["Deployed"] = True if self.DV[axis] >= self.config[axis] else False
                    ab_object["Front_AB"]["Value"] = self.DV[axis]
                else:
                    ab_object["Side_AB"] = {}
                    ab_object["Side_AB"]["Deployed"] = True if self.DV[axis] >= self.config[axis] else False
                    ab_object["Side_AB"]["Value"] = self.DV[axis]
        return ab_object

    

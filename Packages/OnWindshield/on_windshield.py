import json
import copy
import pathlib
import sys
import os

import numpy as np
import pandas as pd

from Utils import IO, LogLevel, DSLogger
import OnWindshield
from SignalProcessing import SignalProcessing


class OnWS:
    def __init__(self, basefolder, signal, button_pressed, onws_history, calib_history, event_type, offset):
        
        try:
            self.logger = DSLogger('OnWS_Module')
            self.logger.PrintLog(LogLevel.Info, "OnWS: module initialize")

            # read configs:
            self.configs = IO.read_config(basefolder, 'onws')
            axes = self.configs["axes"]

            # Read Data
            self.signal = copy.deepcopy(signal)
            self.button_pressed = button_pressed
            self.onws_history = copy.deepcopy(onws_history)
            self.calib_history = copy.deepcopy(calib_history)
            self.event_type = event_type
            self.offset = offset

            # Substract offset from signal
            self.offset_float = SignalProcessing.bit_to_offset(offset)
            self.signal = SignalProcessing.shift(self.signal, [-x for x in self.offset_float], axes[:3])
            self.acc = self.signal[axes[:3]]
            self.logger.PrintLog(LogLevel.Info, "OnWS: Offset {} was substracted from signal".format(str(offset)))

            # Set object
            self.onws_obj = {}
            self.onws_obj["Decision"] = None
            self.onws_obj["Reason"] = None
            self.onws_obj["ReasonDesc"] = None
            self.onws_obj["ButtonPressed"] = {"Decision": None, "Reason": None}
            self.onws_obj["WSRange"] = self.onws_history[0]["WSRange"]
            self.onws_obj["A0"] = None
            self.onws_obj["InitCond"] = None
            self.onws_obj["Angles"] = None
            self.onws_obj["WSRef"] = self.calib_history[0]["OperationalAngles"][1]
            self.onws_obj["Orientation"] = None
            self.onws_obj["ManualOrientation"] = None if self.onws_history[0].get('ManualOrientation') is None else self.onws_history[0]["ManualOrientation"]
            self.onws_obj["EstWSAngles"] = None
            self.onws_obj["ResetCalibrationHistory"] = None
            self.onws_obj["ResetOffset"] = False
        
        except Exception as ex:
            self.logger.PrintLog(LogLevel.Error, "OnWS: Failed in __init__! Exception: " + str(ex))
            raise ex

    def is_z_axis_in_normal_range(self):
        return self.onws_obj["A0"][2] > self.configs["z_axis_limit"]

    def is_y_angle_in_valid_range(self):
        return (self.onws_obj["Angles"][1] > self.configs["y_angle_min"]) and (self.onws_obj["Angles"][1] < self.configs["y_angle_max"])

    def is_x_angle_in_valid_range(self):
        return (self.onws_obj["Angles"][0] > self.configs["x_angle_min"]) and (self.onws_obj["Angles"][0] < self.configs["x_angle_max"])

    def are_ws_angles_normal(self,axis="xyz"):
        if axis == "xyz":
            if not ((self.onws_obj["Angles"][2] > self.configs["z_angle_min"]) and (self.onws_obj["Angles"][2] < self.configs["z_angle_max"])):
                return False
        if not ((self.onws_obj["Angles"][0] > self.onws_obj["WSRange"]["x_range"][0]) and (self.onws_obj["Angles"][0] < self.onws_obj["WSRange"]["x_range"][1])):
            return False
        if not ((self.onws_obj["Angles"][1] > self.onws_obj["WSRange"]["y_range"][0]) and (self.onws_obj["Angles"][1] < self.onws_obj["WSRange"]["y_range"][1])):
            return False
        return True

    def on_ws_angles_calculation(self):
        if self.calib_history[0]["Status"] == "Calibrated":
            self.onws_obj["EstWSAngles"] = self.calib_history[0]["OperationalAngles"]
        else: 
            angle_changed_index = [i for i,onws_obj in enumerate(self.onws_history) if onws_obj.get("Reason") == "Angle changed"]
            angle_changed_index = None if len(angle_changed_index) == 0 else angle_changed_index[0]+1
            onws_angles_array = [onws_obj["Angles"] for onws_obj in self.onws_history[:angle_changed_index] if onws_obj.get("Decision")==True and onws_obj.get("Angles")] 
            if len(onws_angles_array) != 0: 
                self.onws_obj["EstWSAngles"] = np.median(onws_angles_array, axis=0).tolist()
            else: 
                self.onws_obj["EstWSAngles"] = None
    
    def is_diff_from_ws_normal_in_all_axes(self):
        if not np.isclose(self.onws_obj["Angles"][0],self.onws_obj["EstWSAngles"][0], atol=self.configs["stability_x"]):
            return False
        if not np.isclose(self.onws_obj["Angles"][1],self.onws_obj["EstWSAngles"][1], atol=self.configs["stability_y"]):
            return False
        if not (
            np.isclose((self.onws_obj["Angles"][2] -45) % 90,(self.onws_obj["EstWSAngles"][2] -45) % 90, atol=self.configs["stability_z"])):
            # or 
            # np.isclose(self.onws_obj["Angles"][2],(self.onws_obj["EstWSAngles"][2] + 180) % 360, atol=self.configs["stability_z"]) # upside down rotation on the same WS
            return False
        return True
        
    def are_last_onws_angles_stable(self):
        onws_history_with_angles = [onws_obj for onws_obj in self.onws_history if onws_obj.get('Angles') != None]
        if len(onws_history_with_angles) < self.configs["check_on_t-num"]:
            return False
        last_onws_angles = [onws_obj["Angles"] for onws_obj in onws_history_with_angles[-self.configs["check_on_t-num"]:]]
        last_onws_angles.append(self.onws_obj["Angles"])
        gap = np.max(last_onws_angles,axis=0)-np.min(last_onws_angles,axis=0)
        if gap[0] > self.configs["stability_x"]:
            return False
        if gap[1] > self.configs["stability_y"]:
            return False
        if gap[2] > self.configs["stability_z"]:
            return False
        return True
    
    def is_ws_angle_changed(self):
        if self.onws_obj["EstWSAngles"] is None:
            return False
        if not np.isclose(self.onws_obj["Angles"][1],self.onws_obj["EstWSAngles"][1], atol=self.configs["stability_y"]):
            return True
        return False

    def is_orientation_changed(self):
        if self.onws_obj["EstWSAngles"] is None:
            return False
        if not np.isclose(self.onws_obj["Angles"][2],self.onws_obj["EstWSAngles"][2], atol=self.configs["stability_z"]):
            return True
        return False
    
    def is_stable(self):
        if self.onws_obj["EstWSAngles"] is not None:
            return self.is_diff_from_ws_normal_in_all_axes()
        if self.are_ws_angles_normal("xy") and (self.onws_obj["ButtonPressed"]["Decision"] == True):
            return self.are_last_onws_angles_stable()
        return False

    def update_resets(self, offset_only=False):
        self.onws_obj["ResetOffset"] = True
        if offset_only:
            return
        self.onws_obj["ResetCalibrationHistory"] = {
                    "Source": "Algo",
                    "Behavior": "IgnoreHistory"
                    }

    def run(self):
        try:
            self.onws_obj["A0"] = OnWindshield.DeviceMethods.find_a0(self.acc, self.configs) 
            self.onws_obj["ButtonPressed"] = OnWindshield.DeviceMethods.is_bp(self.button_pressed) 
            
            if self.onws_obj["A0"] is None:
                self.logger.PrintLog(LogLevel.Info, "OnWS: Decision is Unknown, ReasonDesc: A0 was not found")
                self.onws_obj["Decision"] = None
                self.onws_obj["Reason"] = "No A0"
                self.onws_obj["ReasonDesc"] = "A0 was not found"
                return self.onws_obj

            if not self.is_z_axis_in_normal_range():
                self.logger.PrintLog(LogLevel.Info, "OnWS: Decision is Not On WS, ReasonDesc: Z axis is not in normal range, Z axis value: " + str(self.onws_obj["A0"][2]))
                self.onws_obj["Decision"] = False
                self.update_resets()                
                self.logger.PrintLog(LogLevel.Info, "OnWS: Asked to reset Offset and Calibration")
                self.onws_obj["Reason"] = "Invalid angles"
                self.onws_obj["ReasonDesc"] = "Z axis is not in normal range"
                return self.onws_obj        

            self.onws_obj["Orientation"] = OnWindshield.DeviceMethods.orientation_estimation(self.onws_obj["A0"], self.configs)
            if self.onws_obj["ManualOrientation"] is not None:
                self.logger.PrintLog(LogLevel.Info, "OnWS: Manual intervention: Orientation calculated: " + str(self.onws_obj["Orientation"] + " But changed manualy to: " +str(self.onws_obj["ManualOrientation"])))
                self.onws_obj["Orientation"] = self.onws_obj["ManualOrientation"]
            if self.calib_history[0]["Status"] == "Calibrated" and self.onws_obj["Orientation"] == self.onws_history[0]["Orientation"]:
                self.onws_obj["InitCond"] = self.calib_history[0]["OperationalAngles"] 
            else:
                self.onws_obj["InitCond"] = OnWindshield.DeviceMethods.find_init_cond(self.onws_obj["Orientation"], self.onws_obj["WSRef"])
            self.logger.PrintLog(LogLevel.Info, "OnWS: Orientation is: "+self.onws_obj["Orientation"].upper()+ " ,Init condition for torch search: " +str(self.onws_obj["InitCond"]))
            self.onws_obj["Angles"] = OnWindshield.DeviceMethods.torch_search(self.onws_obj["A0"], self.onws_obj["InitCond"], self.configs)
            self.logger.PrintLog(LogLevel.Info, "OnWS: Angles found are: " +str(self.onws_obj["Angles"]))

            is_y_angle_valid = self.is_y_angle_in_valid_range()
            is_x_angle_valid = self.is_x_angle_in_valid_range()
            if not is_y_angle_valid or not is_x_angle_valid:
                self.onws_obj["Decision"] = False
                self.onws_obj["Reason"] = "Invalid angles"
                if not is_y_angle_valid and not is_x_angle_valid:
                    self.onws_obj["ReasonDesc"] = "X and Y angle values are not valid for WS"
                elif not is_y_angle_valid:
                    self.onws_obj["ReasonDesc"] = "Y angle value is not valid for WS"
                else:
                    self.onws_obj["ReasonDesc"] = "X angle value is not valid for WS"
                self.logger.PrintLog(LogLevel.Info, "OnWS: Decision is Not On WS, ReasonDesc: "+self.onws_obj["ReasonDesc"])
                self.update_resets()  
                self.logger.PrintLog(LogLevel.Info, "OnWS: Asked to reset Offset and Calibration")
                return self.onws_obj    
            
            self.on_ws_angles_calculation()
            if self.are_ws_angles_normal() and (self.onws_obj["ButtonPressed"]["Decision"] == True):
                self.onws_obj["Decision"] = True
                if self.is_ws_angle_changed() or self.is_orientation_changed():
                    self.onws_obj["Reason"] =  "Angle changed"
                    self.update_resets()  
                    self.logger.PrintLog(LogLevel.Info, "OnWS: Asked to reset Offset and Calibration, angle changed")
                    if self.is_ws_angle_changed() and self.is_orientation_changed():
                        self.onws_obj["ReasonDesc"] = "WS Angle and Orientation have changed, But angles match WS and button is pressed"
                    elif self.is_ws_angle_changed():
                        self.onws_obj["ReasonDesc"] = "WS Angle has changed, But angles match WS and button is pressed"
                    else:
                        self.onws_obj["ReasonDesc"] = "Orientation has changed, But angles match WS and button is pressed"
                else:
                    self.onws_obj["Reason"] =  "Normal angles"
                    self.onws_obj["ReasonDesc"] = "Angles match WS and button is pressed"
                self.logger.PrintLog(LogLevel.Info, "OnWS: Decision is On WS, ReasonDesc: "+self.onws_obj["ReasonDesc"])
                return self.onws_obj 

            if self.is_stable():
                self.onws_obj["Decision"] = True
                if self.is_orientation_changed():
                    self.onws_obj["Reason"] =  "Angle changed"
                    self.onws_obj["ReasonDesc"] = "Orientation has changed, But device is stable"
                    self.update_resets()  
                    self.logger.PrintLog(LogLevel.Info, "OnWS: Asked to reset Offset and Calibration, angle changed")
                else:
                    self.onws_obj["Reason"] =  "Stable"
                    self.onws_obj["ReasonDesc"] = "Device is stable"
                self.logger.PrintLog(LogLevel.Info, "OnWS: Decision is On WS, ReasonDesc: "+self.onws_obj["ReasonDesc"])
                return self.onws_obj 
            else:
                self.logger.PrintLog(LogLevel.Info, "OnWS: Decision is Not On WS, ReasonDesc: Device is not stable")
                self.onws_obj["Decision"] = False
                self.onws_obj["Reason"] = "Unstable"
                self.onws_obj["ReasonDesc"] = "Device is not stable"
                self.update_resets()  
                self.logger.PrintLog(LogLevel.Info, "OnWS: Asked to reset Offset and Calibration")
                return self.onws_obj 

        except Exception as ex:
            self.logger.PrintLog(LogLevel.Error, "OnWS: Failed! Exception: " + str(ex))
            raise ex

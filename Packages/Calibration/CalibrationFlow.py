import json
import copy
import pathlib
import sys
import os

import numpy as np
import pandas as pd

from Utils import IO, LogLevel, DSLogger
from Calibration import *
from SignalProcessing import *


class Flow:
    def __init__(self, basefolder, signal, onws_history, on_ws_info_obj, calib_history, event_type, offset):

        try:
            self.logger = DSLogger('Caliblation_Module')
            self.logger.PrintLog(LogLevel.Info, "Calibration: module initialize")

            # read configs:
            self.configs = IO.read_config(basefolder, 'calibration')

            # Read data
            self.signal = copy.deepcopy(signal)
            self.onws_history = onws_history
            self.on_ws_info_obj = on_ws_info_obj
            self.calib_history = calib_history
            self.event_type = event_type
            self.offset = offset
            self.offset_float = SignalProcessing.bit_to_offset(offset)
            self.signal = SignalProcessing.shift(self.signal, [-x for x in self.offset_float], self.configs['axes'][:3])

            # Return Info
            self.calib_obj = {}
            self.calib_obj["Status"] = calib_history[0]["Status"]
            self.calib_obj['AxesOrientation'] = "FLU"
            self.calib_obj['OperationalAngles'] = calib_history[0]['OperationalAngles']
            self.calib_obj['OperationalMat'] = calib_history[0]['OperationalMat']
            self.calib_obj['A0'] = on_ws_info_obj['A0']
            self.calib_obj['PsiZ'] = None
            self.calib_obj["Calculations"] = {}

        except Exception as ex:
            self.logger.PrintLog(LogLevel.Error, "Calibration: Failed in __init__! Exception: " + str(ex))
            raise ex

    def calc_est_angles(self):
        self.onws_history.insert(0, self.on_ws_info_obj)
        angle_changed_index = [i for i, onws_obj in enumerate(self.onws_history) if
                               onws_obj["Reason"] == "Angle changed"]
        angle_changed_index = None if len(angle_changed_index) == 0 else angle_changed_index[
                                                                             0] + 1  # TODO: assert tests on multuple angle changed maybe 0 anf not -1
        onws_angles_array = [onws_obj["Angles"] for onws_obj in self.onws_history[:angle_changed_index] 
                                if onws_obj.get("Angles") and onws_obj.get("Decision") == True]
        plane_is_better_angles = [obj["OperationalAngles"] for obj in self.calib_history if
                                  "Calculations" in obj and "IsPlaneBetter" in obj["Calculations"] and
                                  obj["Calculations"]["IsPlaneBetter"] == True]
        if len(plane_is_better_angles) != 0:
            self.calib_obj["Calculations"]["EstWSAngles"] = plane_is_better_angles[0]
        elif len(onws_angles_array) != 0:
            self.calib_obj["Calculations"]["EstWSAngles"] = np.mean(onws_angles_array, axis=0).tolist()
        else:
            self.calib_obj["Calculations"]["EstWSAngles"] = None

    def calibration_rest_optimization(self):
        self.a0_list_cleaned = CalibMethods.clean_outlayers_a0(self.a0_history, self.configs)
        if len(self.a0_list_cleaned) > 0:
            self.calib_obj["Calculations"]["A0_mean"] = np.mean(self.a0_list_cleaned, axis=0).tolist()
        else:
            self.calib_obj["Calculations"]["A0_mean"] = np.mean(self.a0_history, axis=0).tolist()

    def calibration_plane_optimization(self):
        self.psi_z_list_cleaned = CalibMethods.clean_outlayers_psi_z(self.psi_z_history, self.configs)
        if len(self.psi_z_list_cleaned) > 0:
            self.calib_obj["Calculations"]["PsiZ_mean"] = np.mean(self.psi_z_list_cleaned)
        else:
            self.calib_obj["Calculations"]["PsiZ_mean"] = np.mean(self.psi_z_history)

    def is_plane_better(self):
        if len(self.psi_z_list_cleaned) < self.configs['min_ax_events']:
            self.logger.PrintLog(LogLevel.Info, "Calibration: Not enough events with aligned acc, have "
                                 + str(len(self.psi_z_list_cleaned)) + ", expected for at least: " + str(
                self.configs['min_ax_events']))
            return False
        if len(self.a0_list_cleaned) < self.configs['min_a0_events']:
            self.logger.PrintLog(LogLevel.Info, "Calibration: Not enough KAs with rest window, have "
                                 + str(len(self.a0_list_cleaned)) + ", expected for at least: " + str(
                self.configs['min_a0_events']))
            return False
        self.prev_psi_mean = [obj["Calculations"]["PsiZ_mean"] for obj in self.calib_history if
                              "PsiZ_mean" in obj["Calculations"] and obj["Calculations"]["PsiZ_mean"] is not None][0]
        self.calib_obj["Calculations"]["ConvergedDelta"] = abs(self.prev_psi_mean - self.calib_obj["Calculations"]["PsiZ_mean"])
        if np.isclose(self.calib_obj["Calculations"]["ConvergedDelta"], 0):
            self.logger.PrintLog(LogLevel.Info, "Calibration: Converge delta is zero - Psi_Z avarage has not changed")
            return False
        if self.calib_obj["Calculations"]["ConvergedDelta"] > self.configs['plane_better_threshold']:
            self.logger.PrintLog(LogLevel.Info, "Calibration: Converged delta, "
                                 + str(self.calib_obj["Calculations"]["ConvergedDelta"]) 
                                 + " is bigger than threshold: "
                                 + str(self.configs['plane_better_threshold']))
            return False
        self.logger.PrintLog(LogLevel.Info, "Calibration: Converged delta, " + str(
            self.calib_obj["Calculations"]["ConvergedDelta"]) + ". Plane is Better!")
        return True

    def is_reach_calibrated(self):
        if self.calib_obj["Calculations"]["ConvergedDelta"] < self.configs['calibrated_threshold']:
            self.logger.PrintLog(LogLevel.Info, "Calibration: Converged delta is smaller than threshold: "
                                 + str(self.configs['calibrated_threshold']) + ", reached calibrated")
            return True
        self.logger.PrintLog(LogLevel.Info, "Calibration: Converged delta is bigger than threshold: "
                             + str(self.configs['calibrated_threshold']) + ", not calibrated yet")
        return False

    def run(self):

        try:
            # If angle changed now calibration reset have not done yet so update to current angles
            # and return
            if self.on_ws_info_obj["Reason"] == "Angle changed":
                self.calib_obj["Status"] = "Pending"
                self.calib_obj["OperationalAngles"] = self.on_ws_info_obj['Angles']
                self.calib_obj['OperationalMat'] = CalibMethods.calc_rotmat(self.on_ws_info_obj['Angles']).tolist()
                self.logger.PrintLog(LogLevel.Info,
                                     "Calibration: Angle changed, update operational matrix based on OnWS calculation, angles: " + str(
                                         self.calib_obj["OperationalAngles"]))
                return self.calib_obj

            status_list = [obj['Status'] for obj in self.calib_history]
            if "Calibrated" in status_list:
                self.calib_obj["Status"] = "Calibrated"
                self.logger.PrintLog(LogLevel.Info, "Calibration: Device is calibrated, no change")
                return self.calib_obj

            # recalculate est angles to include current OnWS run
            self.calc_est_angles()
            if self.calib_obj["Calculations"]['EstWSAngles'] is None:
                self.logger.PrintLog(LogLevel.Info,
                                     "Calibration: WS has no estimated angles, return default, angles: " + str(
                                         self.calib_obj["OperationalAngles"]))
                return self.calib_obj

            self.calib_obj["OperationalAngles"] = self.calib_obj["Calculations"]['EstWSAngles']
            self.calib_obj['OperationalMat'] = CalibMethods.calc_rotmat(
                self.calib_obj["Calculations"]['EstWSAngles']).tolist()
            self.logger.PrintLog(LogLevel.Info, "Calibration: Update operational matrix with estimated angles: " + str(
                self.calib_obj["OperationalAngles"]))
            self.calib_obj["Calculations"]["Ax"], ax_wind_inds = CalibMethods.find_ax(self.signal,
                                                                                      self.calib_obj['OperationalMat'],
                                                                                      self.configs)
            if self.calib_obj["Calculations"]["Ax"] is None:
                self.logger.PrintLog(LogLevel.Info,"Calibration: could not found Ax window")
                self.found_ax = False
            else:
                self.logger.PrintLog(LogLevel.Info, "Calibration: found Ax window")
                self.found_ax = True

            self.a0_history = [obj['A0'] for obj in self.calib_history if obj.get('A0') is not None]
            if self.calib_obj['A0'] is not None:
                self.logger.PrintLog(LogLevel.Info, "Calibration: found A0 window")
                self.a0_history.append(self.calib_obj['A0'])
            if len(self.a0_history) == 0:
                return self.calib_obj
            self.calibration_rest_optimization()

            
            self.psi_z_history = [obj['PsiZ'] for obj in self.calib_history if obj.get('PsiZ') is not None]
            if len(self.psi_z_history) == 0 and not self.found_ax:
                return self.calib_obj
            
            if self.found_ax:
                self.calib_obj["Calculations"]["IsAcc"] = CalibMethods.is_acc(self.signal, ax_wind_inds, self.configs)
                self.calib_obj["PsiZ"] = CalibMethods.calc_psi_z(
                    self.calib_obj["Calculations"]["A0_mean"],
                    self.calib_obj["Calculations"]['Ax'],
                    self.calib_obj["Calculations"]["IsAcc"])
                self.psi_z_history.append(self.calib_obj["PsiZ"])
            self.calibration_plane_optimization()
            
            # Check if somethink changes from last time: (events can run in parallel)
            psiz_mean_list = [obj["Calculations"]['PsiZ_mean'] for obj in self.calib_history if (obj.get('Calculations') is not None) and (obj["Calculations"].get('PsiZ_mean') is not None)]
            if len(psiz_mean_list) != 0:
                if np.isclose(self.calib_obj["Calculations"]["PsiZ_mean"], psiz_mean_list[-1]):
                    self.logger.PrintLog(LogLevel.Info,"Calibration: Nothing chaged, no nead for re-caculate")
                    return self.calib_obj
            
            self.logger.PrintLog(LogLevel.Info,"Calibration: New Information, re-calculating")
            self.calib_obj["Calculations"]["RotationMatrix"] = CalibMethods.find_plane_rotmat(
                self.calib_obj["Calculations"]["A0_mean"],
                self.calib_obj["Calculations"]["PsiZ_mean"]).tolist()
            self.calib_obj["Calculations"]["RotationAngles"] = CalibMethods.find_angles_from_rotmat(
                self.calib_obj["Calculations"]["RotationMatrix"])
            self.logger.PrintLog(LogLevel.Info, "Calibration: Plane Rotation Matrix was calculated, angles: " + str(
                self.calib_obj["Calculations"]["RotationAngles"]))

            self.calib_obj["Calculations"]["IsPlaneBetter"] = self.is_plane_better()
            if not self.calib_obj["Calculations"]["IsPlaneBetter"]:
                return self.calib_obj

            self.calib_obj["OperationalAngles"] = self.calib_obj["Calculations"]["RotationAngles"]
            self.calib_obj['OperationalMat'] = self.calib_obj["Calculations"]["RotationMatrix"]
            self.logger.PrintLog(LogLevel.Info,
                                 "Calibration: Update operational matrix with plane matrix, angles: " + str(
                                     self.calib_obj["OperationalAngles"]))
            if not self.is_reach_calibrated():
                return self.calib_obj

            self.logger.PrintLog(LogLevel.Info, "Calibration: Device reached Calibrated status")
            self.calib_obj["Status"] = "Calibrated"
            return self.calib_obj

        except Exception as ex:
            self.logger.PrintLog(LogLevel.Error, "Calibration: Failed! Exception: " + str(ex))
            raise ex


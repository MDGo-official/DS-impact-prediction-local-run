import os
import sys
import torch
import numpy as np
import pandas as pd
import architectures
import bottleneck as bn

from SignalProcessing import SignalProcessing as sp
from scipy.special import expit as sigmoid
from Utils import IO, DSLogger, LogLevel
from CrashDetection.crash_mechanism import CrashMechanism 
from CrashDetection.pothole_indicator import Pothole_Indicator


class CrashDetection:
    def __init__(self, basefolder, all_signal_not_rot, calib_info_obj, OffSet):
        self.logger = DSLogger("crash_det")
        self.basefolder = basefolder
        self.crash_config = IO.read_config(self.basefolder, 'crash')
        self.acc_columns = self.crash_config["acc_columns_model"]
        self.gyro_columns = self.crash_config["gyro_columns"]

        self.logger.PrintLog(LogLevel.Info, f"calib_obj: {calib_info_obj}")
        self.logger.PrintLog(LogLevel.Info, f"OffSet: {OffSet}")

        self.all_signal_not_rot_copy = all_signal_not_rot.copy(deep=True)
        self.all_signal = sp.rotate_signal(self.all_signal_not_rot_copy, calib_info_obj["OperationalMat"], "FRD",
                                           calib_info_obj["AxesOrientation"], self.crash_config["all_acc_columns"],
                                           OffSet)
        self.calib_info = calib_info_obj
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.sample_rate = self.crash_config["sample_rate"]
        self.section_length = self.crash_config["section_length"]

        self.logger.PrintLog(LogLevel.Info, f"signal_columns: {self.all_signal.columns}")
        self.logger.PrintLog(LogLevel.Info, f"rotated_signal_stats: {self.all_signal.describe()}, ")

    def rollover_check(self):
        """
        Integrates on gyro and look at x/y axis to find if rollover
        Returns: 
            {'X': None / theta, 'Y': None / theta}
        """
        gyro = self.all_signal_not_rot_copy[self.gyro_columns]
        aligned_gyro = self.calib_info['OperationalMat'] @ gyro.T
        angles = np.trapz(aligned_gyro, dx=1/200, axis=1)
        rollover_info = {}
        rollover_info['X'] = angles[0] if abs(angles[0]) > self.crash_config["rollover_angles"] else None
        rollover_info['Y'] = angles[1] if abs(angles[1]) > self.crash_config["rollover_angles"] else None
        return rollover_info

    def alignSignal(self):
        if self.all_signal.shape[0] >= self.crash_config["len_multi_input_signal"]:
            self.all_signal = self.all_signal.iloc[:self.crash_config["len_multi_input_signal"], :]
        else:
            np.random.seed(40)
            sigLen = self.crash_config["len_multi_input_signal"] - self.all_signal.shape[0]
            self.all_signal = pd.concat((self.all_signal, pd.DataFrame((np.random.uniform(low=-0.05, high=0.05
                                                                                          , size=(sigLen, 3)))
                                                                       , columns=self.all_signal.columns))
                                        , axis=0, ignore_index=True)

    def findThreeSignals(self, data):
        data = data.to_numpy().astype("float32")[:, :-1]
        peak_len = self.crash_config["sample_rate"] * 1
        peak_shift = self.crash_config["peak_shift_right"]
        move_min_win = self.crash_config["move_win_len"]

        min_ind = peak_len // 2 + peak_shift
        max_ind = data.shape[0] - (peak_len // 2 - peak_shift)
        norm = np.linalg.norm(data[min_ind - move_min_win + 1: max_ind, :-1], axis=1)
        if move_min_win == 1:
            ind_max = np.argmax(norm)
        else:
            move_min = bn.move_min(norm, window=move_min_win, )[move_min_win - 1:]
            ind_max = np.where(move_min == bn.nanmax(move_min))[0][0]
        event_indexes = [ind_max, ind_max + peak_len]
        data1 = data[ind_max: ind_max + peak_len, :]
        start_ind2 = (
                                 ind_max + min_ind - move_min_win) - peak_len // 2
        if start_ind2 < 0:
            start_ind2 = 0
        end_ind2 = start_ind2 + 2 * peak_len
        if end_ind2 > data.shape[0]:
            start_ind2, end_ind2 = -2 * peak_len, data.shape[0]
        data2 = data[start_ind2: end_ind2, :]
        return (data1, data2, data), event_indexes

    def load_multi_input_model(self):
        self.model = eval(f"architectures.{self.crash_config['multi_input_model']}()")
        self.model.to(self.device)
        model_path = os.path.join(self.basefolder, "Models", "crash_models",
                                  self.crash_config["multi_input_model"] + ".pt")
        state_dict = torch.load(model_path, map_location=lambda storage, loc: storage)
        self.model.load_state_dict(state_dict)

    def prediction_for_multi_input(self, data):
        self.load_multi_input_model()
        self.model.eval()
        inp_data = [torch.from_numpy(inp_data.T.reshape(1, 2, -1)).to(self.device).float() for inp_data in data]
        _, output = self.model(inp_data)
        output = output.detach().cpu().numpy()
        self.logger.PrintLog(LogLevel.Info, f"model_output: {output}")
        crash_prob = float(output[0][1])
        crash = True if crash_prob > self.crash_config["probability_threshold"] else False
        return crash, crash_prob

    def calc_delta_v_xy(self, df, sig_fs=200):
        df_tr = pd.DataFrame()
        for col in df.loc[:, self.acc_columns]:
            col_n = col.replace(self.crash_config["acc_term"], "Delta")
            delta_v = np.cumsum(((df[col] * 9.8) / sig_fs) * 3600 / 1000)
            df_tr[col_n] = delta_v
        return df_tr

    def calc_maxG(self, df):
        maxX, maxY, maxZ = df[self.crash_config["all_acc_columns"]].abs().max(axis=0).round(2).to_numpy()
        return maxX, maxY, maxZ

    @staticmethod
    def calc_max_delta_v_xy(df):
        """potentially add a moving window that looks for the biggest dv within a window"""
        X_max_delta_v = round(df["Delta_X"].abs().max(), 2)
        Y_max_delta_v = round(df["Delta_Y"].abs().max(), 2)
        return X_max_delta_v, Y_max_delta_v


    def run(self):
        """
        :return: {"isCrash": (True, None) or (False, 'failure string'),
            "confidence": [float],
            "mechanism": [String],
            "theta": [Float],
            "DV": {"X": [float], "Y": [float]}
            "RolloverAngels": {"X":[float],"Y"[float]}},
            "severity": None or [String]
        }
        """
        try:
            result = {}

            # Rollover Check:
            rollover_info = self.rollover_check()
            result["RolloverAngels"] = rollover_info
            if any(x is not None for x in rollover_info.values()):
                result["isCrash"] = (True, None)
                result["confidence"] = 1.0
                result["mechanism"] = 'Rollover'
                result["theta"] = 0
                result["DV"] = {"X": 0, "Y": 0}
                maxX, maxY, maxZ = self.calc_maxG(self.all_signal)
                result["maxG"] = {"X": maxX, "Y": maxY, "Z": maxZ}
                return result                               

            self.alignSignal()
            signals, indexes = self.findThreeSignals(self.all_signal)
            self.logger.PrintLog(LogLevel.Info, f"ind_start: {indexes[0]}, ind_end: {indexes[-1]}")
            self.xyz_section = self.all_signal.iloc[indexes[0]: indexes[-1], :].copy(deep=True)
            self.logger.PrintLog(LogLevel.Info, "getting crash prediction")
            is_crash, result["confidence"] = self.prediction_for_multi_input(signals)

            self.logger.PrintLog(LogLevel.Info, f"is_crash: {is_crash},confidence: {result['confidence']}")
            if is_crash:
                result["isCrash"] = (is_crash, None)
            else:
                result["isCrash"] = (is_crash, 'Not An Accident')

            self.logger.PrintLog(LogLevel.Info, "getting crash mechanism")
            result["mechanism"], result["theta"] = CrashMechanism.get_mechanism(self.xyz_section, self.crash_config)

            # get delta-v info
            self.logger.PrintLog(LogLevel.Info, "getting delta-v")
            dv_edges = self.crash_config["dv_edges"]   # calculate dv
            self.xy_section_delta_v = self.calc_delta_v_xy(self.xyz_section.iloc[dv_edges[0]: dv_edges[1]].
                                                           copy(deep=True))
            X_max_delta_v, Y_max_delta_v = self.calc_max_delta_v_xy(self.xy_section_delta_v)
            result["DV"] = {"X": X_max_delta_v, "Y": Y_max_delta_v}
            maxX, maxY, maxZ = self.calc_maxG(self.xyz_section)
            result["maxG"] = {"X": maxX, "Y": maxY, "Z": maxZ}
            # severity estimation
            result["severity"] = None  # [light, moderate, severe]
            # pothole indicator
            if is_crash:
                pothole_indicator = Pothole_Indicator(self.xyz_section,self.crash_config)
                if pothole_indicator.is_bump():
                    if max([maxX,maxY]) < self.crash_config["xy_thresh_pothole"]:
                        result["pothole_indicator"] = True
                    else:
                        result["pothole_indicator"] = False
                else:
                    result["pothole_indicator"] = False

            return result
        except Exception as exc:
            self.logger.PrintLog(LogLevel.Error, "Error occured while running crash detection package: {}".format(exc))
            raise exc


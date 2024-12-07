import os
import numpy as np
import pandas as pd

from Utils import IO, DSLogger, LogLevel

class IsValid:
    def __init__(self, basefolder, signal, event_type):
        self.basefolder = basefolder
        self.config = IO.read_config(self.basefolder, 'IsValid')
        self.signal_acc = signal.loc[:, self.config["acc_columns"]]
        self.signal_gyro = signal.loc[:, self.config["gyro_columns"]]
        self.event_type = event_type
        self.logger = DSLogger("IsValid")

    def check_1_peak_near_edge(self, df):
        """detects if a crash pulse has its peak too close to the edge"""
        if df.to_numpy().max() > self.config["minimal_edge_peak_height"]:
            ind = np.argmax(np.linalg.norm(df, axis=1))
            # check if the peak is too near the beginning or too near the end
            if ind < self.config["minimal_peak_edge_distance"] or (df.shape[0] - ind) < self.config["minimal_peak_edge_distance"]:
                return "peak is too near the edge"
            else:
                return False
        else:
            return False

    def check_2_constant_values(self, df):
        for name, col_values in df.iteritems():

            if col_values.unique().shape[0] < self.config["minimal_unique_values"]:
                return "not enough unique values"

            for i in range(0, len(col_values) - self.config["max_constant_segment_length"]):
                if col_values.iloc[i:i + self.config["max_constant_segment_length"]].unique().shape[0] == 1:
                    return 'During the event there is an interval at constant value'

        return False

    def check_3_bad_range(self, df):
        if df.abs().to_numpy().max() > self.config["max_valid_value"]:
            return "the signal contains a value above the maximum valid value"
        else:
            return False
        
    def check_gyro(self, df):
        start_ind = np.nonzero(self.signal_gyro.to_numpy())[0][0]
        gyro_df = self.signal_gyro.to_numpy()[start_ind:]
        for i in range(3):
            zeros_ind = np.where(gyro_df[:,i] == 0)[0]
            split_ind = np.where(np.diff(zeros_ind) > 1)[0]
            splits = np.split(zeros_ind, split_ind+1)
            res = max([len(j) for j in splits])
            if res > self.config["gyro_max_num_zeros"]:
                return "Gyro should not have long intervals of 0"
        return False

    def run(self):
        if self.event_type=="KA":
            return True, None

        method_list = [func for func in dir(IsValid) if callable(getattr(IsValid, func)) and
                       func.startswith("check")]
        method_list = sorted(method_list)

        error_message = None
        for method in method_list:
            ans = eval(str('self.' + method + '(self.signal_acc)'))
            if ans:
                error_message = ans
                break

        if error_message is None:
            return True, None
        else:
            self.logger.PrintLog(LogLevel.Warning, "signal not valid: {}".format(error_message))
            return False, error_message

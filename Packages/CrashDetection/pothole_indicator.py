import pandas as pd
import numpy as np
import bottleneck as bn
import copy

class Pothole_Indicator:
    def __init__(self,signal_peak,configs):
        self.configs = configs["pothole_indicator"]
        self.signal_peak = copy.deepcopy(signal_peak)
        self.signal_peak = pd.DataFrame(self.signal_peak,columns=configs["all_acc_columns"])
        self.peak_len = self.configs["peak_len"]
        self.peak_shift = self.configs["peak_shift"]
        self.move_win = self.configs["move_win"]
        self.moving_type = self.configs["moving_type"]
        self.times_bigger = self.configs["times_bigger"]

    def findPeack(self):
        signal_peak = copy.deepcopy(self.signal_peak).to_numpy().astype("float32")[:, :-1]

        min_ind = self.peak_len // 2 + self.peak_shift
        max_ind = signal_peak.shape[0] - (self.peak_len // 2 - self.peak_shift)
        
        norm = np.linalg.norm(signal_peak[min_ind - self.move_win + 1: max_ind, :-1], axis=1)
        
        if self.move_win == 1:
            ind_max = np.argmax(norm)
        elif self.moving_type =="min":
            move_min = bn.move_min(norm, window=self.move_win, )[self.move_win - 1:]
            ind_max = np.where(move_min == bn.nanmax(move_min))[0][0]
        elif self.moving_type =="avg":
            move_min = bn.move_mean(norm, window=self.move_win, )[self.move_win - 1:]
            ind_max = np.where(move_min == bn.nanmax(move_min))[0][0]
        return ind_max, ind_max + self.peak_len
    
    def is_bump(self):    
        ind_min, ind_max = self.findPeack()
        self.signal_peak["Acc_Z"] = copy.deepcopy(self.signal_peak["Acc_Z"]) + 1
        
        energy = np.trapz(np.abs(self.signal_peak.iloc[range(ind_min, ind_max)]), dx=1, axis=0)
        max_xy = max([abs(energy[0]), abs(energy[1])])
        if abs(energy[2])>(max_xy*self.times_bigger):
            return True
        else:
            return False
       

        
        
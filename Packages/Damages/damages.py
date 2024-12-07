import os
import torch
from SignalProcessing import SignalProcessing as sp
import numpy as np
import pandas as pd
import traceback
import copy
import architectures
from Utils import IO, LogLevel, DSLogger
import Damages


class DamagesPrediction:
    def __init__(self, base_folder, signal, calib_info_obj, crash_info_obj, OffSet, car_type=None):
        self.logger = DSLogger("Damages_log")
        self.logger.PrintLog(LogLevel.Info, "Damages: module initialization")
        self.base_folder = base_folder
        self.signal = signal.copy(deep=True)
        self.op_matrix = np.array(calib_info_obj["OperationalMat"])
        self.axes_directions = calib_info_obj["AxesOrientation"]
        self.offset = OffSet
        self.mechanism = crash_info_obj["mechanism"]
        self.theta = crash_info_obj["theta"]
        self.DV = copy.deepcopy(crash_info_obj["DV"])
        self.car_type = car_type
        self.package_name = os.path.split(os.path.dirname(__file__))[-1]
        self.params = IO.read_config(self.base_folder, self.package_name)
        self.net_arch = self.params['architecture']
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    def get_net(self):
        self.logger.PrintLog(LogLevel.Info, "Start getting net")
        self.net = eval('architectures.' + self.net_arch + '()').to(self.device)
        self.logger.PrintLog(LogLevel.Info, "Net was gotten")

    def load_model(self):
        self.logger.PrintLog(LogLevel.Info, "Start loading model")
        self.net.to(self.device)
        model_path = os.path.join(self.base_folder, "Models", "Damages_models", "damage_regression.pth")
        state_dict = torch.load(model_path, map_location=lambda storage, loc: storage)
        self.net.load_state_dict(state_dict)
        self.logger.PrintLog(LogLevel.Info, "Model was loaded")

    def preprocess(self):
        self.logger.PrintLog(LogLevel.Info, "Start preprocess signal")
        fs = self.params.get('InFs', 200)
        outFs = self.params.get('OutFs', 200)
        self.signal = self.signal[['Acc_X', 'Acc_Y', 'Acc_Z']]
        self.signal = sp.rotate_signal(self.signal, self.op_matrix, output_orientation="FRD",
                                       input_orientation=self.axes_directions, sensors=['Acc_X', 'Acc_Y', 'Acc_Z'],
                                       offset=self.offset)

        self.signal = self.signal.rename(columns={'Acc_X': 'X', 'Acc_Y': 'Y', 'Acc_Z': 'Z'})
        self.signal = self.signal[["X", "Y"]]
        self.signal = sp.insert_time_column(self.signal, sigFs=fs)
        if outFs != fs:
            self.signal, _ = sp.change_sampling_rate(self.signal, outFs=outFs)
        self.signal = sp.smooth_dataset_filter(self.signal, cutoffFreq=self.params["cutoffFreq"])
        self.signal = sp.alignment_signal(self.signal, size=self.params["signal_length"])
        self.signal = self.signal.to_numpy()[:, 1:]
        self.signal = self.signal.reshape(-1, self.signal.shape[0], self.signal.shape[1]).transpose(0, 2, 1)
        self.logger.PrintLog(LogLevel.Info, "Finish preprocess signal")

    def damage_prediction(self):
        self.logger.PrintLog(LogLevel.Info, "Start damage prediction")
        input = torch.from_numpy(self.signal).to(self.device).float()
        self.net.eval()
        output = self.net(input)
        output = output.data.cpu().numpy()
        Width = self.params["cells_dict"]["W"]
        Length = self.params["cells_dict"]["L"]
        levels = self.params["cells_dict"]["levels"]
        cells = ["Cell_" + w + "_" + str(l) + "_" + level for w in Width for l in Length for level in levels]
        output = 1 * (output > self.params.get("deform_threshold", 30))
        self.result = pd.DataFrame(output, columns=cells).to_dict(orient='index')[0]
        self.result = set([k for k, v in self.result.items() if v == 1])
        post_process = Damages.PostProcessing(self.result, self.params, self.mechanism, theta=self.theta)
        final_result = post_process.run()
        self.logger.PrintLog(LogLevel.Info, "Damage was predicted")
        return final_result

    def shrink_to_two_levels(self):
        post_process_dict = dict()
        for level in ["Low", "High"]:
            if level == "Low":
                levels = ["Middle", "Low"]
            elif level == "High":
                levels = ["Middle", "High"]

            columns = [k for k in self.result.keys() if k.split("_")[-1] in levels]
            new_cells = set(["_".join(i.split('_')[:-1]) for i in self.result.keys()])
            new_data = dict()
            for c in new_cells:
                temp = []
                for l in levels:
                    if c + "_" + l in columns:
                        temp.append(self.result[c + "_" + l])
                temp = max(temp)
                new_data[c] = temp
            for k, v in new_data.items():
                post_process_dict[k + "_" + level] = v
        self.result = set([k for k, v in post_process_dict.items() if v == 1])

    def run(self):
        try:
            self.logger.PrintLog(LogLevel.Info, "Damages: run predictions")
            self.get_net()
            self.load_model()
            self.preprocess()
            result_dict = self.damage_prediction()
            return result_dict
        except Exception as e:
            self.logger.PrintLog(LogLevel.Exception, f"Exception was raised: {e}")
            self.logger.PrintLog(LogLevel.Exception, str(traceback.format_exc()))
            raise e


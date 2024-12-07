import os
import architectures
import torch
from SignalProcessing import SignalProcessing as sp
import glob
import numpy as np
import pandas as pd
import traceback
from Utils import IO, LogLevel, DSLogger


class VS:
    def __init__(self, base_folder, signal, calib_info_obj, crash_info_obj, OffSet):
        self.logger = DSLogger("VirtualSensors_log")
        self.logger.PrintLog(LogLevel.Info, "VirtualSensors: module initialization")
        self.base_folder = base_folder
        self.signal = signal.copy(deep=True)
        self.op_matrix = np.array(calib_info_obj["OperationalMat"])
        self.axes_directions = calib_info_obj["AxesOrientation"]
        self.offset = OffSet
        self.mechanism = crash_info_obj["mechanism"]
        self.package_name = os.path.split(os.path.dirname(__file__))[-1]
        self.params = IO.read_config(self.base_folder, self.package_name)
        self.net_arch = self.params['architecture']
        self.net_arch_hip = self.params["architecture_hip"]
        self.SideRight = ({"1": "2", "4": "3"} if self.mechanism == "SideRight" else False)
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    def get_net(self):
        self.logger.PrintLog(LogLevel.Info, "Start getting nets")
        self.net = eval('architectures.' + self.net_arch + '()').to(self.device)
        self.net_hip = eval('architectures.' + self.net_arch_hip + '()').to(self.device)
        self.logger.PrintLog(LogLevel.Info, "Nets were gotten")

    def preprocess(self):
        self.logger.PrintLog(LogLevel.Info, "Start signal preprocess")
        fs = self.params['InFs']
        outFs = self.params['OutFs']
        self.signal = self.signal[['Acc_X', 'Acc_Y', 'Acc_Z']]
        self.signal = sp.rotate_signal(self.signal, self.op_matrix, output_orientation="FRD",
                                       input_orientation=self.axes_directions, sensors=['Acc_X', 'Acc_Y', 'Acc_Z'],
                                       offset=self.offset)

        self.signal = self.signal.rename(columns={'Acc_X': 'X', 'Acc_Y': 'Y', 'Acc_Z': 'Z'})
        self.signal["Z"] = self.signal["Z"].to_numpy() + 1
        if self.mechanism == "SideRight":
            self.signal = sp.align_axes(self.signal, input_orientation='FLD')
            self.mechanism = "SideLeft"
        self.signal = sp.insert_time_column(self.signal, sigFs=fs)
        if outFs != fs:
            self.signal, _ = sp.change_sampling_rate(self.signal, outFs=outFs)
        self.signal = sp.smooth_dataset_filter(self.signal, cutoffFreq=self.params["cutoffFreq"])
        self.signal = sp.alignment_signal(self.signal, size=self.params["signal_length"])
        self.signal = self.signal.to_numpy()[:, 1:]
        self.signal = self.signal.reshape(-1, self.signal.shape[0], self.signal.shape[1]).transpose(0, 2, 1)
        self.logger.PrintLog(LogLevel.Info, "Finish signal preprocess")

    def load_models(self):
        self.logger.PrintLog(LogLevel.Info, "Start loading models")
        models = [m for m in glob.glob(os.path.join(self.base_folder, 'Models', 'VirtualSensors_models',
                                                    self.mechanism + '*.pth'))]
        sensor_names = [''.join(os.path.split(m)[-1].split('_')[1:5])[:-4] for m in models]
        sensor_names = self.sensors_translation(sensor_names)
        assert len(models) == len(sensor_names), "Number of the sensor names should be equal to the number of models"
        self.models_list = zip(models, sensor_names)
        self.dummies = set([i[1] for i in sensor_names])
        if self.SideRight:
            self.dummies = set(self.SideRight.values())
        self.logger.PrintLog(LogLevel.Info, "Models were loaded")

    def sensors_translation(self, sensor_names):
        body_parts_dict = self.params["body_parts_dict"]
        sens_dict = self.params["sens_dict"]
        new_sensors = []
        for s in sensor_names:
            for b in body_parts_dict.keys():
                if b in s:
                    s = s.replace(b, body_parts_dict[b])
                    break
            for sens in sens_dict.keys():
                if sens in s:
                    s = s.replace(sens, sens_dict[sens])
                    break
            new_sensors.append(s)
        return new_sensors

    def predict(self):
        self.logger.PrintLog(LogLevel.Info, "Start Virtual sensors predictions")
        self.vs_df = dict()
        for i in self.dummies:
            self.vs_df["occ_" + i] = pd.DataFrame()
        self.net.eval()
        self.net_hip.eval()
        input = torch.from_numpy(self.signal).to(self.device).float()
        for m, name in self.models_list:
            dummy = name[1]
            if self.SideRight:
                dummy = self.SideRight[dummy]
            occ = "occ_" + dummy
            if "HipVector" not in name:
                self.net.load_state_dict(torch.load(m, map_location=lambda storage, loc: storage))
                prediction = self.net(input)
                output = prediction.data.cpu().numpy()
                self.vs_df[occ][name[2:]] = np.squeeze(output)
            else:
                self.net_hip.load_state_dict(torch.load(m, map_location=lambda storage, loc: storage))
                prediction = self.net_hip(input)
                output1, output2 = [pred.data.cpu().numpy() for pred in prediction]
                self.vs_df[occ][name[2:]] = np.squeeze(output1)
                self.vs_df[occ]["BRIC"] = np.squeeze(output2)
        self.vs_df = {k: v.to_dict('list') for k, v in self.vs_df.items()}
        self.logger.PrintLog(LogLevel.Info, "Virtual sensors were predicted")

    def run(self):
        try:
            self.logger.PrintLog(LogLevel.Info, "VirtualSensors: run predictions")
            self.preprocess()
            self.get_net()
            self.load_models()
            self.predict()
            return self.vs_df
        except Exception as e:
            self.logger.PrintLog(LogLevel.Exception, f"Exception was raised: {e}")
            self.logger.PrintLog(LogLevel.Exception, str(traceback.format_exc()))
            raise e

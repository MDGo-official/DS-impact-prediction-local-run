
class InjuryLevel:
    def __init__(self, base_folder, signal, calib_info_obj, crash_info_obj, Offset):
        self.base_folder = base_folder
        self.signal = signal
        self.op_matrix = calib_info_obj["OperationalMat"]
        self.axes_orientation = calib_info_obj["AxesOrientation"]
        self.mechanism = crash_info_obj["mechanism"]
        self.theta = crash_info_obj["theta"]
        self.DV = crash_info_obj["DV"]

    def run(self):
        """
        :return: {0,1,2,....} [Int]
        """
        return 0

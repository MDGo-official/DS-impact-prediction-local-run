
class MultiCrash:
    def __init__(self, base_folder, signal, calib_info_obj, OffSet):
        self.base_folder = base_folder
        self.signal = signal
        self.op_matrix = calib_info_obj["OperationalMat"]
        self.axes_orientation = calib_info_obj["AxesOrientation"]
        self.calib_status = calib_info_obj["Status"]

    def run(self):
        """
        :return: [signal1, signal2....] FULL signals ~200*6 in size not rotated
        """
        return [self.signal]

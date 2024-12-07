import os
import numpy as np
import pandas as pd
from SignalProcessing import SignalProcessing as sp
from Utils import DSLogger, LogLevel

class CrashMechanism:
    """NOTE: if the highest peak of the provided signal falls at the end of the 5 seconds
    it's always going to return rear, rare edge case where the signal would have to remain above the thr for 5 sec"""

    @classmethod
    def get_mechanism(cls, df, config):
        fs = config["sample_rate"]
        cutoff_min = config["mechanism"]["cutoff_min"]
        cutoff_max = config["mechanism"]["cutoff_max"]
        cutoff_steps = config["mechanism"]["cutoff_steps"]
        sensors = config["mechanism"]["sensors"]
        log_agreement_perc_thr = config["mechanism"]["log_agreement_perc_thr"]

        angles_per_lowpass_deg = cls.angles_per_lowpass(df, fs, cutoff_min, cutoff_max, cutoff_steps, sensors)
        mechanism, agreed_perc = cls.mechanism_voter(angles_per_lowpass_deg)

        mean_angle = cls.mean_angle(angles_per_lowpass_deg)

        if agreed_perc <= log_agreement_perc_thr:
            DSLogger("crash_det").PrintLog(LogLevel.Warning,
                                           "agreed percentage for mechanism lower than {}: {}, angles:{}".format(
                                               log_agreement_perc_thr, agreed_perc, angles_per_lowpass_deg))

        return mechanism, mean_angle

    @classmethod
    def angles_per_lowpass(cls, df, fs, cutoff_min, cutoff_max, cutoff_steps, sensors=['Acc_X', 'Acc_Y']):
        """
        :param df: pandas dataframe
        :param fs: vehicle data frequency
        :param cutoff_range: (min, max, steps) for used cutoff of lowpass filter
        :param sensors: list of vehicle sensors
        :return: list of positive angles between 0 and 360 degrees
        """

        # explicitly save a copy before making changes to df to be sure
        df = df.copy(deep=True)
        dft = sp.insert_time_column(df.loc[:, sensors], sigFs=int(fs))

        angles = []
        for cutoff in range(cutoff_min, cutoff_max, cutoff_steps):
            # smooth_dataset_filter returns a deep copy, so the lowpass is always on the original dft
            dfs = sp.smooth_dataset_filter(dft, cutoff)
            norm = np.linalg.norm(dfs.loc[:, sensors], axis=1)
            max_norm_ind = np.argmax(norm)

            # arctan2 returns angles in rad between [-pi ; pi]
            thetas_win_rad = np.arctan2(dfs[sensors[1]].values, dfs[sensors[0]].values)  # could do it just for max
            angle_rad = thetas_win_rad[
                max_norm_ind]  # rads are needed for the mean at the end, degrees are needed for mech pred

            # convert angle to positive angle between [0 ; 360] degrees
            angle_deg = cls.rad_to_pos_deg(angle_rad)

            angles.append(angle_deg)

        return np.array(angles)

    @classmethod
    def mechanism_voter(cls, angles_list):
        """
        :param angles_list: receives list of positive angles
        :return: mechanism_pred, agreement_perc
        """
        mech_count = {}
        for theta in angles_list:
            mech = cls.mechanism_classifier(theta)
            if mech in mech_count.keys():
                mech_count[mech] += 1
            else:
                mech_count[mech] = 1
        mech_ranked = [(k, v) for k, v in sorted(mech_count.items(), key=lambda item: item[1], reverse=True)]
        return mech_ranked[0][0], round(mech_ranked[0][1] / len(angles_list), 3)

    @staticmethod
    def rad_to_pos_deg(angle_rad):
        """
        :param angle_rad: receives angle in rad
        :return: angle in deg between 0 and 360
        """
        # convert angle to degrees
        angle_deg = angle_rad * 180 / np.pi

        # convert to positive angle between [0 ; 360] degrees
        if angle_deg < 0:
            angle_deg = angle_deg + 360
        return angle_deg

    @classmethod
    def mean_angle(cls, angles_deg):
        """
        :param angles_deg: list of angles in degrees
        :return: degree between [0; 360]
        """

        if not isinstance(angles_deg, np.ndarray):
            angles_deg = np.array(angles_deg)

        angles_rad = angles_deg/180 * np.pi

        # take mean using cartesian form on angles in rad
        x_ax = np.sum([np.cos(angle) for angle in angles_rad]) / len(angles_rad)
        y_ax = np.sum([np.sin(angle) for angle in angles_rad]) / len(angles_rad)

        theta_rad = np.arctan2(y_ax, x_ax)
        theta_deg = cls.rad_to_pos_deg(theta_rad)
        return theta_deg

    @classmethod
    def mechanism_classifier(cls, theta):
        """
        Uses angle theta of collision to calculate the collision mechanism
        :param theta: impact angle
        :return: collision mechanism
        """
        if theta >= 315 or theta < 45:
            return 'Rear'
        elif theta >= 45 and theta < 135:
            return 'SideLeft' #left
        elif theta >= 135 and theta < 160:
            return 'Frontal'
        elif theta >= 160 and theta < 190:
            return 'Frontal'
        elif theta >= 190 and theta < 230:
            return 'Frontal'
        elif theta >= 230 and theta < 315:
            return 'SideRight'  # right'
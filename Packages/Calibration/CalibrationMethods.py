import json
import pathlib
import sys
import os

import numpy as np
import pandas as pd
import torch

from Utils import IO, LogLevel, DSLogger

class Methods:
    
    @staticmethod
    def in_circle(psi_z):
        if psi_z < -40:
            return psi_z + 360
        return psi_z

    
    @staticmethod
    def find_angles_from_rotmat(rotmat,windshield_angle=27):
        """
        assuming oreder 'Y','X','Z', and -pi/2 < phi_x < pi/2  the function 
        returns [phi_x, theta_y, psi_z]  
        """
        asin = lambda x: np.rad2deg(np.arcsin(x))
        atan = lambda x,y: np.rad2deg(np.arctan2(x,y))
        
        phi_x = asin(-rotmat[1][2])
        theta_y = atan(rotmat[0][2],rotmat[2][2])
        psi_z = Methods.in_circle(atan(rotmat[1][0],rotmat[1][1]))
        
        return [round(phi_x,2), round(theta_y,2), round(psi_z,2)]

    @staticmethod
    def calc_rotmat(angles):
        """
        calc rotation matrix by 'Y','X','Z' from https://www.geometrictools.com/Documentation/EulerAngles.pdf
        But, the order of moving is 'Z','X','Y'
        """
        cos = lambda x: np.cos(np.deg2rad(x))
        sin = lambda x: np.sin(np.deg2rad(x))

        phi_x, theta_y, psi_z = angles
        rotmat = np.array(
            [[cos(theta_y)*cos(psi_z)+sin(phi_x)*sin(theta_y)*sin(psi_z), -1*cos(theta_y)*sin(psi_z)+cos(psi_z)*sin(phi_x)*sin(theta_y),  cos(phi_x)*sin(theta_y)  ],
            [cos(phi_x)*sin(psi_z)                                      ,  cos(phi_x)*cos(psi_z)                                       , -1*sin(phi_x)             ],
            [cos(theta_y)*sin(phi_x)*sin(psi_z)-cos(psi_z)*sin(theta_y) ,  cos(theta_y)*cos(psi_z)*sin(phi_x)+sin(theta_y)*sin(psi_z)  ,  cos(phi_x)*cos(theta_y)]])
        return rotmat
    
    @staticmethod
    def calc_r0(a0):
        """
        consider no rotation about z axis - find rotation matrix from sensor to car

        Returns [phi_x, theta_y, psi_z] 
        """
        z_axis = a0/np.linalg.norm(a0)
        y_axis = [0, -z_axis[2], z_axis[1]] # perpendicular:=> a0*b0+a1*b1+a2*b2 = 0 
        y_axis = y_axis/np.linalg.norm(y_axis) 
        x_axis = np.cross(y_axis,z_axis)
        x_axis = x_axis/np.linalg.norm(x_axis)
        r0 = np.array([
            [x_axis[0],x_axis[1],x_axis[2]],
            [y_axis[0],y_axis[1],y_axis[2]],
            [z_axis[0],z_axis[1],z_axis[2]]
        ])
        return r0
    
    @staticmethod
    def find_ax(signal, r0, configs):
        """
        Find a window where the car is driving straight (breaking or accelerating)
        """  
        # configs
        min_wind = configs['ax_min_win_size']
        start_index = configs['num_samples_in_register']
        min_thresh = configs['ax_min_threshold']
        max_thresh = configs['ax_max_threshold']
        gyro_noise_tolerance = configs['ax_gyro_noise_tolerance']
        ax_wind_inds = None
        ax = None
        
        # signal
        acc_signal = signal[configs['axes'][:3]]    
        if type(r0) == list:
            r0 = np.array(r0)
        aligned_acc = acc_signal.iloc[start_index:].values @ r0.T
        acc_norm_xy = np.linalg.norm(aligned_acc[:,:2], axis=1)
        gyro = signal[configs['axes'][3:]].iloc[start_index:].values
        for i in range(len(acc_norm_xy) - min_wind):
            # acc
            curr_acc = acc_norm_xy[i:i+min_wind]
            if not (((curr_acc) > min_thresh).all() and ((curr_acc) < max_thresh).all()):
                continue
            # gyro
            curr_gyro = gyro[i:i+min_wind]
            if not ((abs(curr_gyro) <= gyro_noise_tolerance).all()).all(): 
                continue
            # find full window inds
            acc_remain = acc_norm_xy[i:]
            gyro_remain = abs(gyro[i:])
            inds = np.arange(acc_remain.shape[0])
            curr_last_wind_ind = inds[(acc_remain > max_thresh) | (acc_remain <= min_thresh) | np.any(gyro_remain > gyro_noise_tolerance, axis=1)]
            curr_last_wind_ind = curr_last_wind_ind[0] if len(curr_last_wind_ind)>0 else len(acc_remain)-1
            # check if biggest sofar
            if (ax_wind_inds is not None) and (ax_wind_inds[1]-ax_wind_inds[0]) > curr_last_wind_ind:
                continue
            # chosen window - can get here more than once
            original_index = i + start_index
            ax_wind_inds = [original_index, curr_last_wind_ind + original_index]
            ax = np.mean(acc_signal.iloc[ax_wind_inds[0]:ax_wind_inds[1]],axis=0).tolist() 
        return ax, ax_wind_inds
    
    @staticmethod
    def is_acc(signal, ax_wind_inds, configs):
        z_values = signal[configs['axes'][2]].values
        start, end = ax_wind_inds
        z_ax = np.mean(z_values[start:end])
        z_out_of_ax = np.mean(np.concatenate((z_values[:start],z_values[end:]),axis=None))
        if z_ax < z_out_of_ax:
            return False
        return True
    
    @staticmethod
    def calc_psi_z(a0, ax, is_acc):
        atan = lambda x,y: np.rad2deg(np.arctan2(x,y))        
        
        r0 = Methods.calc_r0(a0)
        ax_aligned = r0 @ ax
        # deceleration (breaking), the direction of the force is in the opposite direction of the driving
        if not is_acc: 
            return Methods.in_circle(atan(ax_aligned[1],-ax_aligned[0]))
        else: # acceleration, the direction of the force is the same as the direction of the driving
            return Methods.in_circle(atan(-ax_aligned[1],ax_aligned[0]))
        
    @staticmethod
    def find_plane_rotmat(a0, psi_z):
        """
        find full rotation matrix

        Returns [phi_x, theta_y, psi_z] 
        """
        cos = lambda x: np.cos(np.deg2rad(x))
        sin = lambda x: np.sin(np.deg2rad(x))
        
        r0 = Methods.calc_r0(a0)
        rx_rotmat = np.array([
            [cos(psi_z),-sin(psi_z), 0], 
            [sin(psi_z), cos(psi_z), 0], 
            [0         , 0         , 1]])
        return rx_rotmat @ r0
        
    @staticmethod
    def clean_outlayers_a0(a0_list, configs):
        """
        Parameters took from Offset Stable Parameners presentation and research
        """
        a0_clean_list = []
        a0_med = np.median(a0_list, axis=0)
        for a0 in a0_list:
            if not np.isclose(a0[0],a0_med[0],atol=configs['a0x_threshold']/2):
                continue
            if not np.isclose(a0[1],a0_med[1],atol=configs['a0y_threshold']/2):
                continue
            if not np.isclose(a0[2],a0_med[2],atol=configs['a0z_threshold']/2):
                continue
            a0_clean_list.append(a0)
        return a0_clean_list

    @staticmethod
    def clean_outlayers_psi_z(psi_z_list, configs):
        if type(psi_z_list) is list:
            psi_z_list = np.array(psi_z_list)
        psi_z_med = np.median(psi_z_list)
        psi_z_med_rep = np.repeat(psi_z_med,len(psi_z_list))#.reshape(len(ax_mean),len(psi_z_list)).transpose()
        ax_clean_list = psi_z_list[np.isclose(psi_z_list,psi_z_med_rep,atol=configs['psi_z_threshold'])]
        return ax_clean_list
import numpy as np
import math
from MedicalCalculation.Common import FormulaResult
import MedicalCalculation.MedicalBasicFormulas as mbf


# ---------------------------------------------- Head -----------------------------------------------------#

# ---------- Head Injury Criteria - Front, Rear, Side ----------#  # abbreviation [HIC]
def calc_hic(vs_df, fs, win_time=0.015):
    # data - sqrt(head_accx^2 + head_accy^2 + head_accz^2)
    # [fs] = [Hz]
    # win_time = [sec]
    # print(type(vs_df))

    for sensor in ["HEAD_ACX", "HEAD_ACY", "HEAD_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    data = (vs_df["HEAD_ACX"].values ** 2 + vs_df["HEAD_ACY"].values ** 2 + vs_df["HEAD_ACZ"].values ** 2) ** 0.5

    hic = 0
    # t_start = 0
    # t_end = 0
    win = int(win_time * fs)

    for i_start in range(len(data) - win):
        # rng = range(i_start)
        for i_end in range(i_start + 1, i_start + win + 1):
            tmp1 = abs(1 / (i_end - i_start) * sum(data[i_start:i_end])) ** 2.5
            tmp = tmp1 * (i_end - i_start) / fs
            if tmp > hic:
                hic = tmp
                # t_start = i_start/fs
                # t_end = i_end/fs

    if hic < 1:
        return FormulaResult(value=int(hic))

    # risk functions
    p1ais = round(100 * (1 - math.exp(-(hic / 671) ** 4.34)))
    p2ais = round(100 / (1 + math.exp(5.2778 - 0.0064 * hic)))
    p3ais = round(100 / (1 + math.exp((3.39 + 200 / hic) - 0.00372 * hic)))
    p4ais = round(100 / (1 + math.exp((4.9 + 200 / hic) - 0.00351*hic)))
    p5ais = round(100 / (1 + math.exp((7.82 + 200 / hic) - 0.00429*hic)))
    p6ais = round(100 / (1 + math.exp((12.24 + 200 / hic) - 0.00565*hic)))
    hic = int(hic)

    if 300 <= hic < 500:
        limit = 1
    elif hic >= 500:
        limit = 2
    else:
        limit = 0

    return FormulaResult(value=hic, ais1p=p1ais, ais2p=p2ais, ais3p=p3ais, ais4p=p4ais, ais5p=p5ais, ais6p=p6ais, limit=limit)


# ---------- Head Impact Factor - Front, Rear, Side ----------#   # abbreviation [HIP]
def head_impact_power(vs_df, fs, C=4.5):
    # df_head - data frame with HEAD_ACX, HEAD_ACY, HEAD_ACZ, HEAD_AVX, HEAD_AVY, HEAD_AVZ
    # fs = [Hz]
    # C = []

    if "HipVector" in vs_df:
        hip_vec = vs_df["HipVector"].to_numpy().astype('float')
        hip = mbf.calc_3ms(hip_vec, fs)

        #p2ais = round(100 / (1 + math.exp(4.682 - 0.003655 * hip)))
        #p3ais = round(100 / (1 + math.exp(4.8737 - 0.0722 * hip)))

    else:
        for sensor in ["HEAD_ACX", "HEAD_ACY", "HEAD_ACZ", "HEAD_AVX", "HEAD_AVY", "HEAD_AVZ"]:
            if not sensor in vs_df.keys():
                return None

        acx = vs_df["HEAD_ACX"].tolist()
        acy = vs_df["HEAD_ACY"].tolist()
        acz = vs_df["HEAD_ACZ"].tolist()
        avx = vs_df["HEAD_AVX"].tolist()
        avy = vs_df["HEAD_AVY"].tolist()
        avz = vs_df["HEAD_AVZ"].tolist()

        ax = np.asarray(acx) * 9.8  # linear acceleration x [m/sec^2]
        ay = np.asarray(acy) * 9.8  # linear acceleration y [m/sec^2]
        az = np.asarray(acz) * 9.8  # linear acceleration z

        alpha_x = mbf.ece_r_94_diff(avx * math.pi / 180, fs)  # angular acceleration x [rad/sec^2]
        alpha_y = mbf.ece_r_94_diff(avy * math.pi / 180, fs)  # angular acceleration y [rad/sec^2]
        alpha_z = mbf.ece_r_94_diff(avz * math.pi / 180, fs)  # angular acceleration z [rad/sec^2]

        # append 0 to the end of alpha
        alpha_x = np.append(alpha_x, 0)
        alpha_y = np.append(alpha_y, 0)
        alpha_z = np.append(alpha_z, 0)

        sax = np.cumsum(ax) / fs  # integral over linear acceleration x [m/sec]
        say = np.cumsum(ay) / fs  # integral over linear acceleration y [m/sec]
        saz = np.cumsum(az) / fs  # integral over linear acceleration z [m/sec]

        salpha_x = np.cumsum(alpha_x) / fs  # integral over angular acceleration x [rad/sec]
        salpha_y = np.cumsum(alpha_y) / fs  # integral over angular acceleration y [rad/sec]
        salpha_z = np.cumsum(alpha_z) / fs  # integral over angular acceleration z [rad/sec]

        C4 = 0.016
        C5 = 0.024
        C6 = 0.022

        hip_vec = C * ax * sax + C * ay * say + C * az * saz + C4 * alpha_x * salpha_x + C5 * alpha_y * salpha_y + C6 * alpha_z * salpha_z
        hip = mbf.calc_3ms(hip_vec.to_numpy().astype('float'), fs) / 1000

        #p2ais = round(100 / (1 + math.exp(4.682 - 0.003655 * hip)))

    hip = int(hip)

    if 12 <= hip < 20:
        limit = 1
    elif 20 <= hip < 35:
        limit = 2
    elif hip >= 35:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=hip, limit=limit)

# ---------- Head A3ms - Front, Rear, Side ----------#            # abbreviation [HA3ms]
def head_a3ms(vs_df, fs):
    for sensor in ["HEAD_ACX", "HEAD_ACY", "HEAD_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    data = [math.sqrt(a ** 2 + b ** 2 + c ** 2) for a, b, c in
            zip(vs_df['HEAD_ACX'].tolist(), vs_df['HEAD_ACY'].tolist(), vs_df['HEAD_ACZ'].tolist())]

    #This is better way to calculate norm (sqrt)
    #data = np.linalg.norm(vs_df['HEAD_ACX'], vs_df['HEAD_ACY'], vs_df['HEAD_ACZ'], axis=1)

    a3ms = mbf.calc_3ms(np.array(data).astype('float'), fs)
    if a3ms <= 50:
        limit = 0
    elif 50 < a3ms <= 65:
        limit = 1
    elif 65 < a3ms < 85:
        limit = 2
    else:
        limit = 3

    return FormulaResult(value=a3ms, limit=limit)
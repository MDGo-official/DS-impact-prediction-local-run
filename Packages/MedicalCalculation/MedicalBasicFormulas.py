import numpy as np


# -------------------------------------- Max Acceleration in 3ms ---------------------------------------#

def calc_3ms(data, fs):
    data = np.asarray(data)
    a3ms = 0
    win_size = int(round(0.003 * fs))
    for i in range(len(data) - win_size):
        a = min(abs(data[i:i + win_size]))
        if a > a3ms:
            a3ms = a

    return a3ms

# -------------------------------------------- Max force  -----------------------------------------------#

def ece_r_94_diff(data, fs):
    diff1 = [a - b for a, b in zip(data[3:-1], data[1:-3])]
    diff2 = [a - b for a, b in zip(data[4:], data[:-4])]
    Vt = [(8 * a - b) / 12 * fs for a, b in zip(diff1, diff2)]

    return Vt

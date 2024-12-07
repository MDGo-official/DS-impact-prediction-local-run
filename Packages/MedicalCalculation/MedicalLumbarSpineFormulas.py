import numpy as np
import math
from MedicalCalculation.Common import FormulaResult
import MedicalCalculation.MedicalBasicFormulas as mbf


# Not Used/Tested ------------------------------------- Lumbar spine --------------------------------- Not Used/Tested #

# ---------- (AC) Resultant spinal acceleration - Front ----------#

def resultant_spinal_acceleration(vs_df, fs):
    for sensor in ["CHST_ACX", "CHST_ACY", "CHST_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    acc = [math.sqrt(a ** 2 + b ** 2 + c ** 2) for a, b, c in
           zip(vs_df['CHST_ACX'].tolist(), vs_df['CHST_ACY'].tolist(), vs_df['CHST_ACZ'].tolist())]
    ac = mbf.calc_3ms(np.array(acc).astype('float'), fs)
    p2ais = round(100 / (1 + math.exp(1.234 - 0.0576 * ac)))
    p3ais = round(100 / (1 + math.exp(3.1493 - 0.063 * ac)))
    p4ais = round(100 / (1 + math.exp(4.3425 - 0.063 * ac)))
    p5ais = round(100 / (1 + math.exp(8.7652 - 0.0659 * ac)))

    return FormulaResult(ais2p=p2ais, ais3p=p3ais, ais4p=p4ais , ais5p=p5ais)


# --------- Upper spine acceleration (T1) - Side ---------# ()

def upper_spine_acceleration(vs_df, fs, age=45):
    for sensor in ["SPINLO_ACY"]:
        if not sensor in vs_df.keys():
            return None

    t1_acy = mbf.calc_3ms(vs_df["SPINLO_ACY"].to_numpy().astype('float'), fs)
    p3ais = round(100 / (1 + math.exp(6.4606 - 0.0544 * age - 0.061 * t1_acy)))
    p4ais = round(100 / (1 + math.exp(7.9103 - 0.0544 * age - 0.061 * t1_acy)))

    return FormulaResult(ais3p=p3ais, ais4p=p4ais)


# --------- Spine Shear Force: [Spine Force] = [kN] ----------#  (---)
def spine_shear_force(vs_df, fs):
    if not "F(x)" in vs_df.keys():  # TODO: Change sensor name
        return None

    spineShearForce = np.max(vs_df["F(x)"]) / 1000  # [kN] # TODO: Change sensor name

    if 0.43 <= spineShearForce <= 0.6:
        shearForceFlag = 1
    elif 0.6 < spineShearForce:
        shearForceFlag = 3
    else:
        shearForceFlag = 0

    return FormulaResult(value=spineShearForce, limit=shearForceFlag)

# ---------- Spine Tension Force: [Spine Tension] = [kN] ----------#  (---)
def spine_tension_force(vs_df, fs):
    if not "FOZ" in vs_df.keys():  # TODO: Change sensor name
        return None

    spineTensionForce = np.max(vs_df["FOZ"]) / 1000  # [kN] # TODO: Change sensor name

    if 2 <= spineTensionForce <= 4:
        tensionFlag = 1
    elif 4 < spineTensionForce <= 5:
        tensionFlag = 2
    elif 5 < spineTensionForce:
        tensionFlag = 3
    else:
        tensionFlag = 0

    return FormulaResult(value=spineTensionForce, limit=tensionFlag)

# ---------- Spine Compression Force: [Spine Compression] = [kN] ----------#  (---)
def spine_compression_force(vs_df, fs):
    if not "FOZ" in vs_df.keys():  # TODO: Change sensor name
        return None

    spineCompressionForce = np.max(vs_df["FOZ"]) / 1000  # [kN] # TODO: Change sensor name

    if 2 <= spineCompressionForce <= 4:
        compressionFlag = 1
    elif 4 < spineCompressionForce <= 5:
        compressionFlag = 2
    elif 5 < spineCompressionForce:
        compressionFlag = 3
    else:
        compressionFlag = 0

    return FormulaResult(value=spineCompressionForce, limit=compressionFlag)

# ---------- Spine Extention Force: [Spine Extention] = [Nm] ----------#  (---)
def spine_extention_force(vs_df, fs):
    # vs_df - data frame with all virtual sensors
    # spineExtensionForce = [Nm]
    if not "MOY" in vs_df.keys(): # TODO: Change sensor name
        return None

    spineExtensionForce = np.max(vs_df["MOY"])  # [Nm] # TODO: Change sensor name

    if 6 <= spineExtensionForce <= 47:
        extensionFlag = 1
    elif 47 < spineExtensionForce <= 88:
        extensionFlag = 2
    elif 88 < spineExtensionForce <= 165:
        extensionFlag = 2.5
    elif 165 < spineExtensionForce <= 237:
        extensionFlag = 3
    elif 237 < spineExtensionForce:
        extensionFlag = 3.5
    else:
        extensionFlag = 0

    return FormulaResult(value=spineExtensionForce, limit=extensionFlag)

# ---------- Spine Flexion Force: [Spine Flexion] = [Nm] ----------#  (---)
def spine_flexion_force(vs_df, fs):
    # vs_df - data frame with all virtual sensors
    # spineExtensionForce = [Nm]
    if not "MOY" in vs_df.keys(): # TODO: Change sensor name
        return None

    spineFlexionForce = np.max(vs_df["MOY"])  # [Nm] # TODO: Change sensor name

    if 10 <= spineFlexionForce <= 47:
        flexionFlag = 1
    elif 47 < spineFlexionForce <= 88:
        flexionFlag = 2
    elif 88 < spineFlexionForce <= 165:
        flexionFlag = 2.5
    elif 165 < spineFlexionForce <= 237:
        flexionFlag = 3
    elif 237 < spineFlexionForce:
        flexionFlag = 3.5
    else:
        flexionFlag = 0

    return FormulaResult(value=spineFlexionForce, limit=flexionFlag)

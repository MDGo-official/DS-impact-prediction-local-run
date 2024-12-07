import math
from MedicalCalculation.Common import FormulaResult
import MedicalCalculation.MedicalBasicFormulas as mbf


# ------------------------------------------------- Femur -------------------------------------------------#

# ----------- sensitive_femur axial force - Front, Rear, [axial_force] = [KN] ----------##[abbreviation: PAFFrontalSens]
def femur_axial_force_sensitive(vs_df, fs):         # not yet trained
    for sensor in ["FEMRLE_FOZ", 'FEMRRI_FOZ']:
        if not sensor in vs_df.keys():
            return None

    axial_forceL = mbf.calc_3ms(vs_df['FEMRLE_FOZ'].to_numpy().astype('float'), fs) / 1000
    axial_forceR = mbf.calc_3ms(vs_df['FEMRRI_FOZ'].to_numpy().astype('float'), fs) / 1000
    axial_force = max(axial_forceL, axial_forceR)

    p2ais = round(100 / (1 + math.exp(5.7949 - 0.3126 * axial_force)))
    p3ais = round(100 / (1 + math.exp(4.9795 - 0.326 * axial_force)))

    if 2.1 <= axial_force < 3.3:
        limit = 1
    elif 3.3 <= axial_force < 7.1:
        limit = 2
    elif 7.1 <= axial_force:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=axial_force, ais2p=p2ais, ais3p=p3ais, limit=limit)

# ----------- femur_axial_force - Front, Rear, [axial_force] = [KN] -----------#          #[abbreviation: PAFFrontal]
def femur_axial_force(vs_df, fs):  # Non-sensitive version  # not yet trained
    for sensor in ["FEMRLE_FOZ", 'FEMRRI_FOZ']:
        if not sensor in vs_df.keys():
            return None

    axial_forceL = mbf.calc_3ms(vs_df['FEMRLE_FOZ'].to_numpy().astype('float'), fs) / 1000
    axial_forceR = mbf.calc_3ms(vs_df['FEMRRI_FOZ'].to_numpy().astype('float'), fs) / 1000
    axial_force = max(axial_forceL, axial_forceR)

    p2ais = round(100 / (1 + math.exp(5.7949 - 0.5196 * axial_force)))

    if 2.6 <= axial_force <= 6.2:
        limit = 1
    elif 6.2 < axial_force <= 8.9:
        limit = 2
    elif 8.9 < axial_force:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=axial_force, ais2p=p2ais, limit=limit)

'''
# ----------- sensitive_femur_bending_moment - side, [lateral_bending_moment] = [Nm] -----------#
def sensitive_femur_bending_moment(vs_df, fs): #sensitive version #[abbreviation: Bending_moment]
    for sensor in ["FEMRLE_MOY", 'FEMRRI_MOY']:
        if not sensor in vs_df.keys():
            return None

    bending_momentL = mbf.calc_3ms(vs_df['FEMRLE_MOY'].to_numpy().astype('float'), fs) / 1000
    bending_momentR = mbf.calc_3ms(vs_df['FEMRLE_MOY'].to_numpy().astype('float'), fs) / 1000
    bending_moment = max(bending_momentL, bending_momentR)

    if 182 < bending_moment <= 220:
        limit = 1
    elif 220 < bending_moment <= 356:
        limit = 2
    elif 356 < bending_moment:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=bending_moment, limit=limit)

# ----------- femur_bending_moment - side, [lateral_bending_moment] = [Nm] -----------#
def femur_bending_moment(vs_df, fs): #Non-sensitive version #[abbreviation: Bending_moment]
    for sensor in ["FEMRLE_MOY", 'FEMRRI_MOY']:
        if not sensor in vs_df.keys():
            return None

    bending_momentL = mbf.calc_3ms(vs_df['FEMRLE_MOY'].to_numpy().astype('float'), fs) / 1000
    bending_momentR = mbf.calc_3ms(vs_df['FEMRLE_MOY'].to_numpy().astype('float'), fs) / 1000
    bending_moment = max(bending_momentL, bending_momentR)

    if 254 < bending_moment <= 356:
        limit = 1
    elif 356 < bending_moment <= 447:
        limit = 2
    elif 447 < bending_moment:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=bending_moment, limit=limit)

# ----------- femur_lateral_compression_force - side, [lateral_force] = [kN] -----------#
def femur_lateral_compression_force(vs_df, fs): #Non-sensitive version #[abbreviation: lateral_compression]
    for sensor in ["FEMRLE_FY", 'FEMRRI_FY']: # TODO: Change sensor name
        if not sensor in vs_df.keys():
            return None

    compression_forceL = mbf.calc_3ms(vs_df['FEMRLE_FY'].to_numpy().astype('float'), fs) / 1000 # TODO: Change sensor name
    compression_forceR = mbf.calc_3ms(vs_df['FEMRLE_FY'].to_numpy().astype('float'), fs) / 1000 # TODO: Change sensor name
    compression_force = max(compression_forceL, compression_forceR)

    if 2.6 <= compression_force <= 6.2:
        limit = 1
    elif 6.2 < compression_force <= 8.9:
        limit = 2
    elif 8.9 < compression_force:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=compression_force, limit=limit)


# ----------- sensitive_femur_lateral_compression_force - side, [lateral_force] = [kN] -----------#
def sensitive_femur_lateral_compression_force(vs_df, fs):  # Non-sensitive version #[abbreviation: lateral_compression]
    for sensor in ["FEMRLE_FY", 'FEMRRI_FY']:  # TODO: Change sensor name
        if not sensor in vs_df.keys():
            return None

    compression_forceL = mbf.calc_3ms(vs_df['FEMRLE_FY'].to_numpy().astype('float'), fs) / 1000  # TODO: Change sensor name
    compression_forceR = mbf.calc_3ms(vs_df['FEMRLE_FY'].to_numpy().astype('float'), fs) / 1000  # TODO: Change sensor name
    compression_force = max(compression_forceL, compression_forceR)

    if 2.6 < compression_force <= 3.4:
        limit = 1
    elif 3.4 < compression_force <= 7.6:
        limit = 2
    elif 7.6 < compression_force:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=compression_force, limit=limit)

# ----------- Femur_Acetabulum_load - multi, [Acetabulum_force] = [kN] -----------#
def femur_Acetabulum_load_force(vs_df, fs):  #[abbreviation: Acetabulum_load - FR or FAR]
    for sensor in ["FEMRLE_FY", 'FEMRRI_FZ', 'FEMRRI_FX']:  # TODO: Change sensor name
        if not sensor in vs_df.keys():
            return None

    # This is better way to calculate norm (sqrt of sum of powers)
    fr = np.linalg.norm(vs_df[['FEMRLE_FY', 'FEMRRI_FZ', 'FEMRRI_FX']], axis=1)   # TODO: Change sensor name

    pais2 = norm.cdf(np.log(fr * 1.429 - 1.6058) / 0.2339)
    pais3 = norm.cdf(np.log(fr / 0.72 - 1.6526) / 0.1991)

    if 4 <= fr <= 4.8:
        limit = 1
    elif 4.8 < fr <= 5.6:
        limit = 2
    elif 5.6 < fr:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=fr, ais2p=pais2, ais3p=pais3, limit=limit)

'''
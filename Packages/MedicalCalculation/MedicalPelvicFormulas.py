import math
from MedicalCalculation.Common import FormulaResult
import MedicalCalculation.MedicalBasicFormulas as mbf

# ------------------------------------------------ Pelvic ---------------------------------------------------#

# ---------- (Pubic F) Maximal lateral pubic symphysis force, [max_pelv_fy] = [N] -----------## [abbreviation: PSPFSide]
def maximal_lateral_pubic_symphysis_force(vs_df, fs, age=45):    # not yet trained
    for sensor in ["PELVUP_FOY"]:
        if not sensor in vs_df.keys():
            return None

    max_pelv_fy = mbf.calc_3ms(vs_df["PELVUP_FOY"].to_numpy().astype('float'), fs)

    # old formulas
    # p2ais = round(100 / (1 + math.exp(
    #    -1 * (np.log(max_pelv_fy) - (8.77482706 + age * (-0.01385568))) / math.exp(-1.52587836))))
    # p3ais = round(100 / (1 + math.exp(
    #   -1 * (np.log(max_pelv_fy) - (8.70406439 + age * (-0.01163987))) / math.exp(-1.82737827))))
    # p2ais = round(100/(1+math.exp(6.804 - 0.0089*age - 0.0007424*max_pelv_fy)))
    # p3ais = round(100/(1+math.exp(9.7023 - 0.04678*age - 0.0005*max_pelv_fy)))
    # p2ais_dummy = round(100 / (1 + math.exp(6.3055 - 0.00094 * max_pelv_fy)))

    p3ais = round(100 / (1 + math.exp(7.5969 - 0.0011 * max_pelv_fy)))

    # non-sensitive version
    max_pelv_fy = max_pelv_fy / 1000  # [KN]
    if 3 <= max_pelv_fy <= 4.4:
        limit = 1
    elif 4.4 < max_pelv_fy <= 5.6:
        limit = 2
    elif 5.6 < max_pelv_fy:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=max_pelv_fy, ais3p=p3ais, limit=limit)

# ----- (Pubic F) Sensitive_Maximal_lateral_pubic_symphysis_force, [max_pelv_fy] = [N] ---- [abbreviation: PSPFSideSens]
def maximal_lateral_pubic_symphysis_force_sensitive(vs_df, fs):    # not yet trained
    for sensor in ["PELVUP_FOY"]:
        if not sensor in vs_df.keys():
            return None

    max_pelv_fy = mbf.calc_3ms(vs_df["PELVUP_FOY"].to_numpy().astype('float'), fs)

    # sensitive version
    max_pelv_fy = max_pelv_fy / 1000  # [KN]
    if 1.7 <= max_pelv_fy < 2.6:
        limit = 1
    elif 2.6 <= max_pelv_fy < 2.9:
        limit = 2
    elif 2.9 <= max_pelv_fy:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=max_pelv_fy, limit=limit)

# ---------- (Rear Acc) Maximal rear acceleration on pelvic  [acc]=[g]-----------#      # [abbreviation: PelvicRearAcc]
def max_pelvis_acceleration_rear(vs_df, fs):
    for sensor in ["PELVUP_ACX", "PELVUP_ACY", "PELVUP_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    max_pelv_acx = mbf.calc_3ms(vs_df["PELVUP_ACX"].to_numpy().astype('float'), fs)
    max_pelv_acy = mbf.calc_3ms(vs_df["PELVUP_ACY"].to_numpy().astype('float'), fs)
    max_pelv_acz = mbf.calc_3ms(vs_df["PELVUP_ACZ"].to_numpy().astype('float'), fs)

    max_pelv_acc = max(max_pelv_acx, max_pelv_acy, max_pelv_acz)

    if 80 <= max_pelv_acc < 90:
        limit = 1
    elif 90 <= max_pelv_acc:
        limit = 2
    else:
        limit = 0

    # old limits
    """if max_pelv_acc < 80:
        limit = 0
    elif max_pelv_acc >= 80 and max_pelv_acc < 90:
        limit = 2
    elif max_pelv_acc >= 90:
        limit = 3"""

    return FormulaResult(value=max_pelv_acc, limit=limit)

# ---------- (Lateral Acc) Maximal lateral acceleration on pelvic  [acc]=[g]----------- [abbreviation: PelvicSideAcc]
def max_pelvis_acceleration_side(vs_df, fs):
    for sensor in ["LUSP_ACX", "LUSP_ACY", "LUSP_ACZ"]: # This sensors are from the lower spine it can be also "spinelow"
        if not sensor in vs_df.keys():
            return None

    max_pelv_acx = mbf.calc_3ms(vs_df["LUSP_ACX"].to_numpy().astype('float'), fs)
    max_pelv_acy = mbf.calc_3ms(vs_df["LUSP_ACY"].to_numpy().astype('float'), fs)
    max_pelv_acz = mbf.calc_3ms(vs_df["LUSP_ACZ"].to_numpy().astype('float'), fs)

    max_pelv_acc = max(max_pelv_acx, max_pelv_acy, max_pelv_acz)

    if 80 <= max_pelv_acc < 90:
        limit = 1
    elif 90 <= max_pelv_acc:
        limit = 2
    else:
        limit = 0

    # old limits
    """if max_pelv_acc < 80:
        limit = 0
    elif max_pelv_acc >= 80 and max_pelv_acc < 90:
        limit = 2
    elif max_pelv_acc >= 90:
        limit = 3"""

    return FormulaResult(value=max_pelv_acc, limit=limit)

'''
# ---------- (Pubic/iliac Force) frontal_maximal_compression_pubic_symphysis_force, [max_pelv_fx] = [N] -----------#
def frontal_maximal_compression_pubic_symphysis_force(vs_df, fs):
    for sensor in ["PELV_FOX"]:
        if not sensor in vs_df.keys():
            return None

    max_pelv_fx = calc_3ms(vs_df["PELV_FOX"].to_numpy().astype('float'), fs)

    max_pelv_fx = max_pelv_fx / 1000  # [KN]
    if 3 <= max_pelv_fx <= 4.4:
        limit = 1
    elif 4.4 <= max_pelv_fx <= 6:
        limit = 2
    elif 6 < max_pelv_fx:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=max_pelv_fx, limit=limit)

# ---------- (Acetabulum & ilium Force) side_combined_maximal_pelvic_force, [N] -----------#
def side_combined_maximal_pelvic_force(vs_df, fs):
    for sensor in ["?????"]: # TODO: Change sensor name
        if not sensor in vs_df.keys():
            return None

    max_acetabulum_force = calc_3ms(vs_df["????"].to_numpy().astype('float'), fs) # TODO: Change sensor name
    max_ilium_force = calc_3ms(vs_df["????"].to_numpy().astype('float'), fs) # TODO: Change sensor name

    sum_force = max_acetabulum_force + max_ilium_force

    p2ais = round(100 / (1 + math.exp(6.3055 - 0.00094 * sum_force)))

    sum_force = sum_force / 1000  # [KN]
    if 5.1 <= sum_force <= 6.1:
        limit = 1
    elif 6.1 <= sum_force <= 7.1:
        limit = 2
    elif 7.1 < sum_force:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=sum_force, ais2p=p2ais, limit=limit)
'''

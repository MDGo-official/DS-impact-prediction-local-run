import numpy as np
import math
from MedicalCalculation.Common import FormulaResult
import MedicalCalculation.MedicalBasicFormulas as mbf


# -------------------------------------------- Abdominal -------------------------------------------------#
# ---------- Abdomen_peak_total_force_side_v1 - side [non-sensitive] [force]=[N] ---------# #[abbreviation: FmaxSideV1]
def abdomen_peak_total_force_side_v1(vs_df, fs):  # not yet trained
    for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]:
        if not sensor in vs_df.keys():
            return None

    max_force_side = sum([mbf.calc_3ms(vs_df[sensor].to_numpy().astype('float'), fs) for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]])

    p3ais = round(100 / (1 + math.exp(6.04044 - 0.002133 * max_force_side)))
    p4ais = round(100 / (1 + math.exp(9.282 - 0.002133 * max_force_side)))

    if 820 <= max_force_side <= 1500:
        limit = 1
    elif 1500 < max_force_side <= 2300:
        limit = 2
    elif 2300 < max_force_side <= 3800:
        limit = 3
    elif 3800 < max_force_side:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_force_side, ais3p=p3ais, ais4p=p4ais, limit=limit)

# ---------- Abdomen_peak_total_force_side_v2 [non-sensitive] [force]=[N] -----------#     #[abbreviation: FmaxSideV2]
def abdomen_peak_total_force_side_v2(vs_df, fs):   # not yet trained
    for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]:
        if not sensor in vs_df.keys():
            return None

    max_force_side = sum([mbf.calc_3ms(vs_df[sensor].to_numpy().astype('float'), fs) for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]])

    if 1000 <= max_force_side <= 1200:
        limit = 1
    elif 1200 < max_force_side <= 1300:
        limit = 2
    elif 1300 < max_force_side <= 2000:
        limit = 3
    elif 2000 < max_force_side:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_force_side, limit=limit)

# ---------- Abdomen_peak_total_force_side [sensitive]  [force]=[N] -----------#   #[abbreviation: FmaxSideSens]
def abdomen_peak_total_force_side_sensitive(vs_df, fs):    # not yet trained
    for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]:
        if not sensor in vs_df.keys():
            return None

    max_force_side = sum([mbf.calc_3ms(vs_df[sensor].to_numpy().astype('float'), fs) for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]])

    if 1000 <= max_force_side <= 1200:
        limit = 1
    elif 1200 < max_force_side <= 1300:
        limit = 2
    elif 1300 < max_force_side <= 1900:
        limit = 3
    elif 1900 < max_force_side:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_force_side, limit=limit)

# ---------- Abdomen_peak_force_maximum_compression - Side =[kN] -----------#
def  abdomen_peak_force_maximum_compression_side(vs_df, fs, abdominal_depth =200): #[abbreviation: FmaxCmax]
    for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY", "RIBSL_DSY"]:
        if not sensor in vs_df.keys():
            return None

    Dmax_side = mbf.calc_3ms(vs_df["RIBSL_DSY"].to_numpy().astype('float'), fs)
    Compression = (Dmax_side / abdominal_depth) * 100
    max_force_side = sum([mbf.calc_3ms(vs_df[sensor].to_numpy().astype('float'), fs) for sensor in ["ABDOFR_FOY", "ABDOMI_FOY", "ABDORE_FOY"]])

    max_force_max_compression = (max_force_side / 1000) * Compression

    p3ais = round(100 / (1 + math.exp(4.359 - 0.753 * max_force_max_compression)))

    return FormulaResult(value=max_force_max_compression, ais3p=p3ais)

# ------------ Viscous Criteria abdominal [sensitive] - Side -----------#             #[abbreviation: VCAbdomenSideSens]
def viscous_criteria_abdomen_side_sensitive(vs_df, fs, b=200):   # not yet trained
    for sensor in ["RIBSL_DSY"]:
        if not sensor in vs_df.keys():
            return None

    deformation = vs_df["RIBSL_DSY"]

    """deform = mbf.calc_3ms(deformation.to_numpy().astype('float'), fs)
    deform_percent = deform / b * 100"""

    deformation = np.asarray(deformation)
    Vt = mbf.ece_r_94_diff(deformation / 1000, fs)
    Ct = deformation[2:-2] / b

    vc = [a_i * b_i for a_i, b_i in zip(Vt, Ct)]
    vc_max = mbf.calc_3ms(np.array(vc).astype('float'), fs)

    p4ais = round(100 / (1 + math.exp(8.64 - 3.81 * vc_max)))

    if 0.75 <= vc_max <= 1.5:
        limit = 1
    elif 1.5 < vc_max < 1.9:
        limit = 2
    elif 1.9 <= vc_max <= 3.3:
        limit = 3
    elif 3.3 < vc_max:
        limit = 4
    else:
        limit = 0

    """if 0.5 <= vc_max < 1:
        limit = 1
    elif 1 <= vc_max < 2:
        limit = 2
    elif 2 <= vc_max:
        limit = 3
    else:
        limit = 0"""

    return FormulaResult(value=round(vc_max, 1), ais4p=p4ais, limit=limit)


# ------------ Viscous Criteria abdominal [non- sensitive] - Side -----------#            #[abbreviation: VCAbdomenSide]
def viscous_criteria_abdomen_side(vs_df, fs, b=200):   # not yet trained
    for sensor in ["RIBSL_DSY"]:
        if not sensor in vs_df.keys():
            return None

    deformation = vs_df["RIBSL_DSY"]

    deformation = np.asarray(deformation)
    Vt = mbf.ece_r_94_diff(deformation / 1000, fs)
    Ct = deformation[2:-2] / b

    vc = [a_i * b_i for a_i, b_i in zip(Vt, Ct)]
    vc_max = mbf.calc_3ms(np.array(vc).astype('float'), fs)

    if 0.75 <= vc_max <= 1.7:
        limit = 1
    elif 1.7 < vc_max <= 2.7:
        limit = 2
    elif 2.7 < vc_max <= 3.7:
        limit = 3
    elif 3.7 < vc_max:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=round(vc_max, 1), limit=limit)

# ------------ Viscous Criteria abdominal [sensitive] - frontal -----------#       #[abbreviation: VCAbdomenFrontalSens]
def viscous_criteria_abdomen_frontal_sensitive(vs_df, fs, b=200):   # not yet trained
    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    deformation = vs_df["CHST_DSX"]

    deformation = np.asarray(deformation)
    Vt = mbf.ece_r_94_diff(deformation / 1000, fs)
    Ct = deformation[2:-2] / b

    vc = [a_i * b_i for a_i, b_i in zip(Vt, Ct)]
    vc_max = mbf.calc_3ms(np.array(vc).astype('float'), fs)

    if 0.75 <= vc_max <= 1.2:
        limit = 1
    elif 1.2 < vc_max <= 2:
        limit = 2
    elif 2 < vc_max <= 2.6:
        limit = 3
    elif 2.6 < vc_max:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=round(vc_max, 1), limit=limit)

# ------------ Viscous Criteria abdominal [non- sensitive] - frontal -----------#      #[abbreviation: VCAbdomenFrontal]
def viscous_criteria_abdomen_frontal(vs_df, fs, b=200):   # not yet trained
    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    deformation = vs_df["CHST_DSX"]

    deformation = np.asarray(deformation)
    Vt = mbf.ece_r_94_diff(deformation / 1000, fs)
    Ct = deformation[2:-2] / b

    vc = [a_i * b_i for a_i, b_i in zip(Vt, Ct)]
    vc_max = mbf.calc_3ms(np.array(vc).astype('float'), fs)

    if 1.2 <= vc_max <= 2.4:
        limit = 1
    elif 2.4 < vc_max <= 3.57:
        limit = 2
    elif 3.57 < vc_max <= 3.8:
        limit = 3
    elif 3.8 < vc_max:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=round(vc_max, 1), limit=limit)

'''
# ---------- Abdomen_peak_total_force_frontal_v1 [non-sensitive] [force]=[N] -----------#
def abdomen_peak_total_force_frontal_v1(vs_df, fs): #[abbreviation: FmaxFrontalV1]
    for sensor in ["Abdo_Fx"]:
        if not sensor in vs_df.keys():
            return None

    max_force = mbf.calc_3ms(vs_df["Abdo_Fx"].to_numpy().astype('float'), fs)

    if 980 <= max_force <= 1500:
        limit = 1
    elif 1500 < max_force <= 2900:
        limit = 2
    elif 2900 < max_force <= 3900:
        limit = 3
    elif 3900 < max_force:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_force, limit=limit)

# ---------- Abdomen_peak_total_force_frontal_v2 [non-sensitive] [force]=[N] -----------#
def abdomen_peak_total_force_frontal_v2(vs_df, fs): #[abbreviation: FmaxFrontalV2]
    for sensor in ["Abdo_Fx"]:
        if not sensor in vs_df.keys():
            return None

    max_force = mbf.calc_3ms(vs_df["Abdo_Fx"].to_numpy().astype('float'), fs)

    if 1200 <= max_force <= 2800:
        limit = 1
    elif 2800 < max_force <= 3600:
        limit = 2
    elif 3600 < max_force <= 5300:
        limit = 3
    elif 5300 < max_force:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_force, limit=limit)

# ---------- Abdomen_peak_total_force_frontal [sensitive] [force]=[N] -----------#
def abdomen_peak_total_force_frontal_sensitive(vs_df, fs): #[abbreviation: FmaxFrontalSens]
    for sensor in ["Abdo_Fx"]:
        if not sensor in vs_df.keys():
            return None

    max_force = mbf.calc_3ms(vs_df["Abdo_Fx"].to_numpy().astype('float'), fs)

    if 880 <= max_force <= 1200:
        limit = 1
    elif 1200 < max_force <= 1300:
        limit = 2
    elif 1300 < max_force <= 1900:
        limit = 3
    elif 1900 < max_force:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_force, limit=limit)


# ---------- Abdomen_max_compression - side, [def]=[mm] -----------#
def abdomen_max_compression_side(vs_df, fs, abdominal_depth = 200): #[abbreviation: CmaxSide]
    for sensor in ["Abdo_DSY"]:
        if not sensor in vs_df.keys():
            return None

    max_compression = mbf.calc_3ms(vs_df["Abdo_DSY"].to_numpy().astype('float'), fs)
    max_c_percent= max_compression / abdominal_depth * 100

    if 10 <= max_c_percent <= 25:
        limit = 1
    elif 25 < max_c_percent <= 37:
        limit = 2
    elif 37 < max_c_percent <= 43.7:
        limit = 3
    elif 43.7 < max_c_percent:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_compression, limit=limit)

# ----------[Non-sensitive] Abdomen_max_compression - frontal, [def]=[mm] -----------#
def abdomen_max_compression_frontal(vs_df, fs, abdominal_depth = 200): #[abbreviation: CmaxFrontal]
    for sensor in ["Abdo_DSX"]:
        if not sensor in vs_df.keys():
            return None

    max_compression = mbf.calc_3ms(vs_df["Abdo_DSX"].to_numpy().astype('float'), fs)
    max_c_percent= max_compression / abdominal_depth * 100

    p4ais = round(100 / (1 + math.exp(10.046 - 0.01853 * max_c_percent)))

    if 10 <= max_c_percent <= 25:
        limit = 1
    elif 25 < max_c_percent <= 40:
        limit = 2
    elif 40 < max_c_percent <= 44:
        limit = 3
    elif 44 < max_c_percent:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_compression, ais4p=p4ais, limit=limit)

# ---------- Sensitive_abdomen_max_compression - frontal, [def]=[mm] -----------#
def abdomen_max_compression_frontal_sensitive(vs_df, fs, abdominal_depth = 200): #[abbreviation: CmaxFrontalSens]
    for sensor in ["Abdo_DSX"]:
        if not sensor in vs_df.keys():
            return None

    max_compression = mbf.calc_3ms(vs_df["Abdo_DSX"].to_numpy().astype('float'), fs) # TODO: Change sensor name
    max_c_percent= max_compression / abdominal_depth * 100

    p4ais = round(100 / (1 + math.exp(16.29 - 0.35 * max_c_percent)))

    if 10 <= max_c_percent <= 20:
        limit = 1
    elif 20 < max_c_percent <= 38:
        limit = 2
    elif 38 < max_c_percent <= 44:
        limit = 3
    elif 44 < max_c_percent:
        limit = 4
    else:
        limit = 0

    return FormulaResult(value=max_compression, ais4p=p4ais, limit=limit)

# ------------ abdominal injury criteria - frontal -----------#
def abdominal_injury_criteria(vs_df, fs, abdominal_depth =200): # [abbreviation: AIC]
    for sensor in ["Abdo_DSX"]:
        if not sensor in vs_df.keys():
            return None

    max_compression = calc_3ms(vs_df["Abdo_DSX"].to_numpy().astype('float'), fs)
    c_max= max_compression / abdominal_depth # [mm]

    deformation = vs_df["Abdo_DSX"]
    deformation = np.asarray(deformation)

    vt = ece_r_94_diff(deformation / 1000, fs)  #[ms]
    v_max = calc_3ms(np.array(vt).astype('float'), fs)

    aic = v_max * c_max

    p2ais = round(100 / (1 + math.exp(-8.07533 + 2.77263 * aic)))
    p3ais = round(100 / (1 + math.exp(-13.9050 + 3.51619 * aic)))
    
'''
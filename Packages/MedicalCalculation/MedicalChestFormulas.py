import numpy as np
import math
from MedicalCalculation.Common import FormulaResult
from MedicalCalculation.Common import GetMaxAISP
import MedicalCalculation.MedicalBasicFormulas as mbf


# ----------------------------------------------- Chest ---------------------------------------------------#

# ---------- Compression Criteria_frontal ----------#              # abbreviation [Deflection/C/CC/CCFrontal/Compression criteria]
def compression_criterion_frontal(vs_df, fs, chst_depth=229):
    # vs_df - data frame with all virtual sensors
    # fs = [Hz]
    # chst_depth - the depth of the chest in mm

    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    Dmax_frontal = mbf.calc_3ms(vs_df["CHST_DSX"].to_numpy().astype('float'), fs)
    Compression = (Dmax_frontal / chst_depth) * 100

    """AIS_chest = -3.78 + 19.56 * C
    AIS_chest = int(AIS_chest)
    if AIS_chest < 0:
        AIS_chest = 0"""

    # p4ais = round(100 / (1 + math.exp(31.22 - 79 * Compression)))

    if 13 <= Compression < 16:
        limit = 1
    elif 16 <= Compression <= 25:
        limit = 2
    elif 25 < Compression:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=Compression, limit=limit)

# ---------- Compression Criteria_side ----------#          # abbreviation [Deflection/C/CC/CCSide/Compression criteria]
def compression_criterion_side(vs_df, fs, chst_depth_side=114):
    # vs_df - data frame with all virtual sensors
    # fs = [Hz]
    # chst_depth - the depth of the chest in mm

    for sensor in ["RIBSL_DSY"]:
        if not sensor in vs_df.keys():
            return None

    Dmax_side = mbf.calc_3ms(vs_df["RIBSL_DSY"].to_numpy().astype('float'), fs)
    Compression = (Dmax_side / chst_depth_side) * 100

    p4ais = round((1 / (1 + math.exp(31.22 - 0.79 * Compression)))*100)

    if 13 <= Compression < 22:
        limit = 1
    elif 22 <= Compression <= 32:
        limit = 2
    elif 32 < Compression:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=Compression, ais4p=p4ais, limit=limit)

# --------- maximal chest deflection - Front [mm] -----------#          # abbreviation [Dmax_frontal/MCDF/DeqMax]
def maximal_chest_deflection_frontal(vs_df, fs, age = 45):
    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    Dmax_frontal = mbf.calc_3ms(vs_df["CHST_DSX"].to_numpy().astype('float'), fs)

    p2ais = round(100 / (1 + math.exp(1.8706 - 0.04439 * Dmax_frontal)))
    p3ais = round(100 / (1 + math.exp(12.597 - 0.05861 * age - 1.568 * Dmax_frontal ** 0.4612)))
    p4ais = round(100 / (1 + math.exp(5.0952 - 0.0475 * Dmax_frontal)))
    p5ais = round(100 / (1 + math.exp(8.8274 - 0.0459 * Dmax_frontal)))

    # old formulation
    # p3ais = round(100 / (1 + math.exp(3.7124 - 0.0475 * Dmax_frontal)))

    if 22 <= Dmax_frontal < 35:
        limit = 1
    elif 35 <= Dmax_frontal <= 42:
        limit = 2
    elif 42 < Dmax_frontal:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=Dmax_frontal, ais2p=p2ais, ais3p=p3ais, ais4p=p4ais, ais5p=p5ais, limit=limit)

'''
# --------- sensitive_maximal chest deflection - Front [mm] -#          # abbreviation [Dmax_frontal/MCDFSens/DeqMax]
def maximal_chest_deflection_frontal_sensitive(vs_df, fs, age = 45):
    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    Dmax_frontal = mbf.calc_3ms(vs_df["CHST_DSX"].to_numpy().astype('float'), fs)
    p3ais = round(100 / (1 + math.exp(17.5 - age / 5.8 - Dmax_frontal / 3.3)))

    return FormulaResult(value=Dmax_frontal, ais3p=p3ais)

'''

## --------- maximal chest deflection - Side [mm] -----------#           # abbreviation [Dmax_frontal/MCDS/DeqMax]
def maximal_chest_deflection_side(vs_df, fs):
    for sensor in ["RIBSL_DSY"]:
        if not sensor in vs_df.keys():
            return None

    Dmax_side = mbf.calc_3ms(vs_df["RIBSL_DSY"].to_numpy().astype('float'), fs)

    p3ais = round(100 / (1 + math.exp(5.3895 - 0.0919 * Dmax_side)))

    if 11 <= Dmax_side < 25:
        limit = 1
    elif 25 <= Dmax_side < 37:
        limit = 2
    elif 37 <= Dmax_side:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=Dmax_side, ais3p=p3ais, limit=limit)

# ------------ Viscous Criteria - Front-----------#                     # abbreviation [VCMaxFront/VC]
def chest_viscous_criteria_frontal(vs_df, fs, s=1.3, b=229):
    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    deformation = vs_df["CHST_DSX"]

    """deform = mbf.calc_3ms(deformation.to_numpy().astype('float'), fs)
    deform_percent = deform / b * 100"""

    deformation = np.asarray(deformation)
    Vt = mbf.ece_r_94_diff(deformation / 1000, fs)
    Ct = s * deformation[2:-2] / b

    vc = [a_i * b_i for a_i, b_i in zip(Vt, Ct)]
    vc_max = mbf.calc_3ms(np.array(vc).astype('float'), fs)

    p4ais = round(100 / (1 + math.exp(10.02 - 6.08 * vc_max)))

    if 0.5 <= vc_max < 0.8:
        limit = 1
    elif 0.8 <= vc_max < 1:
        limit = 2
    elif 1 <= vc_max:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=vc_max, ais4p=p4ais, limit=limit)

# ------------ Viscous Criteria - Side -----------#                     # abbreviation [VCMaxSide/VC]
def chest_viscous_criteria_side(vs_df, fs, b=140):
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

    p4ais = round(100 / (1 + math.exp(10.02 - 6.08 * vc_max)))

    if 0.5 <= vc_max < 1:
        limit = 1
    elif 1 <= vc_max < 2:
        limit = 2
    elif 2 <= vc_max:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=vc_max, ais4p=p4ais, limit=limit)


# ----------- Combined Thoracic Index (CTI) - Front -----------#        # abbreviation [CTI]
def combined_thoracic_index(vs_df, fs, a_int=85, d_int=102):
    for sensor in ["CHST_DSX", "CHST_ACX", "CHST_ACY", "CHST_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    acc = [math.sqrt(a ** 2 + b ** 2 + c ** 2) for a, b, c in
           zip(vs_df['CHST_ACX'].tolist(), vs_df['CHST_ACY'].tolist(), vs_df['CHST_ACZ'].tolist())]
    a_max = mbf.calc_3ms(np.array(acc).astype('float'), fs)
    d_max = mbf.calc_3ms(vs_df["CHST_DSX"].to_numpy().astype('float'), fs)

    cti = a_max / a_int + d_max / d_int
    p2ais = round(100 / (1 + math.exp(4.847 - 6.036 * cti)))
    p3ais = round(100 / (1 + math.exp(8.224 - 7.125 * cti)))
    p4ais = round(100 / (1 + math.exp(9.872 - 7.125 * cti)))
    p5ais = round(100 / (1 + math.exp(14.242 - 6.589 * cti)))

    probDict = {2: p2ais, 3: p3ais, 4: p4ais, 5: p5ais}
    maxais, maxpais = GetMaxAISP(probDict)

    if 35 <= maxpais:
        limit = maxais
    elif 28 <= maxpais < 35:
        limit = 2
    elif 20 <= maxpais < 28:
        limit = 1
    else:
        limit = 0

    return FormulaResult(value=float(cti), ais2p=p2ais, ais3p=p3ais, ais4p=p4ais, ais5p=p5ais, limit=limit)

# ---------- Thoracic Trauma Index (TTI) - Side ------------#           # abbreviation [TTI]
def thoracic_trauma_index(vs_df, fs, m=77.7, age=45):
    for sensor in ["RIBSL_ACY", "LUSP_ACY"]:
        if not sensor in vs_df.keys():
            return None

    m_std = 75
    riby = mbf.calc_3ms(vs_df["RIBSL_ACY"].to_numpy().astype('float'), fs)
    t12y = mbf.calc_3ms(vs_df["LUSP_ACY"].to_numpy().astype('float'), fs)
    tti = 1.4 * age + 0.5 * (riby + t12y) * m / m_std

    p2ais = p3ais = round(100 / (1 + math.exp(7.2448 - 0.048657 * tti)))
    p4ais = round(100 / (1 + math.exp(8.7703 - 0.048657 * tti)))

    if p3ais < 40:
        p3ais = 0

    """avg_accl = 0.5 * (riby + t12y)
    if avg_accl >= 85 and avg_accl < 90:
        limit = 1
    elif avg_accl >= 90:
        limit = 3
    else:
        limit = 0"""

    return FormulaResult(value=float(tti), ais2p=p2ais, ais3p=p3ais, ais4p=p4ais)

# ------------ Belt Force [N] ------------#                             # abbreviation [BeltForce]
def belt_force(vs_df, fs, age=45, k=98, m_type="human"):
    if 'CHST_DSX' in vs_df.keys():
        diformation = vs_df["CHST_DSX"].tolist()
    elif "RIBSL_DSY" in vs_df.keys():
        diformation = vs_df['RIBSL_DSY'].tolist()
    else:
        return None

    if m_type == "dummy":
        c = 0.341
    elif m_type == "human":
        c = 0.275

    diformation = np.asarray(diformation)
    Vt = np.asarray(mbf.ece_r_94_diff(diformation, fs))
    Dt = np.asarray(diformation[2:-2])

    Ft = k * Dt + c * Vt
    F = int(mbf.calc_3ms(np.array(Ft).astype('float'), fs))

    #p3ais = (100 / (1 + math.exp(19.9 - age / 5.9 - F / 557)))  # reliability questionable

    return FormulaResult(value=float(F))

# ----------- TIP (number of rib fracture to semi-thorax) - Side -----# # abbreviation [TIPSide]
def tip_side(vs_df, fs, bcf=-1.2, semi_thx_wd=138):
    # fs = [Hz]
    # bcf =
    # semi_thx_wd = [mm]

    for sensor in ["RIBSL_DSY"]:
        if not sensor in vs_df.keys():
            return None

    ribs3ms = mbf.calc_3ms(vs_df["RIBSL_DSY"].to_numpy().astype('float'), fs)
    tip = int(0.22275 * ((ribs3ms / semi_thx_wd) * 100) + 2.4824 * bcf - 1.098)

    #relative_chst_compress = float((ribs3ms / semi_thx_wd) * 100)
    # max_rib_def = 100*max([rib01_com,rib02_com,rib03_com,rib02_ab_com])/semi_thx_wd
    # tip = 0.2275*max_rib_def + 2.4824*bcf - 1.098

    if tip < 0:
        tip = 0

    if 1 <= tip < 2:
        limit = 1
    elif 2 <= tip < 5:
        limit = 2
    elif 5 <= tip:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=float(tip), limit=limit)

# ----------- TIP (number of rib fracture to Full-thorax) - frontal --# # abbreviation [TIPFrontal]
def tip_frontal(vs_df, fs, bcf=-1.2, full_thx_wd=229):
    # fs = [Hz]
    # bcf =
    # thx_wd = [mm]

    for sensor in ["CHST_DSX"]:
        if not sensor in vs_df.keys():
            return None

    chest3ms = mbf.calc_3ms(vs_df["CHST_DSX"].to_numpy().astype('float'), fs)
    tip = int(0.22275 * ((chest3ms / full_thx_wd) * 100) + 2.4824 * bcf - 1.098)

    if tip < 0:
        tip = 0

    if 1 <= tip < 2:
        limit = 1
    elif 2 <= tip < 5:
        limit = 2
    elif 5 <= tip:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=float(tip), limit=limit)

# ---------- Chest A3ms - Front ----------#                            # abbreviation [CA3msFrontal]
def chest_a3ms_frontal(vs_df, fs):
    for sensor in ["CHST_ACX", "CHST_ACY", "CHST_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    data = [math.sqrt(a ** 2 + b ** 2 + c ** 2) for a, b, c in
            zip(vs_df['CHST_ACX'].tolist(), vs_df['CHST_ACY'].tolist(), vs_df['CHST_ACZ'].tolist())]

    chest_A3ms_frontal = mbf.calc_3ms(np.array(data).astype('float'), fs)

    if 60 <= chest_A3ms_frontal:
        limit = 1
    else:
        limit = 0

    return FormulaResult(value=chest_A3ms_frontal, limit=limit)


# ---------- Chest A3ms - side ----------#                             # abbreviation [CA3msSide]
def chest_a3ms_side(vs_df, fs):
    for sensor in ["RIBSL_ACY"]:
        if not sensor in vs_df.keys():
            return None

    chest_A3ms_side = mbf.calc_3ms(np.array(vs_df["RIBSL_ACY"]).astype('float'), fs)

    if 60 <= chest_A3ms_side:
        limit = 1
    else:
        limit = 0

    return FormulaResult(value=chest_A3ms_side, limit=limit)

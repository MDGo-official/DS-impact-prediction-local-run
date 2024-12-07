import numpy as np
import math
from MedicalCalculation.Common import FormulaResult
import MedicalCalculation.MedicalBasicFormulas as mbf


# ----------------------------------------------- Neck ----------------------------------------------------#

# --------- Neck Injury Criteria - Front, Rear, Side ----------#             # abbreviation [NIJFront]
def neck_injury_criteria_frontal(vs_df, fs, Ften=4500, Fcom=4500, Mext=125, Mflex=310):
    # df_neck - neck data frame with NECKUP_FOZ, NECKUP_MOY
    # fs = [Hz]
    # Ften,Fcom = [N]
    # Mext,Mflex = [Nm]

    for sensor in ["NECKUP_FOZ", "NECKUP_MOY"]:
        if not sensor in vs_df.keys():
            return None

    Fz = mbf.calc_3ms(vs_df["NECKUP_FOZ"].to_numpy().astype('float'), fs)
    My = mbf.calc_3ms(vs_df["NECKUP_MOY"].to_numpy().astype('float'), fs)

    Nte = Fz / Ften + My / Mext
    Ntf = Fz / Ften + My / Mflex
    Nce = Fz / Fcom + My / Mext
    Ncf = Fz / Fcom + My / Mflex

    Nij = [Nte, Ntf, Nce, Ncf]

    p2ais = []
    p3ais = []
    p4ais = []
    p5ais = []
    #p2ais_af = []
    #p3ais_af = []

    for nij in Nij:
        p2ais.append(round(100 / (1 + math.exp(4.3085 - 5.4079 * nij))))
        p3ais.append(round(100 / (1 + math.exp(4.9372 - 4.5294 * nij))))
        p4ais.append(round(100 / (1 + math.exp(2.693 - 1.195 * nij))))
        p5ais.append(round(100 / (1 + math.exp(3.817 - 1.195 * nij))))
        # air force criteria
        #p2ais_af.append(round(100 / (1 + math.exp(5.2545 - 4.1 * nij))))
        #p3ais_af.append(round(100 / (1 + math.exp(5.31423 - 3.3922 * nij))))

    maxNij = float(max(Nij))

    if 0.5 <= maxNij < 1:
        limit = 1
    elif 1 <= maxNij < 1.2:
        limit = 2
    elif maxNij >= 1.2:
        limit = 3
    else:
        limit = 0

    return FormulaResult(value=maxNij, ais2p=max(p2ais), ais3p=max(p3ais), ais4p=max(p4ais), ais5p=max(p5ais), limit=limit)

# --------- Neck Injury Criteria - Front, Rear, Side ----------#             # abbreviation [NIJSide]
def neck_injury_criteria_lateral(vs_df, fs, Ften=6810, Fcom=6160, Mr=60, Ml=60):
    # df_neck - neck data frame with NECKUP_FOZ, NECKUP_MOX
    # fs = [Hz]
    # Ften,Fcom = [N]
    # Mr,Ml = [Nm]

    for sensor in ["NECKUP_FOZ", "NECKUP_MOX"]:
        if not sensor in vs_df.keys():
            return None

    Fz = mbf.calc_3ms(vs_df["NECKUP_FOZ"].to_numpy().astype('float'), fs)
    Mx = mbf.calc_3ms(vs_df["NECKUP_MOX"].to_numpy().astype('float'), fs)

    Ntl = Fz / Ften + Mx / Ml
    Ntr = Fz / Ften + Mx / Mr
    Ncl = Fz / Fcom + Mx / Ml
    Ncr = Fz / Fcom + Mx / Mr

    Nij_lateral = [Ntl, Ntr, Ncl, Ncr]

    p2ais = []
    p3ais = []
    p4ais = []
    p5ais = []

    for nij in Nij_lateral:
        p2ais.append(round(100 / (1 + math.exp(4.3085 - 5.4079 * nij))))
        p3ais.append(round(100 / (1 + math.exp(4.9372 - 4.5294 * nij))))
        p4ais.append(round(100 / (1 + math.exp(2.693 - 1.195 * nij))))
        p5ais.append(round(100 / (1 + math.exp(3.817 - 1.195 * nij))))

    maxNij_lateral = float(max(Nij_lateral))

    if 0.5 <= maxNij_lateral < 1:
        limit = 1
    elif 1 <= maxNij_lateral < 1.3:
        limit = 2
    elif maxNij_lateral >= 1.3:
        limit = 3
    else:
        limit = 0

    #return FormulaResult(value=maxNij_lateral, ais2p=max(p2ais), ais3p=max(p3ais), ais4p=max(p4ais), ais5p=max(p5ais), limit=limit)

    return FormulaResult(value=maxNij_lateral, limit=limit)

# --------- NKM - Front, Side, Rear ----------#                              # abbreviation [NKMWhip]
def nkm(vs_df, fs, mechanism):

    for sensor in ["NECKUP_FOX", "NECKUP_MOY"]:
        if not sensor in vs_df.keys():
            return None

    if mechanism == 'Frontal' or 'Side' in mechanism:
        return nkm_FrontSide(vs_df, fs)

    elif mechanism == 'Rear':
        return nkm_Rear(vs_df, fs)

# --------- NKM - Front, Side ----------#
def nkm_FrontSide(vs_df, fs, Fneg=845, Fpos=845, Mext=47.5, Mflex=88.1):
    # df_neck - neck data frame with NECKUP_FOZ, NECKUP_MOY
    # fs = [Hz]
    # Fneg,Fpos = [N]
    # Mext,Mflex = [Nm]

    Fx = np.asarray(vs_df["NECKUP_FOX"])
    My = np.asarray(vs_df["NECKUP_MOY"])
    Nfp_t = Fx / Fneg + My / Mflex
    Nfa_t = Fx / Fpos + My / Mflex
    Nep_t = Fx / Fneg + My / Mext
    Nea_t = Fx / Fpos + My / Mext

    Nfp = mbf.calc_3ms(np.array(Nfp_t).astype('float'), fs)
    Nfa = mbf.calc_3ms(np.array(Nfa_t).astype('float'), fs)
    Nep = mbf.calc_3ms(np.array(Nep_t).astype('float'), fs)
    Nea = mbf.calc_3ms(np.array(Nea_t).astype('float'), fs)

    max_nkm = max(float(Nfp), float(Nfa), float(Nep), float(Nea))
    if max_nkm >= 0.98:
        limit = 1
    else:
        limit = 0

    return FormulaResult(value=max_nkm, limit=limit)
# --------- NKM - Rear ----------#
def nkm_Rear(vs_df, fs, Fneg=845, Fpos=845, Mext=47.5, Mflex=88.1):
    # df_neck - neck data frame with NECKUP_FOZ, NECKUP_MOY
    # fs = [Hz]
    # Fneg,Fpos = [N]
    # Mext,Mflex = [Nm]

    Fx = np.asarray(vs_df["NECKUP_FOX"])
    My = np.asarray(vs_df["NECKUP_MOY"])
    Nfp_t = Fx / Fneg + My / Mflex
    Nfa_t = Fx / Fpos + My / Mflex
    Nep_t = Fx / Fneg + My / Mext
    Nea_t = Fx / Fpos + My / Mext

    Nfp = mbf.calc_3ms(np.array(Nfp_t).astype('float'), fs)
    Nfa = mbf.calc_3ms(np.array(Nfa_t).astype('float'), fs)
    Nep = mbf.calc_3ms(np.array(Nep_t).astype('float'), fs)
    Nea = mbf.calc_3ms(np.array(Nea_t).astype('float'), fs)

    max_nkm = max(float(Nfp), float(Nfa), float(Nep), float(Nea))
    if 0.5 <= max_nkm:
        limit = 1
    else:
        limit = 0

    return FormulaResult(value=max_nkm, limit=limit)


# -------- Multi-axial neck injury criteria - Frontal, Side, Rear --------#  # abbreviation [MANIC]
def manic(vs_df, fs, mechanism, model='human'):
    # df - data frame with:
    # frontal: NECKUP_FOX, NECKUP_FOY, NECKUP_FOZ, NECKUP_MOY
    # side: NECKUP_FOX, NECKUP_FOY, NECKUP_FOZ, NECKUP_MOX, NECKUP_MOZ
    # rear: NECKUP_FOX, NECKUP_FOZ, NECKUP_MOY
    # fs = [Hz]
    # model - string: human, dummy
    # mechanism = string: frontal, rear, side
    if mechanism == 'Frontal':
        for sensor in ["NECKUP_FOZ", "NECKUP_MOY"]:
            if not sensor in vs_df.keys():
                return None
    elif mechanism == 'Rear':
        for sensor in ["NECKUP_FOZ", "NECKUP_MOY"]:
            if not sensor in vs_df.keys():
                return None
    elif 'Side' in mechanism:
        for sensor in ["NECKUP_FOY", "NECKUP_FOZ", "NECKUP_MOX", "NECKUP_MOZ"]:
            if not sensor in vs_df.keys():
                return None
    Fxcrit = 2780
    Fycrit = 2780
    Fzcrit_p = 6806
    Fzcrit_n = 6160
    Mxcrit = 135
    Mycrit_p = 310
    Mycrit_n = 135
    Mzcrit = 135
    Fz = mbf.calc_3ms(vs_df["NECKUP_FOZ"].to_numpy().astype('float'), fs)
    if Fz >= 0:
        Fzn = Fz / Fzcrit_p
    else:
        Fzn = Fz / Fzcrit_n
    if mechanism == 'Frontal':
        #Fy = calc_3ms(vs_df["NECKUP_FOY"].to_numpy().astype('float'), fs)
        #Fyn = Fy / Fycrit
        Fyn = 0
        My = mbf.calc_3ms(vs_df["NECKUP_MOY"].to_numpy().astype('float'), fs)
        if My >= 0:
            Myn = My / Mycrit_p
        else:
            Myn = My / Mycrit_n
        Mxn = 0
        Mzn = 0
    elif 'Side' in mechanism:
        Fy = mbf.calc_3ms(vs_df["NECKUP_FOY"].to_numpy().astype('float'), fs)
        Fyn = Fy / Fycrit
        Mx = mbf.calc_3ms(vs_df["NECKUP_MOX"].to_numpy().astype('float'), fs)
        Mxn = Mx / Mxcrit
        Mz = mbf.calc_3ms(vs_df["NECKUP_MOZ"].to_numpy().astype('float'), fs)
        Mzn = Mz / Mzcrit
        Myn = 0
    elif mechanism == 'Rear':
        My = mbf.calc_3ms(vs_df["NECKUP_MOY"].to_numpy().astype('float'), fs)
        if My >= 0:
            Myn = My / Mycrit_p
        else:
            Myn = My / Mycrit_n
        Fyn = 0
        Mxn = 0
        Mzn = 0
    if model == 'human':
        manic_Gy = math.sqrt(Fyn ** 2 + Fzn ** 2 + Myn ** 2 + Mzn ** 2)
    elif model == 'dummy':
        manic_Gy = math.sqrt(Fyn ** 2 + Fzn ** 2 + Mxn ** 2 + Myn ** 2 + Mzn ** 2)
    p2ais_Gy = round(100 / (1 + math.exp(6.185 - 6.85 * manic_Gy)))
    p3ais_Gy = round(100 / (1 + math.exp(5.44 - 4.73 * manic_Gy)))
    manic_Gx = abs(Fzn) + abs(Myn)
    p2ais_Gx = round(100 / (1 + math.exp(5.2545 - 4.1 * manic_Gx)))
    p3ais_Gx = round(100 / (1 + math.exp(5.31423 - 3.3922 * manic_Gx)))
    manic_Gz = Fz
    p2ais_Gz = round(100 / (1 + math.exp(5.44 - 0.00271 * manic_Gz)))
    p3ais_Gz = round(100 / (1 + math.exp(6.318 - 0.00297 * manic_Gz)))
    max_manic = max(float(manic_Gx),float(manic_Gy),float(manic_Gz))
    if 0.47 < manic_Gy < 0.7:
        limit = 1
    elif 0.7 <= manic_Gy < 0.86:
        limit = 2
    elif manic_Gy >= 0.86:
        limit = 3
    else:
        limit = 0
    return FormulaResult(value=max_manic, ais2p=max(p2ais_Gx, p2ais_Gy, p2ais_Gz), ais3p=max(p3ais_Gx, p3ais_Gy, p3ais_Gz), limit=limit)


# --------- Neck Injury Criteria (NIC) - Rear low speed -----------#         # abbreviation [NICWhip]
def nic(vs_df, fs):
    # df - data frame with HEAD_ACX, HEAD_ACY, HEAD_ACZ, LUSP01_ACX, LUSP01_ACZ
    # fs = [Hz]

    for sensor in ["HEAD_ACX", "HEAD_ACY", "HEAD_ACZ", "LUSP_ACX", "LUSP_ACZ"]:
        if not sensor in vs_df.keys():
            return None

    a_head = [math.sqrt(a ** 2 + b ** 2 + c ** 2) for a, b, c in
              zip(vs_df['HEAD_ACX'].tolist(), vs_df['HEAD_ACY'].tolist(), vs_df['HEAD_ACZ'].tolist())]
    a_T1 = [math.sqrt(a ** 2 + b ** 2) for a, b in zip(vs_df['LUSP_ACX'].tolist(), vs_df['LUSP_ACZ'].tolist())]
    a_rel = [a - b for a, b in zip(a_T1, a_head)]
    v_rel = np.cumsum(a_rel) / fs

    nic = [0.2 * a + b ** 2 for a, b in zip(a_rel, v_rel)]
    nic_max = mbf.calc_3ms(np.array(nic).astype('float'), fs)
    nic_max_f = float(nic_max)

    Phi_neck = round((nic_max_f / 15)*100)
    if Phi_neck > 100:
        Phi_neck = 100

    if nic_max_f < 15:
        limit = 0
    else:
        limit = 1

    return FormulaResult(value=nic_max_f, ais1p=Phi_neck, limit=limit)


# --------- Neck Shear Force: [Neck force] = [kN] ----------#                # abbreviation [NShearF]
def neck_shear_force(vs_df, fs):
    # This formulation is currently disabled (overpredicted virtual-sensor)
    return None

    # if not "NECKUP_FOX" in vs_df.keys():
    #     return None
    #
    # neckShearForce = mbf.calc_3ms(vs_df["NECKUP_FOX"], fs) / 1000  # [kN]
    #
    # if 1.1 <= neckShearForce <= 1.5:
    #     shearForceFlag = 1
    # elif 1.5 < neckShearForce <= 3.3:
    #     shearForceFlag = 2
    # elif 3.3 < neckShearForce:
    #     shearForceFlag = 3
    # else:
    #     shearForceFlag = 0
    #
    # return FormulaResult(value=neckShearForce, limit=shearForceFlag)


# ---------- Neck Tension Force: [Neck Tension] = [kN] ----------#           # abbreviation [NTensionF]
def neck_tension_force(vs_df, fs):
    if not "NECKUP_FOZ" in vs_df.keys():
        return None

    neckTensionForce = mbf.calc_3ms(vs_df["NECKUP_FOZ"], fs) / 1000  # [kN]

    if 1.2 <= neckTensionForce <= 2.5:
        tensionFlag = 1
    elif 2.5 < neckTensionForce:
        tensionFlag = 3
    else:
        tensionFlag = 0

    return FormulaResult(value=neckTensionForce, limit=tensionFlag)


# ---------- Neck Compression Force: [Neck Compression] = [kN] ----------#   # abbreviation [NCompressionF]
def neck_compression_force(vs_df, fs):
    if not "NECKUP_FOZ" in vs_df.keys():
        return None

    neckCompressionForce = mbf.calc_3ms(vs_df["NECKUP_FOZ"], fs) / 1000  # [kN]

    if 1.5 <= neckCompressionForce <= 2.8:
        compressionFlag = 1
    elif 2.8 < neckCompressionForce:
        compressionFlag = 3
    else:
        compressionFlag = 0

    return FormulaResult(value=neckCompressionForce, limit=compressionFlag)


# ---------- Neck Extension Force: [Neck Extention] = [Nm] ----------#       # abbreviation [NExtensionF]
def neck_extension_force(vs_df, fs):
    # vs_df - data frame with all virtual sensors
    # neckExtensionForce = [Nm]
    if not "NECKUP_MOY" in vs_df.keys():
        return None

    neckExtensionForce = mbf.calc_3ms(vs_df["NECKUP_MOY"], fs)  # [Nm]

    if 38 <= neckExtensionForce <= 42:
        extensionFlag = 1
    elif 42 < neckExtensionForce <= 56:
        extensionFlag = 2
    elif 56 < neckExtensionForce:
        extensionFlag = 3
    else:
        extensionFlag = 0

    return FormulaResult(value=neckExtensionForce, limit=extensionFlag)


# ---------- Neck Flexion Force: [Neck Flexion] = [Nm] ----------#           # abbreviation [NFlexionF]
def neck_flexion_force(vs_df, fs):
    # vs_df - data frame with all virtual sensors
    # neckExtensionForce = [Nm]
    if not "NECKUP_MOY" in vs_df.keys():
        return None

    neckFlexionForce = mbf.calc_3ms(vs_df["NECKUP_MOY"], fs)  # [Nm]

    if 61 <= neckFlexionForce <= 88:
        flexionFlag = 1
    elif 88 < neckFlexionForce <= 190:
        flexionFlag = 2
    elif 190 < neckFlexionForce:
        flexionFlag = 3
    else:
        flexionFlag = 0

    return FormulaResult(value=neckFlexionForce, limit=flexionFlag)

# --------- Lower Neck Injury Criteria - Rear ----------#             # abbreviation [LNIJRear]
def neck_injury_criteria_rear(vs_df, fs, H3Fcrit=565, THORFcrit=342, H3Mcrit=117, THORMcrit=85):
    # df_neck - neck data frame with NECKLO_FOZ,NECKLO_FOX, NECKLO_MOY
    # fs = [Hz]
    # Fcrit = [N]
    # Mcrit = [Nm]

    for sensor in ["NECKLO_FOZ","NECKLO_FOX", "NECKLO_MOY"]:
        if not sensor in vs_df.keys():
            return None

    Fz = mbf.calc_3ms(vs_df["NECKLO_FOZ"].to_numpy().astype('float'), fs)
    Fx = mbf.calc_3ms(vs_df["NECKLO_FOX"].to_numpy().astype('float'), fs)
    My = mbf.calc_3ms(vs_df["NECKLO_MOY"].to_numpy().astype('float'), fs)

    H3LNz = Fz / H3Fcrit + My / H3Mcrit
    H3LNx = Fx / H3Fcrit + My / H3Mcrit

    THORLNz = Fz / THORFcrit + My / THORMcrit
    THORLNx = Fx / THORFcrit + My / THORMcrit

    H3LNij = [H3LNz, H3LNx]
    THORLNij = [THORLNz, THORLNx]

    maxH3LNij = float(max(H3LNij))
    maxTHORLNij = float(max(THORLNij))

    # calculations for Hybrid3:
    if 1.1 <= maxH3LNij <= 1.9:
        limit = 1
    elif maxH3LNij > 1.9:
        limit = 2
    else:
        limit = 0

    # calculations for Thor:
    # if 1.2 <= maxTHORLNij <= 1.9:
    #     limit = 1
    # elif maxTHORLNij > 1.9:
    #     limit = 2
    # else:
    #     limit = 0

    return {
        'H3LNij': maxH3LNij,
        'THORLNij': maxTHORLNij,
        'H3LNz': H3LNz,
        'H3LNx': H3LNx,
        'THORLNz': THORLNz,
        'THORLNx': THORLNx,
        'limit': limit
    }

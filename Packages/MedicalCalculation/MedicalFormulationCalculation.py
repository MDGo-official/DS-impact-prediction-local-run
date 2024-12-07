import pandas as pd
from MedicalCalculation.Common import CalcMaxAISWithLimit, CombineFormulas, CalcMaxAISByLimitWithFlag
import MedicalCalculation.MedicalHeadFormulas as mhf
import MedicalCalculation.MedicalNeckFormulas as mnf
import MedicalCalculation.MedicalChestFormulas as mcf
import MedicalCalculation.MedicalAbdominalFormulas as maf
import MedicalCalculation.MedicalPelvicFormulas as mpf
import MedicalCalculation.MedicalFemurFormulas as mff


class MedicalFormulationCalculation:
    def __init__(self, mech, vs, fs=200):
        self.fs = fs
        self.mechanism = mech
        self.vs_df = pd.DataFrame.from_dict(vs)
        self.medical_criteria = {
            "Head": {
                "HIC": {},
                "HIP": {},
                "HA3ms": {}
            },
            "Neck": {
                "NIJFront": {},
                "NIJSide": {},
                "NKMWhip": {},
                "MANIC": {},
                "NICWhip": {},
                "NShearF": {},
                "NTensionF": {},
                "NCompressionF": {},
                "NExtensionF": {},
                "NFlexionF": {},
                "NIJ": {},
                "LNIJRear": {}
            },
            "Chest": {
                "CCFrontal": {},
                "CCSide": {},
                "MCDF": {},
                "MCDS": {},
                "VCMaxFront": {},
                "VCMaxSide": {},
                "CTI": {},
                "TTI": {},
                "BeltForce": {},
                "TIPSide": {},
                "TIPFrontal": {},
                "CA3msFrontal": {},
                "CA3msSide": {},
                "Frontal": {},
                "Side": {}
            },
            "Abdominal": {
                "FmaxSideV1": {},
                "FmaxSideV2": {},
                "FmaxSideSens": {},
                "FmaxCmaxSide": {},
                "VCAbdomenSideSens": {},
                "VCAbdomenSide": {},
                "VCAbdomenFrontalSens": {},
                "VCAbdomenFrontal": {}
            },
            "Pelvic": {
                "PSPFSide": {},
                "PSPFSideSens": {},
                "PelvicRearAcc": {},
                "PelvicSideAcc": {}
            },
            "Femur": {
                "PAFFrontalSens": {},
                "PAFFrontal": {}
            }
        }

    def calc_head(self):
        self.medical_criteria["Head"]["HIC"] = mhf.calc_hic(self.vs_df, self.fs)
        self.medical_criteria["Head"]["HIP"] = mhf.head_impact_power(self.vs_df, self.fs)
        self.medical_criteria["Head"]["HA3ms"] = mhf.head_a3ms(self.vs_df, self.fs)

    def calc_neck(self):
        self.medical_criteria["Neck"]["NIJFront"] = mnf.neck_injury_criteria_frontal(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NIJSide"] = mnf.neck_injury_criteria_lateral(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NKMWhip"] = mnf.nkm(self.vs_df, self.fs, self.mechanism)
        self.medical_criteria["Neck"]["MANIC"] = mnf.manic(self.vs_df, self.fs, self.mechanism)
        self.medical_criteria["Neck"]["NICWhip"] = mnf.nic(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NShearF"] = mnf.neck_shear_force(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NTensionF"] = mnf.neck_tension_force(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NCompressionF"] = mnf.neck_compression_force(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NExtensionF"] = mnf.neck_extension_force(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["NFlexionF"] = mnf.neck_flexion_force(self.vs_df, self.fs)
        self.medical_criteria["Neck"]["LNIJRear"] = mnf.neck_injury_criteria_rear(self.vs_df, self.fs)

    def calc_chest(self):
        self.medical_criteria["Chest"]["CCFrontal"] = mcf.compression_criterion_frontal(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["CCSide"] = mcf.compression_criterion_side(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["MCDF"] = mcf.maximal_chest_deflection_frontal(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["MCDS"] = mcf.maximal_chest_deflection_side(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["VCMaxFront"] = mcf.chest_viscous_criteria_frontal(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["VCMaxSide"] = mcf.chest_viscous_criteria_side(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["CTI"] = mcf.combined_thoracic_index(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["TTI"] = mcf.thoracic_trauma_index(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["BeltForce"] = mcf.belt_force(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["TIPSide"] = mcf.tip_side(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["TIPFrontal"] = mcf.tip_frontal(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["CA3msFrontal"] = mcf.chest_a3ms_frontal(self.vs_df, self.fs)
        self.medical_criteria["Chest"]["CA3msSide"] = mcf.chest_a3ms_side(self.vs_df, self.fs)

    def calc_abdominal(self):
        self.medical_criteria["Abdominal"]["FmaxSideV1"] = maf.abdomen_peak_total_force_side_v1(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["FmaxSideV2"] = maf.abdomen_peak_total_force_side_v2(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["FmaxSideSens"] = maf.abdomen_peak_total_force_side_sensitive(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["FmaxCmaxSide"] = maf.abdomen_peak_force_maximum_compression_side(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["VCAbdomenSideSens"] = maf.viscous_criteria_abdomen_side_sensitive(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["VCAbdomenSide"] = maf.viscous_criteria_abdomen_side(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["VCAbdomenFrontalSens"] = maf.viscous_criteria_abdomen_frontal_sensitive(self.vs_df, self.fs)
        self.medical_criteria["Abdominal"]["VCAbdomenFrontal"] = maf.viscous_criteria_abdomen_frontal(self.vs_df, self.fs)

    def calc_pelvic(self):
        self.medical_criteria["Pelvic"]["PSPFSide"] = mpf.maximal_lateral_pubic_symphysis_force(self.vs_df, self.fs)
        self.medical_criteria["Pelvic"]["PSPFSideSens"] = mpf.maximal_lateral_pubic_symphysis_force_sensitive(self.vs_df, self.fs)
        self.medical_criteria["Pelvic"]["PelvicRearAcc"] = mpf.max_pelvis_acceleration_rear(self.vs_df, self.fs)
        self.medical_criteria["Pelvic"]["PelvicSideAcc"] = mpf.max_pelvis_acceleration_side(self.vs_df, self.fs)

    def calc_femur(self):  # Femur Force
        self.medical_criteria["Femur"]["PAFFrontalSens"] = mff.femur_axial_force_sensitive(self.vs_df, self.fs)
        self.medical_criteria["Femur"]["PAFFrontal"] = mff.femur_axial_force(self.vs_df, self.fs)

    def calc_all_formulas(self):
        self.calc_head()
        self.calc_neck()
        self.calc_chest()
        self.calc_abdominal()
        self.calc_pelvic()
        self.calc_femur()

    def calc_ais_head(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Head"]["HIC"], 20, 20)
        CalcMaxAISWithLimit(self.medical_criteria["Head"]["HIP"], 20, 20)

        # calc formulas combination
        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Head"]["HIC"], self.medical_criteria["Head"]["HIP"]])

        # check other conditions
        if aisFormula <= 2:
            if self.medical_criteria["Head"]["HA3ms"] is not None:
                limit = self.medical_criteria["Head"]["HA3ms"]["Limit"]
                if limit < 3:
                    if limit > aisFormula:
                        aisFormula = limit
                        aisFormula_prob[aisFormula] = 20
                elif limit == 3 and aisFormula < 2:
                    aisFormula = 2
                    aisFormula_prob[aisFormula] = 25

        return aisFormula, aisFormula_prob

    def calc_ais_neck(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Neck"]["NIJSide"], 30, 20)
        CalcMaxAISWithLimit(self.medical_criteria["Neck"]["NIJFront"], 20, 20)
        CalcMaxAISWithLimit(self.medical_criteria["Neck"]["MANIC"], 25, 20)

        # calc formulas combination
        self.medical_criteria["Neck"]["NIJ"]["AIS"], self.medical_criteria["Neck"]["NIJ"]["P(AIS)"]\
            = CombineFormulas([self.medical_criteria["Neck"]["NIJSide"], self.medical_criteria["Neck"]["NIJFront"]])

        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Neck"]["NIJ"], self.medical_criteria["Neck"]["MANIC"]])

        # check other conditions
        limits = []
        if self.medical_criteria["Neck"]["NShearF"] is not None:
            limits.append(self.medical_criteria["Neck"]["NShearF"]["Limit"])
        if self.medical_criteria["Neck"]["NTensionF"] is not None:
            limits.append(self.medical_criteria["Neck"]["NTensionF"]["Limit"])
        if self.medical_criteria["Neck"]["NCompressionF"] is not None:
            limits.append(self.medical_criteria["Neck"]["NCompressionF"]["Limit"])
        if self.medical_criteria["Neck"]["NExtensionF"] is not None:
            limits.append(self.medical_criteria["Neck"]["NExtensionF"]["Limit"])
        if self.medical_criteria["Neck"]["NFlexionF"] is not None:
            limits.append(self.medical_criteria["Neck"]["NFlexionF"]["Limit"])
        if self.medical_criteria["Neck"]["NKMWhip"] is not None:
            limits.append(self.medical_criteria["Neck"]["NKMWhip"]["Limit"])
        if self.medical_criteria["Neck"]["NICWhip"] is not None:
            limits.append(self.medical_criteria["Neck"]["NICWhip"]["Limit"])

        if len(limits) > 0:
            maxLimit = max(limits)
            if maxLimit > aisFormula:
                aisFormula = maxLimit
                aisFormula_prob[aisFormula] = 25
            elif aisFormula < 1 and self.medical_criteria["Neck"]["MANIC"] is not None and self.medical_criteria["Neck"]["MANIC"]["AIS"] >= 10:
                aisFormula = 1
                aisFormula_prob[aisFormula] = 20

        return aisFormula, aisFormula_prob


    def calc_ais_chest_side(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["MCDS"], 35, 30)
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["TTI"], 20, 30)
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["VCMaxSide"], 20, 30)
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["CCSide"], 20, 30)

        # calc formulation combination
        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Chest"]["MCDS"],
                                                           self.medical_criteria["Chest"]["TTI"],
                                                           self.medical_criteria["Chest"]["VCMaxSide"],
                                                           self.medical_criteria["Chest"]["CCSide"]])
        # check other conditions
        limits = []
        if self.medical_criteria["Chest"]["TIPSide"] is not None:
            limits.append(self.medical_criteria["Chest"]["TIPSide"]["Limit"])
        if self.medical_criteria["Chest"]["CA3msSide"] is not None:
            limits.append(self.medical_criteria["Chest"]["CA3msSide"]["Limit"])

        if len(limits) > 0:
            maxLimit = max(limits)
            if maxLimit > aisFormula and aisFormula <= 1:
                aisFormula = aisFormula + 1
                aisFormula_prob[aisFormula] = 30

        return aisFormula, aisFormula_prob

    def calc_ais_chest_front(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["MCDF"], 35, 35)
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["CTI"], 35, 35)
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["VCMaxFront"], 20, 35)
        CalcMaxAISWithLimit(self.medical_criteria["Chest"]["CCFrontal"], 20, 35)

        # calc formulas combination
        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Chest"]["MCDF"],
                                                           self.medical_criteria["Chest"]["CTI"],
                                                           self.medical_criteria["Chest"]["VCMaxFront"],
                                                           self.medical_criteria["Chest"]["CCFrontal"]])

        # check other conditions
        limits = []
        if self.medical_criteria["Chest"]["CCFrontal"] is not None:
            limits.append(self.medical_criteria["Chest"]["CCFrontal"]["Limit"])
        if self.medical_criteria["Chest"]["CA3msFrontal"] is not None:
            limits.append(self.medical_criteria["Chest"]["CA3msFrontal"]["Limit"])

        if len(limits) > 0:
            maxLimit = max(limits)
            if maxLimit > aisFormula and aisFormula <= 1:
                aisFormula = aisFormula + 1
                aisFormula_prob[aisFormula] = 35

        return aisFormula, aisFormula_prob

    def calc_ais_chest(self):
        self.medical_criteria["Chest"]["Frontal"]["AIS"], self.medical_criteria["Chest"]["Frontal"]["P(AIS)"]\
                                                    = self.calc_ais_chest_front()
        self.medical_criteria["Chest"]["Side"]["AIS"], self.medical_criteria["Chest"]["Side"]["P(AIS)"]\
                                                    = self.calc_ais_chest_side()

        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Chest"]["Frontal"],
                                                           self.medical_criteria["Chest"]["Side"]])

        return aisFormula, aisFormula_prob

    def calc_ais_abdominal(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Abdominal"]["FmaxSideV1"], 20, 25)
        CalcMaxAISByLimitWithFlag(self.medical_criteria["Abdominal"]["VCAbdomenSide"], 0, 25)
        CalcMaxAISByLimitWithFlag(self.medical_criteria["Abdominal"]["VCAbdomenFrontal"], 0, 25)

        # calc formulas combination
        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Abdominal"]["FmaxSideV1"],
                                                       self.medical_criteria["Abdominal"]["VCAbdomenSide"],
                                                       self.medical_criteria["Abdominal"]["VCAbdomenFrontal"]])

        return aisFormula, aisFormula_prob

    def calc_ais_pelvic(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Pelvic"]["PSPFSide"], 20, 25)
        CalcMaxAISByLimitWithFlag(self.medical_criteria["Pelvic"]["PSPFSideSens"], 0, 25)

        # calc formulas combination
        aisFormula, aisFormula_prob = CombineFormulas([self.medical_criteria["Pelvic"]["PSPFSide"]])
        # check other conditions
        if aisFormula <= 1:
            limits = []
            if self.medical_criteria["Pelvic"]["PelvicRearAcc"] is not None:
                limits.append(self.medical_criteria["Pelvic"]["PelvicRearAcc"]["Limit"])
            if self.medical_criteria["Pelvic"]["PelvicSideAcc"] is not None:
                limits.append(self.medical_criteria["Pelvic"]["PelvicSideAcc"]["Limit"])
            if len(limits) > 0:
                maxLimit = max(limits)
                if maxLimit > 0:
                    aisFormula = aisFormula + 1
                    aisFormula_prob[aisFormula] = 25

        return aisFormula, aisFormula_prob

    def calc_ais_femur(self):
        # calc formulas with limits
        CalcMaxAISWithLimit(self.medical_criteria["Femur"]["PAFFrontalSens"], 15, 20)
        CalcMaxAISWithLimit(self.medical_criteria["Femur"]["PAFFrontal"], 15, 20)

        return CombineFormulas([self.medical_criteria["Femur"]["PAFFrontal"]])

    def run_decision_tree(self):
        self.medical_criteria["Head"]["AIS"], self.medical_criteria["Head"]["P(AIS)"] = self.calc_ais_head()
        self.medical_criteria["Neck"]["AIS"], self.medical_criteria["Neck"]["P(AIS)"] = self.calc_ais_neck()
        self.medical_criteria["Chest"]["AIS"], self.medical_criteria["Chest"]["P(AIS)"] = self.calc_ais_chest()
        self.medical_criteria["Abdominal"]["AIS"], self.medical_criteria["Abdominal"]["P(AIS)"] = self.calc_ais_abdominal()
        self.medical_criteria["Pelvic"]["AIS"], self.medical_criteria["Pelvic"]["P(AIS)"] = self.calc_ais_pelvic()
        self.medical_criteria["Femur"]["AIS"], self.medical_criteria["Femur"]["P(AIS)"] = self.calc_ais_femur()

    def run_injuries_mitigation(self):
        if self.mechanism == "Frontal" and self.medical_criteria["Pelvic"]["AIS"] == 0:
            if self.medical_criteria["Femur"]["AIS"] == 2:
                self.medical_criteria["Pelvic"]["AIS"] = 1
                self.medical_criteria["Pelvic"]["P(AIS)"][1] = 20
            elif self.medical_criteria["Femur"]["AIS"] == 3 or self.medical_criteria["Femur"]["AIS"] == 4:
                self.medical_criteria["Pelvic"]["AIS"] = 2
                self.medical_criteria["Pelvic"]["P(AIS)"][2] = 25

        if "Side" in self.mechanism and self.medical_criteria["Femur"]["AIS"] == 0:
            if self.medical_criteria["Pelvic"]["AIS"] == 2:
                self.medical_criteria["Femur"]["AIS"] = 1
                self.medical_criteria["Femur"]["P(AIS)"][1] = 25

            if self.medical_criteria["Pelvic"]["AIS"] > 2:
                self.medical_criteria["Femur"]["AIS"] = 2
                self.medical_criteria["Femur"]["P(AIS)"][2] = 30

    def calc_max_ais(medical_criteria):
        # calculate the max ais from all body regions
        aisList = []
        for key, val in medical_criteria.items():
            if key != "GeneralCalculations" and isinstance(val, dict):
                aisList.append(val["AIS"])

        medical_criteria["GeneralCalculations"]["MaxAis"] = max(aisList)

    def calc_niss(medical_criteria):
        # calculate the 3 highest ais from all body regions
        aisList = [medical_criteria["Head"]["AIS"], medical_criteria["Neck"]["AIS"],
                   medical_criteria["Chest"]["AIS"],
                   medical_criteria["Abdominal"]["AIS"], medical_criteria["Pelvic"]["AIS"],
                   medical_criteria["Femur"]["AIS"]]
        aisList.sort(reverse=True)

        # calculate sqrt of sum of sqrt of the 3 highest ais
        medical_criteria["GeneralCalculations"]["Niss"] = (aisList[0] ** 2 + aisList[1] ** 2 + aisList[2] ** 2)

    def run_post_processing_summary(medical_criteria):
        if medical_criteria is not None:
            medical_criteria["GeneralCalculations"] = {}
            MedicalFormulationCalculation.calc_max_ais(medical_criteria)
            MedicalFormulationCalculation.calc_niss(medical_criteria)

    def Run(self):
        self.calc_all_formulas()
        self.run_decision_tree()
        self.run_injuries_mitigation()
        return self.medical_criteria


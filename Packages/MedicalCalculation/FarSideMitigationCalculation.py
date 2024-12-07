from MedicalCalculation.Common import GetMaxAISByProbFilter
from Utils import DSLogger, LogLevel
import copy

class FarSideMitigationCalculation:
    """
    This model accepts medical criteria and outputs a calculated far side mitigation medical criteria according
    to dummy location
    """
    def __init__(self, mechanism=None, dummyLocation=None, medicalDict=None):
        if mechanism is None:
            raise ValueError("mechanism is undefined.")
        if dummyLocation is None:
            raise ValueError("dummyLocation is undefined.")
        if medicalDict is None:
            raise ValueError("medicalDict is undefined.")

        self.logger = DSLogger("FarSideMitigationCalculation")
        self.Mechanism = mechanism
        self.Location = dummyLocation
        self.FarSideMedicalDict = copy.deepcopy(medicalDict)

        self.logger.PrintLog(LogLevel.Info, "Successfully initialized FarSideMitigationCalculation")

    def RefactorProbability(self, bodyRegion, factor):
        if self.FarSideMedicalDict[bodyRegion] is not None:
            if self.FarSideMedicalDict[bodyRegion]["P(AIS)"] is not None:
                for aisp, probais in self.FarSideMedicalDict[bodyRegion]["P(AIS)"].items():
                    probais = probais + factor
                    if probais < 0:
                        probais = 0
                    elif probais > 100:
                        probais = 100
                    self.FarSideMedicalDict[bodyRegion]["P(AIS)"][aisp] = probais


    def FixAis(self):
        # finds the maximum AIS by filter >=20
        # TODO: Set configurable filter >=20 (default) per body region
        for val in self.FarSideMedicalDict.values():
            # fix ais only for body parts values which are dictionaries
            if isinstance(val, dict) and "P(AIS)" in val.keys():
                maxAis, maxAisP = GetMaxAISByProbFilter(val["P(AIS)"], 30)
                val["AIS"] = maxAis


    def Run(self):
        validFarSideInput1 = self.Mechanism == "SideLeft" and (self.Location == 2 or self.Location == 3)
        validFarSideInput2 = self.Mechanism == "SideRight" and (self.Location == 1 or self.Location == 4)
        if validFarSideInput1 or validFarSideInput2:
            self.logger.PrintLog(LogLevel.Info, "Starting FarSideMitigation refactoring...")

            self.RefactorProbability("Head", -3)
            self.RefactorProbability("Neck", 2)
            self.RefactorProbability("Chest", -13)
            self.RefactorProbability("Pelvic", -3)
            self.RefactorProbability("Femur", -5)
            #self.RefactorProbability("Spine", 2)
            self.RefactorProbability("Abdominal", 10)

            self.logger.PrintLog(LogLevel.Info, "Recalculating MaxAIS after refactoring...")
            self.FixAis()
            self.logger.PrintLog(LogLevel.Info, "FarSideMitigationCalculation has finished successfully")
        else:
            self.logger.PrintLog(LogLevel.Warning, f"Can not run FarSideMitigation on this input. mechanism: "
                                                   f"{self.Mechanism} Location: {self.Location}")

        return self.FarSideMedicalDict



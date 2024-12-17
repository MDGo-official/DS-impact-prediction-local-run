import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import sys

sys.path.append(os.path.abspath(os.path.join(".",os.pardir)))
sys.path.append(os.path.join(".", 'Packages'))
sys.path.append(os.path.join(".", 'Architectures'))

from Packages.CrashDetection import CrashDetection, InjuryLevel
from Packages.VirtualSensors import VS
from Packages.MedicalCalculation import MedicalFormulationCalculation, FarSideMitigationCalculation
from Packages.Damages import DamagesPrediction
from Packages.SignalProcessing import SignalProcessing
from Packages.AirBagDeploy import airbag_deploy
   
folder_name = 'Data/'
# file_name = "63fdf0e17060d1c0a8d93b21.json"
# file_name = "606c2bf94ff42e0002ce4d71.json"
# file_name = "606c447f416c5e0002a96c2d.json"
file_name = "644172bb4c55584206a9d570.json"

# Load JSON data
with open(folder_name+file_name, 'r') as f:
    data = json.load(f)

# Extract accelerometer data and time
acc_x = np.array(data['Acc_X']['Data'])
acc_y = np.array(data['Acc_Y']['Data'])
acc_z = np.array(data['Acc_Z']['Data'])

# data to df
Acc_X=data['Acc_X']['Data']
Acc_Y=data['Acc_Y']['Data']
Acc_Z=data['Acc_Z']['Data']
gyr_x = data['Sensors'][0]['Data']
gyr_y = (data['Sensors'][1]["Data"])
gyr_z = (data['Sensors'][2]["Data"])
rawData_df = pd.DataFrame(np.array([Acc_X,Acc_Y,Acc_Z,gyr_x,gyr_y,gyr_z]).T, columns=["Acc_X","Acc_Y","Acc_Z",'Gyro_X', 'Gyro_Y', 'Gyro_Z'])


calibInfo = {
    #creating matrix for aligned signal
    "OperationalMat": np.eye(3) if file_name == "63fdf0e17060d1c0a8d93b21.json" else np.array([
        [-9.13119776e-01, -2.03933585e-03,  4.07686295e-01],
        [ 2.21042190e-03, -9.99997556e-01, -5.13897804e-05],
        [ 4.07685403e-01,  8.54233690e-04,  9.13122052e-01]
    ]),
    "AxesOrientation": "FLU"
}


offset = [0,0,0]
impactData = {}

impactData['rawData'] = rawData_df.to_dict(orient='list')

# Crash Detection
crashDetectionObj = CrashDetection(".", rawData_df, calibInfo, offset)
crashDict = crashDetectionObj.run() #running crash detection

isCrash, reason = crashDict.get('isCrash')
mechanism = crashDict.get("mechanism")

impactData['IsCrash'] = isCrash
impactData['Dv'] = crashDict.get('DV')
impactData['MaxG'] = crashDict.get('maxG')

if isCrash:
    impactData['Confidence'] = crashDict.get('confidence')
    impactData['Theta'] = crashDict.get('theta')
    impactData['Mechanism'] = mechanism
else:
    impactData['Mechanism'] = "No Crash"

# Virtual Sensors
vs = VS(".", rawData_df, calibInfo, crashDict, offset)
occpVsDict = vs.run()
#impactData['VirtualSensors'] = occpVsDict

# Air Bag deployment
ab_deploy = airbag_deploy.AirBagDeploy(".", rawData_df, calibInfo, crashDict, offset)
ab_deployObj = ab_deploy.run()
impactData['AirBagDeploy'] = ab_deployObj

# Damages
damagesObj = DamagesPrediction(".", rawData_df, calibInfo, crashDict, offset)
damagesResult = damagesObj.run()

impactData['Damages'] = {}
impactData['Damages'] = damagesResult.get('final')

# Injuries
injuryLevelObj = InjuryLevel(".", rawData_df, calibInfo, crashDict, offset)
injuryLevelData = injuryLevelObj.run()
occpDict = impactData['Occupants'] = {}
# run medical criteria for each known occupant
for occKey, occVS in occpVsDict.items():
    occLocation = occKey.split('_')[1]  # get the location
    occpDict[occLocation] = {}
    occpDict[occLocation]['VirtualSensors'] = occVS
    mfc = MedicalFormulationCalculation(mechanism, occVS)
    medicalDict = mfc.Run()
    occpDict[occLocation]['MedicalCriteria'] = medicalDict


def CalcOccFarSideMitigation(occDict, knownOcc, unknownOcc):
    if occDict is None:
        raise ValueError("occDict is not defined.")
    if knownOcc is None:
        raise ValueError("knownOcc is not defined.")
    if unknownOcc is None:
        raise ValueError("unknownOcc is not defined.")

    try:
        # get known medical criteria
        if knownOcc in occDict.keys():
            medCriteria = occDict[knownOcc].get('MedicalCriteria')
            # calculate FarSideMitigation for unknown occupant
            fsmc = FarSideMitigationCalculation(mechanism, int(unknownOcc), medCriteria)
            farSideDict = fsmc.Run()
            occDict[unknownOcc] = {'MedicalCriteria': farSideDict}
        else:
            raise Exception(f"Occupant {knownOcc} is missing medical criteria.")
    except Exception as ex:
        msg = ex.message if hasattr(ex, 'message') else str(ex.args)
        raise Exception(f"Error while calculating far side mitigation: {msg}")


# run FarSideMitigation only for Side crash
if mechanism == "SideLeft":
    CalcOccFarSideMitigation(occpDict, "1", "2")
    CalcOccFarSideMitigation(occpDict, "4", "3")
elif mechanism == "SideRight":
    CalcOccFarSideMitigation(occpDict, "2", "1")
    CalcOccFarSideMitigation(occpDict, "3", "4")
    
# run Post Process calculations for each occupant
for occVal in occpDict.values():
    MedicalFormulationCalculation.run_post_processing_summary(occVal["MedicalCriteria"])


# Function to save impactData to JSON files
def save_impact_data(impactData):
    # Ensure the outputs directory exists
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Save the whole impactData dictionary
    with open(os.path.join(output_dir, "impactData_full.json"), "w") as f:
        json.dump(impactData, f, indent=4)

# Call the function to save data
save_impact_data(impactData)

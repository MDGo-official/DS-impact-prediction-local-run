import numpy as np

Mongo_ID_Field_Name = "_id"
Mongo_Parent_ID_Field_Name = "ParentId"

Mongo_InitialCalibration_Field_Name = "InitialCalibration"
Mongo_ResetPI_Field_Name = "ResetPhysicalInsightHistory"
Mongo_ResetCalibration_Field_Name = "ResetCalibrationHistory"

CalibrationInfo_SubDocument_Field_Name = "CalibrationInfo"
OnWindshieldInfo_SubDocument_Field_Name = "OnWindshieldData"

VehicleType_SubDocument_Field_Name = "VehicleType"

Reset_Behavior_Ignore_History = "IgnoreHistory"
Reset_Behavior_Ignore_Current = "IgnoreCurrent"

DEFAULT_CLIBRATION_SENSEID = "default"
DEFAULT_EFS_SENSEID = "default"

Events_MongoDB_Collection = "Events"
Raw_Data_MongoDB_Collection = "RawData"
Insights_MongoDB_Collection = "Insights"
Insights_Data_MongoDB_Collection = "InsightsData"

SenseDevices_MongoDB_Collection = "SenseDevices"
SenseUpdates_MongoDB_Collection = "SenseUpdates"
CalibrationData_MongoDB_Collection = "CalibrationData"
PhysicalInsight_MongoDB_Collection = "PhysicalInsightData"

Source_Field = "Source"
SupportTool_Source = "SupportTool"

def validateObject(originalValue):
    if isinstance(originalValue, dict):
        return {str(key): validateObject(val) for key, val in originalValue.items()}

    if isinstance(originalValue, list):
        return [validateObject(item) for item in originalValue]

    elif isinstance(originalValue, np.float32):
        return float(originalValue)

    return originalValue

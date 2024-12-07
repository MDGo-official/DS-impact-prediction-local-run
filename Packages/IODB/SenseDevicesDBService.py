from Utils import DSLogger, LogLevel
from IODB import *
from IODB.CommonConstants import *
from IODB.HybridCollectionService import *
from IODB.SortingOption import *
from IODB.ResetHistoryUtil import *

class SenseDevicesDBService:

    def __init__(self, mongo_connection):
        if mongo_connection is None:
            raise ValueError("MongoDB connection is not defined")

        self.logger = DSLogger("SenseDevicesDBService")

        self.devicesColl = MongoDBService(mongo_connection, SenseDevices_MongoDB_Collection)
        self.updatesColl = HybridCollectionService(mongo_connection, SenseUpdates_MongoDB_Collection)
        self.physicalInsightColl = MongoDBService(mongo_connection, PhysicalInsight_MongoDB_Collection)
        self.logger.PrintLog(LogLevel.Info, "Successfully initialized SenseDevicesDBService")

    def GetSenseDevice(self, sense_id):
        if sense_id is None:
            raise ValueError("Device's ID is not defined")

        try:
            return self.devicesColl.LoadDocuments({"SenseID": sense_id})[0]
        except Exception as ex:
            msg = f"Failed to load SenseDevice by its ID '{sense_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetSenseUpdateById(self, update_id):
        if update_id is None:
            raise ValueError("Update's ID is not defined")

        try:
            return self.updatesColl.LoadDocumentById(update_id)
        except Exception as ex:
            msg = f"Failed to load update by its ID '{update_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def InsertSenseUpdate(self, update_json):
        if update_json is None:
            raise ValueError("Update data is not defined")

        try:
            return self.updatesColl.InsertDocument(update_json)
        except Exception as ex:
            msg = "Failed to insert new sense update"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetCalibrationHistory(self, sense_id, event_time, objectsCountlimit=None):
        if sense_id is None:
            raise ValueError("SenseID is not defined")
        if event_time is None:
            raise ValueError("EventTime is not defined")
        if objectsCountlimit is None or objectsCountlimit < 1:
            objectsCountlimit = 200

        try:
            resetCalibrationField = f"{OnWindshieldInfo_SubDocument_Field_Name}.{Mongo_ResetCalibration_Field_Name}"
            query = {
                "SenseID": sense_id,
                "TriggeredDate": {"$lt": event_time},
                "$or": [
                    {CalibrationInfo_SubDocument_Field_Name: {"$ne": None}},
                    {
                        OnWindshieldInfo_SubDocument_Field_Name: {"$exists": True},
                        resetCalibrationField: {"$exists": True}
                    },
                    {Mongo_ResetPI_Field_Name: {"$ne": None}}
                ]
            }
            histArr = self.physicalInsightColl.LoadDocuments(query, objectsCountlimit,
                                                             sorting=SortingOption("TriggeredDate"))

            finalResult = list()
            for physicalInsightObj in histArr:
                if OnWindshieldInfo_SubDocument_Field_Name in physicalInsightObj and \
                        Mongo_ResetCalibration_Field_Name in physicalInsightObj[OnWindshieldInfo_SubDocument_Field_Name] and \
                            physicalInsightObj[OnWindshieldInfo_SubDocument_Field_Name][Mongo_ResetCalibration_Field_Name] is not None:

                    resetObj = physicalInsightObj[OnWindshieldInfo_SubDocument_Field_Name][Mongo_ResetCalibration_Field_Name]
                    isFlagValid, ignoreCurrent = ResetHistoryUtil.IsResetNeeded(resetObj)

                    if isFlagValid:
                        if not ignoreCurrent and CalibrationInfo_SubDocument_Field_Name in physicalInsightObj:
                            finalResult.append(physicalInsightObj[CalibrationInfo_SubDocument_Field_Name])

                        # stop appending
                        break

                if Mongo_ResetPI_Field_Name in physicalInsightObj and \
                        physicalInsightObj[Mongo_ResetPI_Field_Name] is not None:
                    resetObj = physicalInsightObj[Mongo_ResetPI_Field_Name]
                    isFlagValid, ignoreCurrent = ResetHistoryUtil.IsResetNeeded(resetObj)
                    if isFlagValid:
                        if not ignoreCurrent and CalibrationInfo_SubDocument_Field_Name in physicalInsightObj:
                            finalResult.append(physicalInsightObj[CalibrationInfo_SubDocument_Field_Name])

                        # stop appending
                        break

                if CalibrationInfo_SubDocument_Field_Name in physicalInsightObj:
                    finalResult.append(physicalInsightObj[CalibrationInfo_SubDocument_Field_Name])

            vehicleType = None  # TODO: get vehicle type from sense device
            if len(finalResult) == 0:
                # return default DeviceExamination
                query = {
                    "SenseID": DEFAULT_EFS_SENSEID,
                    "$or": [
                        {VehicleType_SubDocument_Field_Name: {"$exists": False}},
                        {VehicleType_SubDocument_Field_Name: vehicleType},
                    ]
                }
                histArr = self.physicalInsightColl.LoadDocuments(query, sorting=SortingOption(
                    VehicleType_SubDocument_Field_Name))
                if len(histArr) > 0:
                    self.logger.PrintLog(LogLevel.Info,
                                         "Did not found Calibration history. Will use default Calibration instead")
                    if CalibrationInfo_SubDocument_Field_Name in histArr[0]:
                        finalResult.append(histArr[0][CalibrationInfo_SubDocument_Field_Name])
                else:
                    self.logger.PrintLog(LogLevel.Warning,
                                         "Did not found Calibration history and neither default Calibration.")
            else:
                self.logger.PrintLog(LogLevel.Info,
                                     f"{len(histArr)} Calibration object found as history for {sense_id}")

            return finalResult

        except Exception as ex:
            msg = f"Failed to load CalibrationData object by SenseID '{sense_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetCurrentCalibrationData(self, calib_type, id):
        if calib_type is None:
            raise ValueError("calib_type is not defined")
        if id is None:
            raise ValueError("id is not defined")

        try:
            if calib_type == "Event":
                collection = "Events"
            elif calib_type == "KA":
                collection = "SenseUpdates"
            else:
                raise Exception("Unknown calibration type")
            query = {"TriggeredBy": {"Ref": collection, "Id": id},
                     CalibrationInfo_SubDocument_Field_Name: {"$ne": None}}
            self.logger.PrintLog(LogLevel.Info,
                                 f"Searching for calibration object on {id} from {collection} collection")

            histArr = self.physicalInsightColl.LoadDocuments(query, 50, sorting=SortingOption("TriggeredDate"))

            vehicleType = None  # TODO: get vehicle type from sense device
            if len(histArr) == 0:
                # return default calibration
                query = {
                    "SenseID": DEFAULT_EFS_SENSEID,
                    "$or": [
                        {VehicleType_SubDocument_Field_Name: {"$exists": False}},
                        {VehicleType_SubDocument_Field_Name: vehicleType},
                    ]
                }
                histArr = self.physicalInsightColl.LoadDocuments(query, sorting=SortingOption(
                    VehicleType_SubDocument_Field_Name))
                if len(histArr) > 0:
                    self.logger.PrintLog(LogLevel.Info,
                                         "Did not found calibration history. Will use default calibration instead")
                else:
                    self.logger.PrintLog(LogLevel.Warning,
                                         "Did not found calibration history and neither default calibration.")
            else:
                self.logger.PrintLog(LogLevel.Info,
                                     f"{len(histArr)} calibration object found as history for {calib_type} - {id}")

            for physicalInsightObj in histArr:
                if physicalInsightObj[CalibrationInfo_SubDocument_Field_Name] is not None:
                    return physicalInsightObj[CalibrationInfo_SubDocument_Field_Name]
                if Mongo_InitialCalibration_Field_Name in physicalInsightObj[CalibrationInfo_SubDocument_Field_Name]:
                    # stops appending later calibration
                    break

            self.logger.PrintLog(LogLevel.Warning, f'No valid object found for {collection} {id}')
            return None

        except Exception as ex:
            msg = f"Failed to load CurrentCalibrationData by its type {calib_type} and id '{id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetOnWindshieldHistory(self, sense_id, event_time, objects_count_limit=None):
        if sense_id is None:
            raise ValueError("SenseID is not defined")
        if event_time is None:
            raise ValueError("EventTime is not defined")
        if objects_count_limit is None or objects_count_limit < 1:
            objects_count_limit = 200

        try:
            query = {
                "SenseID": sense_id,
                "TriggeredDate": {"$lt": event_time},
                "$or": [
                    {OnWindshieldInfo_SubDocument_Field_Name: {"$ne": None}},
                    {Mongo_ResetPI_Field_Name: {"$exists": True}}
                ]
            }
            histArr = self.physicalInsightColl.LoadDocuments(query, objects_count_limit,
                                                             sorting=SortingOption("TriggeredDate", False))

            finalResult = list()
            for onWindshieldObj in histArr:

                if Mongo_ResetPI_Field_Name in onWindshieldObj and \
                        onWindshieldObj[Mongo_ResetPI_Field_Name] is not None:

                    resetObj = onWindshieldObj[Mongo_ResetPI_Field_Name]
                    isFlagValid, ignoreCurrent = ResetHistoryUtil.IsResetNeeded(resetObj)
                    if isFlagValid:
                        if not ignoreCurrent and OnWindshieldInfo_SubDocument_Field_Name in onWindshieldObj:
                            finalResult.append(onWindshieldObj[OnWindshieldInfo_SubDocument_Field_Name])

                        # stop appending
                        break

                if OnWindshieldInfo_SubDocument_Field_Name in onWindshieldObj:
                    if Mongo_ResetCalibration_Field_Name in onWindshieldObj[OnWindshieldInfo_SubDocument_Field_Name] and \
                            onWindshieldObj[OnWindshieldInfo_SubDocument_Field_Name][Mongo_ResetCalibration_Field_Name] is not None and \
                            onWindshieldObj[OnWindshieldInfo_SubDocument_Field_Name][Mongo_ResetCalibration_Field_Name][Source_Field] == SupportTool_Source:
                        continue
                    finalResult.append(onWindshieldObj[OnWindshieldInfo_SubDocument_Field_Name])

            vehicleType = None  # TODO: get vehicle type from sense device
            if len(finalResult) == 0:
                # return default DeviceExamination
                query = {
                    "SenseID": DEFAULT_EFS_SENSEID,
                    "$or": [
                        {VehicleType_SubDocument_Field_Name: {"$exists": False}},
                        {VehicleType_SubDocument_Field_Name: vehicleType},
                    ]
                }
                histArr = self.physicalInsightColl.LoadDocuments(query, sorting=SortingOption(
                    VehicleType_SubDocument_Field_Name))
                if len(histArr) > 0:
                    self.logger.PrintLog(LogLevel.Info,
                                         "Did not found OnWindshield history. Will use default OnWindshield instead")
                    if OnWindshieldInfo_SubDocument_Field_Name in histArr[0]:
                        finalResult.append(histArr[0][OnWindshieldInfo_SubDocument_Field_Name])
                else:
                    self.logger.PrintLog(LogLevel.Warning,
                                         "Did not found OnWindshield history and neither default OnWindshield.")
            else:
                self.logger.PrintLog(LogLevel.Info,
                                     f"{len(histArr)} OnWindshield object found as history for {sense_id}")

            return finalResult

        except Exception as ex:
            msg = f"Failed to load onWindshieldData object by SenseID '{sense_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def InsertPhysicalInsightData(self, physicalInsight_json):
        if physicalInsight_json is None:
            raise ValueError("PhysicalInsight data is not defined")

        try:
            return self.physicalInsightColl.InsertDocument(physicalInsight_json)
        except Exception as ex:
            msg = "Failed to insert new physicalInsight data"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def InsertSenseDevice(self, senseDevice_json):
        if senseDevice_json is None:
            raise ValueError("SenseDevice data is not defined")

        try:
            return self.devicesColl.InsertDocument(senseDevice_json)
        except Exception as ex:
            msg = "Failed to insert new SenseDevice data"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetSensePhysicalInsights(self, sense_id, event_time, objects_count_limit=None):
        if sense_id is None:
            raise ValueError("SenseID is not defined")

        if objects_count_limit is None or objects_count_limit < 1:
            objects_count_limit = 200

        try:
            query = {
                "SenseID": sense_id,
                "TriggeredDate": {"$lt": event_time}
            }
            histArr = self.physicalInsightColl.LoadDocuments(query, objects_count_limit,
                                                             sorting=SortingOption("TriggeredDate", False))

            if len(histArr) > 0:
                self.logger.PrintLog(LogLevel.Info,
                                         f"{len(histArr)} PhysicalInsight objects found as history for {sense_id}")
            else:
                self.logger.PrintLog(LogLevel.Warning,
                                     "Did not found PhysicalInsight history for {sense_id}.")

            return histArr

        except Exception as ex:
            msg = f"Failed to load PhysicalInsight objects by SenseID '{sense_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def DeleteSenseDevice(self, sense_id):
        if sense_id is None:
            raise ValueError("SenseID is not defined")

        try:
            query = { "SenseID": sense_id }

            self.devicesColl.DeleteDocuments(query)

        except Exception as ex:
            msg = f"Failed to delete PhysicalInsight objects by SenseID '{sense_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def DeletePysicalInsightsForSense(self, sense_id):
        if sense_id is None:
            raise ValueError("SenseID is not defined")

        try:
            query = { "SenseID": sense_id }

            self.physicalInsightColl.DeleteDocuments(query)

        except Exception as ex:
            msg = f"Failed to delete PhysicalInsight objects by SenseID '{sense_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)
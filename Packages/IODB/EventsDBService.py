from Utils import DSLogger, LogLevel
from IODB.HybridCollectionService import HybridCollectionService
from IODB.MongoDBService import MongoDBService
from IODB.CommonConstants import *


class EventsDBService:

    def __init__(self, mongo_connection):
        if mongo_connection is None:
            raise ValueError("MongoDB connection is not defined")

        self.logger = DSLogger("EventsDBService")
        self.EventsColl = MongoDBService(mongo_connection, Events_MongoDB_Collection)
        self.RawDataColl = HybridCollectionService(mongo_connection, Raw_Data_MongoDB_Collection)
        self.InsightsColl = MongoDBService(mongo_connection, Insights_MongoDB_Collection)
        self.InsDataColl = HybridCollectionService(mongo_connection, Insights_Data_MongoDB_Collection)

        self.logger.PrintLog(LogLevel.Info, "Successfully initialized EventsDBService")

    def GetEventMetaData(self, _id):
        if _id is None:
            raise ValueError("Events's _id is not defined")

        try:
            return self.EventsColl.LoadDocumentById(_id)
        except Exception as ex:
            msg = f"Failed to load event by _id '{_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetEventRawData(self, parent_id):
        if parent_id is None:
            raise ValueError("Parent's ID is not defined")

        try:
            return self.RawDataColl.LoadDocumentsByParentId(parent_id)[0]
        except Exception as ex:
            msg = f"Failed to load RawData by event's ID '{parent_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def CreateInsight(self, parent_id, insight):
        if parent_id is None:
            raise ValueError("Parent's ID is not defined")
        if insight is None or type(insight) is not dict:
            raise ValueError("The received insight is not defined or not a valid dictionary")

        try:
            return self.InsightsColl.InsertDocument(insight, parent_id)
        except Exception as ex:
            msg = "Failed to insert new insight"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def UpdateInsight(self, insight_id, fieldsDict):
        if insight_id is None:
            raise ValueError("The insight's ID is not defined")
        if fieldsDict is None or type(fieldsDict) is not dict:
            raise ValueError("The fieldsDict is not defined or not a valid dictionary")

        try:
            self.InsightsColl.UpdateFields(insight_id, fieldsDict)
        except Exception as ex:
            msg = "Failed to update insight"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def InsertRelatedData(self, insight_id, data):
        if insight_id is None:
            raise ValueError("The insight's ID is not defined")
        if data is None or type(data) is not dict:
            raise ValueError("The received insight is not defined or not a valid dictionary")

        try:
            return self.InsDataColl.InsertDocument(data, insight_id)
        except Exception as ex:
            msg = f"Failed to insert related data on '{insight_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReplaceRelatedData(self, insightData_id, data, insightId):
        if insightData_id is None:
            raise ValueError("The insight data ID is not defined")
        if data is None or type(data) is not dict:
            raise ValueError("The data is not defined or not a valid dictionary")

        try:
            self.InsDataColl.ReplaceDocument(insightData_id, data, insightId)
        except Exception as ex:
            msg = "Failed to update insight"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReadInsight(self, event_id, insight_type, algo_version):
        if event_id is None:
            raise ValueError("Event's ID is not defined")
        if insight_type is None:
            raise ValueError("Insight's type is not defined")
        if algo_version is None:
            raise ValueError("The algorithm's version is not defined")

        try:
            query = {
                Mongo_Parent_ID_Field_Name: event_id,
                "AlgoVersion": algo_version,
                "InsightType": insight_type
            }
            insightsList = self.InsightsColl.LoadDocuments(query)

            if len(insightsList) > 1:
                raise Exception(f"More than 1 insights ({len(insightsList)}) found for event '{event_id}' of type {insight_type} versioned {algo_version}")
            if not insightsList:
                return None

            return insightsList[0]

        except Exception as ex:
            msg = f"Failed to load insight for event '{event_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReadLatestInsight(self, event_id, insight_type):
        if event_id is None:
            raise ValueError("Event's ID is not defined")
        if insight_type is None:
            raise ValueError("Insight's type is not defined")

        # Need to add implementation for latest version

        try:
            query = {
                Mongo_Parent_ID_Field_Name: event_id,
                "InsightType": insight_type
            }

            insightsList = self.InsightsColl.LoadDocuments(query)

            if not insightsList:
                return None

            return insightsList[0]

        except Exception as ex:
            msg = f"Failed to load insight for event '{event_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReadRelatedData(self, insight_id):
        if insight_id is None:
            raise ValueError("Insight's ID is not defined")

        try:
            return self.InsDataColl.LoadDocumentsByParentId(insight_id)
        except Exception as ex:
            msg = f"Failed to load insight's data for insight's ID '{insight_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReadRelatedDataById(self, insightData_id):
        if insightData_id is None:
            raise ValueError("insightData _id is not defined")

        try:
            return self.InsDataColl.LoadDocumentById(insightData_id)
        except Exception as ex:
            msg = f"Failed to load insight data by _id '{insightData_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetEventsDeviceHistory(self, device_id, start_time, end_time, insightType):
        if device_id is None:
            raise ValueError("Device's ID is not defined")

        try:
            query = {
                "DeviceID": device_id,
                "ReceivingTime": {"$lte": end_time,"$gte": start_time}
            }
            eventsList = self.EventsColl.LoadDocuments(query)

            if not eventsList:
                self.logger.PrintLog(LogLevel.Info,f"Did not found events history for {device_id}")
                return None

            self.logger.PrintLog(LogLevel.Info,f"{len(eventsList)} events object found as history for {device_id}")
            finalResult = list()
            for eventObj in eventsList:
                _id = eventObj.get(Mongo_ID_Field_Name)
                eventHistoryObj = {}
                eventHistoryObj['EventID'] = _id
                eventHistoryObj['EventLocation'] = eventObj.get('EventLocation')
                eventHistoryObj['EventTime'] = eventObj.get('EventTime')
                eventHistoryObj['ReceivingTime'] = eventObj.get('ReceivingTime')

                docInsight = self.ReadLatestInsight(_id, insightType)
                if docInsight is None:
                    continue

                eventHistoryObj['IsCrash'] = docInsight.get('IsCrash', 'No')
                finalResult.append(eventHistoryObj)
            return finalResult

        except Exception as ex:
            msg = f"Failed to load event history for device '{device_id}' == {ex}"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def DeleteEventData(self, _id):
        if _id is None:
            raise ValueError("Events's _id is not defined")

        try:
            # delete event
            self.EventsColl.DeleteDocumentById(_id)
            # delete insights and insight_data
            insights_list = self.InsightsColl.LoadDocumentsByParentId(_id)
            for insight in insights_list:
                insight_id = insight.get(Mongo_ID_Field_Name)
                # delete insight
                self.InsightsColl.DeleteDocumentById(insight_id)

                insights_data_list = self.InsDataColl.LoadDocumentsByParentId(insight_id)
                for insight_data in insights_data_list:
                    self.InsDataColl.DeleteDocumentById(insight_data.get(Mongo_ID_Field_Name))

            # delete raw data
            rawData_list = self.RawDataColl.monColl.LoadDocumentsByParentId(_id)
            for rawData in rawData_list:
                rawData_id = rawData.get(Mongo_ID_Field_Name)
                # delete raw data
                self.RawDataColl.DeleteDocumentById(rawData_id)

        except Exception as ex:
            msg = f"Failed to delete event by _id '{_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def InsertEvent(self, event_json):
        if event_json is None:
            raise ValueError("Event data is not defined")

        try:
            return self.EventsColl.InsertDocument(event_json)
        except Exception as ex:
            msg = "Failed to insert new Event data"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def GetEventsByEventID(self, event_id):
        if event_id is None:
            raise ValueError("Event's ID is not defined")

        try:
            query = {
                "EventID": event_id
            }
            eventsList = self.EventsColl.LoadDocuments(query)

            if not eventsList:
                self.logger.PrintLog(LogLevel.Info,f"Did not found events for event id : {event_id}")
                return None

            return eventsList
        except Exception as ex:
            msg = f"Failed to load events for event id '{event_id}' == {ex}"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)
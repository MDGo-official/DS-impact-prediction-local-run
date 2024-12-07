from bson.objectid import ObjectId
from Utils import DSLogger, LogLevel
from IODB.CommonConstants import *
from IODB.CollectionServiceBase import CollectionServiceBase
from IODB.SortingOption import SortingOption
from pymongo import DESCENDING, ASCENDING


class MongoDBService(CollectionServiceBase):

    def __init__(self, mongo_connection, collection_name, sorting = None):
        if mongo_connection is None:
            raise ValueError("MongoDB connection is not defined")
        if collection_name is None:
            raise ValueError("Collection name is not defined")

        self.logger = DSLogger("MongoDBService")
        self.CollectionName = collection_name
        self.Collection = mongo_connection.DbClient.get_collection(collection_name)
        self.DefaultSorting = sorting

    def InsertDocument(self, doc, parent_id=None):
        if doc is None or type(doc) is not dict:
            raise ValueError("The received document value is not defined or not a valid dictionary")

        try:
            self.logger.PrintLog(LogLevel.Info, "Inserting document")
            if parent_id is not None:
                doc[Mongo_Parent_ID_Field_Name] = parent_id

            doc = validateObject(doc)
            self.Collection.insert_one(doc)
            doc[Mongo_ID_Field_Name] = str(doc[Mongo_ID_Field_Name])
            return doc[Mongo_ID_Field_Name]

        except Exception as ex:
            msg = "Failed to insert document"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReplaceDocument(self, mongoId, doc, parent_id=None):
        if mongoId is None:
            raise ValueError("mongoId is not defined")
        if doc is None or type(doc) is not dict:
            raise ValueError("The received document value is not defined or not a valid dictionary")

        try:
            queryFilter = { Mongo_ID_Field_Name: ObjectId(mongoId) }
            self.logger.PrintLog(LogLevel.Info,f"Updating document with id '{mongoId}'")
            if parent_id is not None:
                doc[Mongo_Parent_ID_Field_Name] = parent_id
            doc = validateObject(doc)
            self.Collection.replace_one(queryFilter, doc)
        except Exception as ex:
            msg = f"Failed to replace document '{mongoId}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def UpdateField(self, mongoId, field_name, value):
        if mongoId is None:
            raise ValueError("mongoId is not defined")
        if field_name is None:
            raise ValueError("Field name to update is not defined")
        if value is None:
            raise ValueError("New value to update is not defined")

        try:
            filter = { Mongo_ID_Field_Name: ObjectId(mongoId) }
            value = validateObject(value)
            update = {'$set': {field_name: value} }
            self.logger.PrintLog(LogLevel.Info,f"Updating '{field_name}' on id '{mongoId}'")

            self.Collection.update_one(filter, update)
        except Exception as ex:
            msg = f"Failed to update field '{field_name}' on document '{mongoId}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def UpdateFields(self, mongoId, fieldsDict):
        if mongoId is None:
            raise ValueError("mongoId is not defined")
        if fieldsDict is None or not isinstance(fieldsDict, dict) or len(fieldsDict.items()) == 0:
            raise ValueError("fieldsDict is not defined or not a valid dictionary")

        try:
            filter = { Mongo_ID_Field_Name: ObjectId(mongoId) }
            validatedDic = validateObject(fieldsDict)

            self.logger.PrintLog(LogLevel.Info, f"Updating fields on id '{mongoId}'")
            setQuery = {"$set": validatedDic}
            self.Collection.update_one(filter, setQuery)
        except Exception as ex:
            msg = f"Failed to update fields on document '{mongoId}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def LoadDocumentsByParentId(self, parent_id):
        if parent_id is None:
            raise ValueError("Parent's ID for reading event is not defined")

        try:
            query = { Mongo_Parent_ID_Field_Name: parent_id }
            return self.LoadDocuments(query)

        except Exception as ex:
            msg = f"Failed to load document by parent ID '{parent_id}' from collection '{self.CollectionName}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def LoadDocumentById(self, mongoId):
        if mongoId is None:
            raise ValueError("MongoDB ID for reading event is not defined")

        try:
            self.logger.PrintLog(LogLevel.Info, f"Loading document '{mongoId}' from collection '{self.CollectionName}'")
            query = {Mongo_ID_Field_Name: ObjectId(mongoId)}
            resultsArr = self.LoadDocuments(query)
            if len(resultsArr) == 0:
                self.logger.PrintLog(LogLevel.Warning, f"Document {mongoId} was not found in {self.CollectionName}!")
                return None

            return resultsArr[0]

        except Exception as ex:
            msg = f"Failed to load document by id '{mongoId}' from collection '{self.CollectionName}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def LoadDocuments(self, query, limitAmount = None, sorting = None):
        if query is None:
            raise ValueError("The received query is not defined")

        self.logger.PrintLog(LogLevel.Info, f"Running query: {query}")
        dbResults = self.Collection.find(query)

        sort = self.DefaultSorting if sorting is None else sorting
        if sort is not None:
            if sort.SortBy is not None:
                if sort.IsAscending:
                    self.logger.PrintLog(LogLevel.Info, f"Sort query results by ASCENDING order...")
                    dbResults = dbResults.sort(sort.SortBy, ASCENDING)
                else:
                    self.logger.PrintLog(LogLevel.Info, f"Sort query results by DESCENDING order...")
                    dbResults = dbResults.sort(sort.SortBy, DESCENDING)

        if limitAmount is not None:
            dbResults = dbResults.limit(limitAmount)

        result = self.__query2Eventlist(dbResults)

        return result

    def __query2Eventlist(self, query):
        event_list = []
        for result in query:
            result[Mongo_ID_Field_Name] = str(result[Mongo_ID_Field_Name])
            event_list.append(result)

        return event_list

    def DeleteDocuments(self, query):
        if query is None:
            raise ValueError("The received query is not defined")

        try:
            self.logger.PrintLog(LogLevel.Info, f"Running query: {query}")
            self.Collection.delete_many(query)
        except Exception as ex:
            msg = f"Failed to delete documents"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def DeleteDocumentById(self, mongoId):
        if mongoId is None:
            raise ValueError("MongoDB ID for deleting event is not defined")

        try:
            query = {Mongo_ID_Field_Name: ObjectId(mongoId)}
            self.logger.PrintLog(LogLevel.Info, f"Running query: {query}")
            self.Collection.delete_one(query)
        except Exception as ex:
            msg = f"Failed to delete document"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)
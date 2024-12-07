
from Utils import DSLogger, LogLevel, StorageClient, ReadOnlyStorageClient

from IODB.MongoDBService import MongoDBService
from IODB.CollectionServiceBase import CollectionServiceBase
from IODB.CommonConstants import *


class HybridCollectionService(CollectionServiceBase):

    def __init__(self, mongo_connection, collection_name):
        if mongo_connection is None:
            raise ValueError("MongoDB connection is not defined")
        if collection_name is None:
            raise ValueError("Collection name is not defined")

        self.logger = DSLogger("HybridCollectionService")
        self.BucketName = mongo_connection.Bucket
        self.Cluster = mongo_connection.Cluster
        self.Database = mongo_connection.Database
        self.CollectionName = collection_name
        self.monColl = MongoDBService(mongo_connection, collection_name)
        self.storageClient = StorageClient(mongo_connection.Region)

        if mongo_connection.RO_Bucket is not None:
            self.RO_StorageClient = ReadOnlyStorageClient(mongo_connection.RO_Region)
            self.RO_Cluster = mongo_connection.RO_Cluster
            self.RO_Bucket = mongo_connection.RO_Bucket
            self.RO_DBName = mongo_connection.RO_DBName
        else:
            self.RO_StorageClient = None
            self.RO_Cluster = None
            self.RO_Bucket = None
            self.RO_DBName = None

    def InsertDocument(self, doc, parent_id=None):
        if doc is None or type(doc) is not dict:
            raise ValueError("The received document value is not defined or not a valid dictionary")

        try:
            self.logger.PrintLog(LogLevel.Info, "Inserting document")
            if parent_id is not None:
                doc[Mongo_Parent_ID_Field_Name] = parent_id

            doc = validateObject(doc)
            monDoc = self.__filterMongoDoc(doc)
            newId = self.monColl.InsertDocument(monDoc, parent_id)
            self.storageClient.StoreJsonFile(self.BucketName, self.__getWriteStorageKey(newId), doc)
            self.logger.PrintLog(LogLevel.Info, "Successfully stored document")
            return newId
        except Exception as ex:
            msg = "Failed to insert document"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def ReplaceDocument(self, mongoId, doc, parent_id = None):
        if mongoId is None:
            raise ValueError("The given ID is not defined")
        if doc is None or type(doc) is not dict:
            raise ValueError("The received document value is not defined or not a valid dictionary")

        try:
            self.logger.PrintLog(LogLevel.Info, "Replacing document")
            if parent_id is not None:
                doc[Mongo_Parent_ID_Field_Name] = parent_id
            doc = validateObject(doc)
            monDoc = self.__filterMongoDoc(doc)
            self.monColl.ReplaceDocument(mongoId, monDoc)

            self.storageClient.StoreJsonFile(self.BucketName, self.__getWriteStorageKey(mongoId), doc)
            self.logger.PrintLog(LogLevel.Info, "Successfully replaced document")
        except Exception as ex:
            msg = f"Failed to replace document '{mongoId}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)


    def LoadDocumentsByParentId(self, parent_id):
        if parent_id is None:
            raise ValueError("The given ID is not defined")

        try:
            self.logger.PrintLog(LogLevel.Info, f"Loading documents by parent ID '{parent_id}'")

            docsList = self.monColl.LoadDocumentsByParentId(parent_id)
            loadedDocsList = []
            for doc in docsList:
                loadedDocsList.append(self.__getJsonFileFromStorage(doc[Mongo_ID_Field_Name]))

            self.logger.PrintLog(LogLevel.Info, f"found '{len(loadedDocsList)}' documents")
            return loadedDocsList
        except Exception as ex:
            msg = f"Failed to load documents by parent ID '{parent_id}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def LoadDocumentById(self, mongoId):
        if mongoId is None:
            raise ValueError("The given ID is not defined")

        try:
            self.logger.PrintLog(LogLevel.Info, f"Loading document '{mongoId}' from '{self.CollectionName}'")
            return self.__getJsonFileFromStorage(mongoId)

        except Exception as ex:
            msg = f"Failed to load document '{mongoId}'"
            self.logger.PrintLog(LogLevel.Exception, msg)
            raise Exception(msg)

    def __getJsonFileFromStorage(self, jsonKey):
        isExist, obj = self.storageClient.TryGetJsonFile(self.BucketName, self.__getWriteStorageKey(jsonKey))
        if isExist:
            return obj
        elif self.RO_StorageClient is not None:
            return self.RO_StorageClient.GetJsonFile(self.RO_Bucket, self.__getStorageKey(jsonKey, self.RO_DBName, self.RO_Cluster))
        else:
            raise Exception(obj)

    def __getWriteStorageKey(self, mongoId):
        return self.__getStorageKey(mongoId, self.Database, self.Cluster)
    def __getStorageKey(self, mongoId, dbName, clusterName):
        return f"{clusterName}/{dbName}/{self.CollectionName}/{mongoId}.json"


    def __filterMongoDoc(self, originalDoc):
        mongoDoc = {}
        for key, val in originalDoc.items():
            if isinstance(val, dict):
                result = self.__filterMongoDoc(val)
                if len(result.keys()) != 0:
                    mongoDoc[key] = result
            else:
                if val is not None and not isinstance(val, list):
                    mongoDoc[key] = val

        return mongoDoc

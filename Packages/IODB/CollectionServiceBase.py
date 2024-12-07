from abc import ABC, abstractmethod


class CollectionServiceBase(ABC):

    @abstractmethod
    def InsertDocument(self, doc):
        pass

    @abstractmethod
    def ReplaceDocument(self, mongoid, doc):
        pass

    @abstractmethod
    def LoadDocumentsByParentId(self, parent_id):
        pass

    @abstractmethod
    def LoadDocumentById(self, mongoid):
        pass

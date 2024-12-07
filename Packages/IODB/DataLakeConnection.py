from pymongo import MongoClient, ReadPreference
from Utils import DSLogger, LogLevel

class DataLakeConnection:

    def __init__(self, connStr, cluster, db, region, bucket, use_secondary=False):
        self.RO_Bucket = None
        self.RO_Region = None
        self.RO_DBName = None
        self.RO_Cluster = None
        if connStr is None:
            raise ValueError("Connsction string is not defined")
        if cluster is None:
            raise ValueError("mongo cluster is not defined")
        if db is None:
            raise ValueError("mongo db is not defined")
        if region is None:
            raise ValueError("region is not defined")
        if bucket is None:
            raise ValueError("storage bucket is not defined")

        self.logger = DSLogger("DataLakeConnection")
        try:
            self.Cluster = cluster
            self.Database = db
            self.Region = region
            self.Bucket = bucket

            readPref = ReadPreference.SECONDARY if  use_secondary else ReadPreference.PRIMARY

            self.Client = MongoClient(connStr)
            self.DbClient = self.Client.get_database(name=db, read_preference=readPref)
        except Exception as ex:
            msg = ex.message if hasattr(ex, 'message') else str(ex.args)
            raise Exception(f"Error while initializing connection to MongoDB: {msg}")

    @classmethod
    def CreateUserNamePwdConnection(cls, cluster, user, pwd, db, region, bucket, use_secondary=False):
        if user is None:
            raise ValueError("mongo user is not defined")
        if pwd is None:
            raise ValueError("mongo password is not defined")

        conn = cls(
            f'mongodb+srv://{str(user)}:{str(pwd)}@{str(cluster)}.mongodb.net/test?retryWrites=true',
            cluster, db, region, bucket, use_secondary
        )
        conn.logger.PrintLog(LogLevel.Info, f"Established connection to MongoDB on '{db}' using username '{user}'")
        return conn

    @classmethod
    def CreateRoleConnection(cls, cluster, db, region, bucket, use_secondary=False):
        conn = cls(
            f'mongodb+srv://{str(cluster)}.mongodb.net/test?retryWrites=true&authSource=$external&authMechanism=MONGODB-AWS',
            cluster, db, region, bucket, use_secondary
        )
        conn.logger.PrintLog(LogLevel.Info, f"Established connection to MongoDB on '{db}' using attached role")
        return conn

    def AddReadOnlyStorageService(self, readonly_region, readonly_bucket, readonly_db_name, readonly_cluster_name):
        self.RO_Region = readonly_region
        self.RO_Bucket = readonly_bucket
        self.RO_DBName = readonly_db_name
        self.RO_Cluster = readonly_cluster_name
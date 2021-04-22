""" DB 연결 및 관리, 생성 하는 모듈

"""
from common.database.mogodb import MongoDBManager
from common.config.configmanager import ConfigManager, DatabaseObject, DatabaseType
from common.util import Singleton


class DatabaseManager(metaclass=Singleton):
    """ 여러 데이터 베이스를 한곳에서 관리하기 위한 Class"""

    def __init__(self):
        # Mongo DB
        self._mongo_db: MongoDBManager = None

        self.database_list: [DatabaseObject] = ConfigManager().database_object_list

        self._load()

    def _load(self):
        for item in self.database_list:
            database: DatabaseObject = item
            if DatabaseType.MONGO == database.database_type:
                self._mongo_db = MongoDBManager(host=database.host,
                                                database=database.database_name,
                                                collection=database.tables,
                                                database_object=database)

            elif DatabaseType.ELASTIC == database.database_type:
                pass
                # self._mongo_db = MongoDBManager(host=database.host,
                #                                 database=database.database_name,
                #                                 collection=database.tables,
                #                                 database_object=database)

            elif DatabaseType.ELASTIC == database.database_type:
                pass

    def close(self):
        """ DB를 닫는다. """
        if self._mongo_db is not None:
            self._mongo_db.close()

    def insert_one_mongo(self, collection: str, value) -> bool:
        """ Insert One Document
        :param value: 저장할 값 (dict)
        :param collection: collection 이름

        collection 이름에 맞춰 DB에 저장

        :return  InsertOneResult """
        return self._mongo_db.insert_one(collection, value)

    def insert_many_mongo(self, collection: str, value) -> bool:
        """ Insert many Document
        :param value: 저장할 값 (dict)
        :param collection: collection 이름

        collection 이름에 맞춰 DB에 저장

        :return InsertManyResult
        """
        return self._mongo_db.insert_many(collection, value)

    def find_all_mongo(self, collection: str):
        """ Find All Documnet
        :param collection: collection 이름

        collection 이름에 맞춰 DB에서 결과 조회

        :return json string
        """
        return self._mongo_db.find_all(collection)

    def delete_one(self, collection, query):
        return self._mongo_db.delete_one(collection, query)

    def update(self, collection, selection, data, is_upsert: bool = True):
        return self._mongo_db.update(collection, selection, data, is_upsert)

    def find(self, collection, query: dict = None):
        return self._mongo_db.find(collection, query)

    def find_one(self, collection, query: dict = None):
        return self._mongo_db.find_one(collection, query)

    def count_document(self, collection, query: dict = None):
        return self._mongo_db.count_document(collection, query)

    def count_document_exists(self, collection, field, value) -> bool:
        return self._mongo_db.count_document(collection, self.find_query(field, value)) > 0

    @staticmethod
    def keyword_query(field, keyword) -> dict:
        return {field: {'$regex': '(?=.*#' + keyword + '#)'}}

    @staticmethod
    def find_query(field, keyword) -> dict:
        return {field: keyword}


db = DatabaseManager()


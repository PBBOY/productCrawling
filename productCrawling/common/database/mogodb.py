""" MongoDB 관리 모듈

MongoDB Client 연결 및 DB에 접근하여 Collection 생성
수집된 데이터를 Insert 하는 모듈
"""

from enum import Enum, auto
from pymongo import MongoClient
from pymongo.database import Database
from common.config.configmanager import DatabaseObject

from urllib.parse import quote_plus


class TableType(Enum):
    """ 테이블 유형 """
    Category = auto()
    Detail = auto()


class MongoDBManager:
    """ MongoDB 관리 클래스

    Attribute

    host URL, Database 이름, Collection 이름
    """
    def __init__(self, host, database, collection, database_object: DatabaseObject = None):
        self.host = host
        self.database = database
        self.collection = collection

        self._url = database_object.server
        # self._port = database_object.port

        self._username = database_object.username
        self._password = database_object.password

        self._client: MongoClient = None

        self.is_connect: bool = False

        self._connect()

    def _connect(self):
        # uri = "mongodb://%s:%s@%s" % (quote_plus(user), quote_plus(password), quote_plus(socket_path))
        # - `username`: A
        # string.
        # - `password`: A
        # string.
        self._client = MongoClient(self.host)

        if self._client is not None:
            self.is_connect = True

            self._db: Database = self._client[self.database]  # db name

    def close(self):
        """MongoDB Close"""
        if self._client is not None:
            self._client.close()

    def update(self, collection: str, selection, data, upsert: bool = True):
        return self._db[collection].update(selection, data, upsert)

    def delete_one(self, collection: str, query: dict):
        return self._db[collection].delete_one(query)

    def insert_one(self, collection: str, value: dict) -> bool:
        """ Insert One Document
        :param value: 저장할 값 (dict)
        :param collection: collection 이름

        collection 이름에 맞춰 DB에 저장

        :return  InsertOneResult """
        if self.is_connect:
            return self._db[collection].insert_one(value)
        return None

    def insert_many(self, collection: str, value):
        """ Insert many Document
        :param value: 저장할 값 (dict)
        :param collection: collection 이름

        collection 이름에 맞춰 DB에 저장

        :return InsertManyResult
        """
        if self.is_connect:
            return self._db[collection].insert_many(value)
        return None

    def find_all(self, collection: str):
        """ Find All Documnet
        :param collection: collection 이름

        collection 이름에 맞춰 DB에서 결과 조회

        :return json string
        """
        if self.is_connect:
            return self._db[collection].find()
        return None

    def find(self, collection, query: dict):
        if self.is_connect:
            return self._db[collection].find(query)

    def find_one(self, collection, query: dict):
        if self.is_connect:
            return self._db[collection].find_one(query)

    def count_document(self, collection, query: dict):
        if self.is_connect:
            return self._db[collection].count_documents(query)

import unittest
import sys
import os
from operator import eq
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.database import Database, Collection
from pymongo.collection import Cursor

baseprojectpath = os.path.dirname(
                os.path.dirname(os.path.dirname(__file__)) 
            )
baseprojectpathexists = False
for syspath in sys.path:
    if baseprojectpath == syspath :
        baseprojectpathexists = True
        break

if not baseprojectpathexists :
    sys.path.append(baseprojectpath)

HOST = "mongodb://192.168.137.223:27017/"


def find_query(field, keyword) -> dict:
    return {field: keyword}


class DatabaseManagerTest(unittest.TestCase):
    def setUp(self):
        self.client: MongoClient = MongoClient(HOST)

        self._db: Database = self.client.crawl_database_test

        self._col: Collection = self._db.category

        self._category_list: list = list(self._col.find())

        print('')

    def tearDown(self):
        # self.client.drop_database("pymongo_db_test")
        self.client.close()
        pass

    def test_find(self):
        keywordquery = {'paths': {'$regex': '(?=.*' + "#컴퓨터#" + ')'}}
        jsons = self._col.find(keywordquery)
        # jsons = self._col.find({"paths": "\\/\\#\\클렌징\\#\\/"})
        # jsons = self._col.find({"name": "클렌징"})

        for item in jsons:
            print('')
            id = item['_id']
            find = self._col.find({"_id": id})
            print('')

        self.assertIsNotNone(jsons)

    def fix_rows(self) -> list:
        result = list()
        _category_document = dict()
        _category_document['cid'] = None
        _category_document['name'] = "가전제품"
        _category_document['paths'] = None
        _category_document['insert_time'] = datetime.now()

        result.append(_category_document)

        _category_document = dict()
        _category_document['cid'] = '50000190'
        _category_document['name'] = "컴퓨터"
        _category_document['paths'] = "가전제품#컴퓨터"
        _category_document['insert_time'] = datetime.now()

        result.append(_category_document)

        _category_document = dict()
        _category_document['cid'] = '50000191'
        _category_document['name'] = "노트북"
        _category_document['paths'] = "가전제품#컴퓨터#노트북"
        _category_document['insert_time'] = datetime.now()

        result.append(_category_document)

        return result

    # def test_update(self):
    #     selection = {"cid": '50000190'}
    #
    #     _update_data = dict()
    #     _update_data['name'] = "컴퓨터"
    #     _update_data['paths'] = "가전제품#컴퓨터"
    #     _update_data['update_time'] = datetime.now()
    #
    #     update = self._col.update_one(selection, {"$set": _update_data})
    #     self.assertTrue(update.acknowledged)

    def test_count_document(self):
        field = 'cid'
        keyword = '50000191'

        # keywordquery = {'paths': {'$regex': '(?=.*' + "#클렌징#" + ')'}}

        count = self._col.count_documents({field: keyword}) > 0
        self.assertTrue(count)

    def _update(self, cid, name, paths: str):
        _query = find_query('cid', cid)

        _update_data = dict()
        _update_data['name'] = name
        _update_data['paths'] = paths
        _update_data['update_time'] = datetime.now()
        return self._col.update_one(_query, {"$set": _update_data}, upsert=True)

    def test_insert_rootItem_Exists_True(self):
        name = "가전제품"
        cid = ""
        is_root = True
        paths = ""

        _exists = False
        for item in self._category_list:
            _name = item['name']
            _cid = item['cid']
            _paths = item['paths']
            if is_root:
                if eq(_name, name):
                    self._category_list.remove(item)
                    _exists = True
                    break
            else:
                if eq(_cid, cid):
                    if eq(_name, name) and eq(_paths, paths):
                        self._category_list.remove(item)
                        _exists = True
                        break
                    else:
                        self._update(cid, name, paths)
                        self._category_list.remove(item)
                        _exists = True
                        break
        # False 면 Insert 진행한다.
        self.assertTrue(_exists)

    def test_insert_rootItem_Exists_False(self):
        name = "가구제품"
        cid = ""
        is_root = True
        paths = ""

        _exists = False
        for item in self._category_list:
            _name = item['name']
            _cid = item['cid']
            _paths = item['paths']
            if is_root:
                if eq(_name, name):
                    self._category_list.remove(item)
                    _exists = True
                    break
            else:
                if eq(_cid, cid):
                    if eq(_name, name) and eq(_paths, paths):
                        self._category_list.remove(item)
                        _exists = True
                        break
                    else:
                        self._update(cid, name, paths)
                        self._category_list.remove(item)
                        _exists = True
                        break

        # False 면 Insert 진행한다.
        self.assertFalse(_exists)

    def test_insert_subItem_Exists_True(self):
        name = "컴퓨터"
        cid = "50000190"
        is_root = False
        paths = "가전제품#컴퓨터"

        _exists = False
        for item in self._category_list:
            _name = item['name']
            _cid = item['cid']
            _paths = item['paths']
            if is_root:
                if eq(_name, name):
                    self._category_list.remove(item)
                    _exists = True
                    break
            else:
                if eq(_cid, cid):
                    if eq(_name, name) and eq(_paths, paths):
                        self._category_list.remove(item)
                        _exists = True
                        break
                    else:
                        self._update(cid, name, paths)
                        self._category_list.remove(item)
                        _exists = True
                        break

        # False 면 Insert 진행한다.
        self.assertTrue(_exists)

    def test_insert_subItem_Exists_True_and_Update(self):
        name = "에어컨"
        cid = "50000190"
        is_root = False
        paths = "가전제품#에어컨"

        _exists = False
        for item in self._category_list:
            _name = item['name']
            _cid = item['cid']
            _paths = item['paths']
            if is_root:
                if eq(_name, name):
                    self._category_list.remove(item)
                    _exists = True
                    break
            else:
                if eq(_cid, cid):
                    if eq(_name, name) and eq(_paths, paths):
                        self._category_list.remove(item)
                        _exists = True
                        break
                    else:
                        # update
                        self._update(cid, name, paths)
                        self._category_list.remove(item)
                        _exists = True
                        break

        # False 면 Insert 진행한다.
        self.assertTrue(_exists)

    # def test_insert_1(self):
    #     rows = self.fix_rows()
    #     x = self._col.insert_many(rows)
    #     self.assertTrue(x.acknowledged)



if __name__ == '__main__':
    unittest.main()

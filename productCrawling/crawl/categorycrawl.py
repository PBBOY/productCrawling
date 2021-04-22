import re
import json
import os
import time
import asyncio
import requests
import logging
from datetime import datetime
from operator import eq

from lxml import html, etree
from lxml.html import HtmlElement

from common.util import Utils
from common.database.dbmanager import DatabaseManager
from common.config.configmanager import CrawlConfiguration, ConfigManager


class CategoryCrawl(object):

    CATEGORY_ID = 50000000  # Default value

    COLLECTION = 'category'
    _DELIMITER = 'category?catId='
    _PATH_TOKEN = '#'
    status: dict = {}

    def __init__(self):
        # 크롤링 설정 정보 관리 - singleton
        self.crawl_config: CrawlConfiguration = ConfigManager().crawl_config
        # Database manager - 데이터 조회 및 저장을 여기서 합니다. - singleton
        self.database_manager = DatabaseManager()

        # 중복 데이터 확인을 위해 미리 저장된 결과 list를 조회한다.
        self._category_list: list = list(self.database_manager.find_all_mongo(self.COLLECTION))
        self.CATEGORY_ID = self.crawl_config.category_id

    def _update(self, cid, name, paths: str):
        # Database manager - 데이터 조회 및 저장을 여기서 합니다. - singleton
        self.database_manager = DatabaseManager()

        _query = self.database_manager.find_query('cid', cid)

        _update_data = dict()
        _update_data['name'] = name
        _update_data['paths'] = paths
        _update_data['update_time'] = datetime.now()

        return self.database_manager.update(self.COLLECTION, _query, {"&set": _update_data})

    def crawl_status(self, cid: str, name: str, status: int):
        self.status = {"status": {
            "message": "Category Crawling Status",
            "cid": cid,
            "name": name,
            "status": status,
            "Remaining count": len(self._category_list),
        }}

        return self.status

    def _insert(self, cid, name, paths: str, is_root: bool = False):
        """ Mongo Database Insert """
        _is_exists: bool = False

        for item in self._category_list:
            _name = item['name']
            _cid = item['cid']
            _paths = item['paths']
            if is_root:
                if eq(_name, name):
                    self._category_list.remove(item)
                    return
            else:
                if eq(_cid, cid):
                    if eq(_name, name) and eq(_paths, paths):
                        self._category_list.remove(item)
                        return
                    else:
                        self._update()
                        self._category_list.remove(item)
                        return

        _category_document = dict()
        _category_document['cid'] = cid
        _category_document['name'] = name
        _category_document['paths'] = paths
        _category_document['insert_time'] = datetime.now()

        return self.database_manager.insert_one_mongo(self.COLLECTION, _category_document)

    def _is_exists(self, field, value: str):
        """MongoDB에 cid 값을 조회하여 조건에 맞는 document가 있는지 확인"""
        _query = self.database_manager.find_query(field, value)
        return self.database_manager.count_document('category', _query) > 0

    def _parse_category(self, element: HtmlElement, root_paths: str):
        ul_tag: HtmlElement = element.find('ul')

        if ul_tag is not None:
            li_tags = ul_tag.findall('li')

            li: HtmlElement
            for li in li_tags:
                li_a_tag = li.find('a')
                if li_a_tag is not None:
                    _name = li_a_tag.text
                    _href = li_a_tag.get('href')
                    _cid = Utils.separate_right(_href, self._DELIMITER)
                    _paths = Utils.join_path(self._PATH_TOKEN, root_paths, _name)

                    self._insert(_cid, _name, _paths)
                    div_tag = li.find('div')
                    if div_tag is not None:
                        self._parse_category(div_tag, _paths)

                    if li.find('ul') is not None:
                        self._parse_category(li, _paths)

    async def parse(self, identifier: str, context: dict):

        logging.info("Category Crawl Start >> WEB")

        for category_id in range(self.CATEGORY_ID, self.CATEGORY_ID + 11):
            await asyncio.sleep(1)
            _url = 'https://search.shopping.naver.com/category/category/{0}'
            logging.info("PID >> %s | CategoryID >> %d " % (os.getpid(), category_id))

            jobs = context['jobs']

            job_info = jobs[identifier]

            request = requests.get(_url.format(category_id))
            #  상태 체크
            if request.status_code != 200:
                return
            try:
                _content = request.content
                tree: HtmlElement = html.fromstring(_content)
                header_xpath = '//*[@id="__next"]/div/div[2]/h2'
                _root_name = tree.xpath(header_xpath)[0].text
                job_info['status'] = 'in progress'
                job_info['name'] = _root_name

                self.crawl_status(str(category_id), _root_name, request.status_code)

                self._insert(str(category_id), _root_name, None, True)

                xpath = '//*[@id="__next"]/div/div[2]/div/div'
                elements: [HtmlElement] = tree.xpath(xpath)

                element: HtmlElement
                for element in elements:
                    if element.find('div') is not None:
                        a_tag: HtmlElement = element[0].find('h3').find('a')
                        _name = a_tag.find('strong').text
                        _href = a_tag.get('href')
                        _cid = Utils.separate_right(_href, self._DELIMITER)
                        _paths = Utils.join_path(self._PATH_TOKEN, _root_name, _name)

                        self._insert(_cid, _name, _paths)
                        self._parse_category(element[0], _paths)
                    else:
                        logging.info('Element is not Exists')

            except Exception as e:
                logging.error(str(e))

            # 더이상 필요없는 카테고리 아이템들 제거
            for item in self._category_list:
                _query = self.database_manager.find_query('_id', item['_id'])
                self.database_manager.delete_one(self.COLLECTION, _query)
        logging.info("Category Crawl END >> WEB")

        context['jobs'][identifier]['status'] = 'done'


crawl = CategoryCrawl()

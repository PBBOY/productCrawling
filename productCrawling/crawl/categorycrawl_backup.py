import re
import json
import time
import requests
import logging
from datetime import datetime
from operator import eq

from lxml import html, etree
from lxml.html import HtmlElement

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.remote.webelement import WebElement

from common.util import Utils
from common.driver.seleniumdriver import Selenium
from common.database.dbmanager import DatabaseManager
from common.config.configmanager import CrawlConfiguration, ConfigManager


def _join_path(token, source: str, value: str) -> str:
    return token.join([source, value])


class CategoryCrawl(object):
    URL = 'https://search.shopping.naver.com/category/category/{0}'
    CATEGORY = 50000000
    DELIMITER = 'cat_id='
    COLLECTION = 'category'

    def __init__(self):
        # 크롬 selenium Driver - singleton
        self.driver = Selenium().driver
        # 크롤링 설정 정보 관리 - singleton
        self.crawl_config: CrawlConfiguration = ConfigManager().crawl_config
        # Database manager - 데이터 조회 및 저장을 여기서 합니다. - singleton
        self.database_manager = DatabaseManager()
        # 중복 데이터 확인을 위해 미리 저장된 결과 list를 조회한다.
        self._category_list: list = list(self.database_manager.find_all_mongo(self.COLLECTION))

    def _update(self, cid, name, paths: str):
        _query = self.database_manager.find_query('cid', cid)

        _update_data = dict()
        _update_data['name'] = name
        _update_data['paths'] = paths
        _update_data['update_time'] = datetime.now()

        return self.database_manager.update(self.COLLECTION, _query, {"&set": _update_data})

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

    def parse(self):
        self.driver.get(self.URL)

        try:
            for category in self.driver.find_elements_by_xpath('//*[@id="home_category_area"]/div[1]/ul/li'):
                time.sleep(1)
                self._parse_root(category)

            # 더이상 필요없는 카테고리 아이템들 제거
            for item in self._category_list:
                _query = self.database_manager.find_query('_id', item['_id'])
                self.database_manager.delete_one(self.COLLECTION, _query)

        except Exception as e:
            logging.error(str(e))

    def _parse_root(self, category: WebElement):
        # Root 이름
        root_name: str = category.text
        # root_name = text.replace('/', '-')

        logging.info('rootName : ' + root_name)

        for exclude_category in self.crawl_config.exclude_category:
            if eq(root_name, exclude_category):
                return None

        class_att = category.get_attribute('class')
        click_xpath = '//*[@id="home_{0}"]'.format(class_att)

        self.driver.implicitly_wait(5)
        # 먼저 클릭해봄.
        self.driver.find_element_by_xpath(click_xpath).send_keys(Keys.ENTER)
        # class_att 맞춰 내부 xPath 설정
        time.sleep(1)

        xpath_cate = '//*[@id="home_{0}_inner"]/div[1]'.format(class_att)

        # Root Category
        element: WebElement = None
        while 1:
            if element is not None:
                break
            else:
                # 클릭 이벤트가 정상적으로 안들어오면 계속 클릭하자..
                self.driver.find_element_by_xpath(click_xpath).send_keys(Keys.ENTER)
                self.driver.implicitly_wait(4)
                time.sleep(1)
                element = self.driver.find_element_by_xpath(xpath_cate)

        self._insert(None, root_name, None, True)
        # Root -> sub
        co_col_elements = element.find_elements(By.CLASS_NAME, 'co_col')

        self._parse_co_col(co_col_elements, root_name)

    def _parse_co_cel(self, co_cel_elements, root_name):
        co_cel: WebElement
        for co_cel in co_cel_elements:
            # href
            sub_href = co_cel.find_element_by_tag_name('a').get_attribute('href')
            # cid
            _cid = Utils.separate_right(sub_href, self.DELIMITER)

            sub_element: WebElement = co_cel.find_element_by_tag_name('strong')

            # name
            _name = sub_element.find_element_by_tag_name('a').text
            _name = re.sub("전체보기", "", _name)
            # paths
            _paths = Utils.join_path(token='#', source=root_name, value=_name)

            # cid, name, paths
            self._insert(_cid, _name, _paths)

            # 하위 카테고리 리스트
            child_items: [WebElement] = co_cel.find_elements(By.TAG_NAME, 'li')
            self._parse_child(child_items, _paths)
        pass

    def _parse_co_col(self, sub_category, root_name):
        co_col: WebElement
        for co_col in sub_category:
            time.sleep(1)
            # 중간 카테고리
            co_cel_elements = co_col.find_elements_by_class_name('co_cel')
            self._parse_co_cel(co_cel_elements, root_name)

    def _parse_child(self, child_items, sub_paths):
        child_item: WebElement
        for child_item in child_items:
            time.sleep(1)
            # href
            _href = child_item.find_element_by_tag_name('a').get_attribute('href')
            # cid
            _cid = Utils.separate_right(_href, self.DELIMITER)
            # name
            _name = child_item.text  # 이름
            # paths
            _paths = Utils.join_path(token='#', source=sub_paths, value=_name)
            self._insert(_cid, _name, _paths)

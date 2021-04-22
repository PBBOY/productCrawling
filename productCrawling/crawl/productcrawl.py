'''
상품목록에서 상품 정보를 수집하는 crawler 입니다.

수집된 category의 id(cat_id)를 받아
해당 카테고리에 있는 상품을 수집합니다.
'''
import logging
import datetime
import math
import time
import asyncio
import requests
import re
import json
from typing import Optional
from bs4 import BeautifulSoup  # BeautifulSoup import
from operator import eq
from common.config.configmanager import ConfigManager, CrawlConfiguration
from common.database.dbmanager import DatabaseManager

from common.util import Utils

class ProductCrawl:
    '''
    상품목록에서 상품 정보를 수집하는 crawler 입니다.
    Attributes:
        driver
    '''
    PRODUCT_COLLECTION = "product"
    CRAWL_CONFIG_COLLECTION = "crawl_config"

    _excepted_data_count = 0

    def __init__(self):
        logging.info('start product crawl')
        # Database manager - 데이터 조회 및 저장을 여기서 합니다. - singleton
        self.database_manager = DatabaseManager()
        self.crawl_config: CrawlConfiguration = ConfigManager().crawl_config
        # start Page Default
        self._paging_start: int = 1
        self._view_size: int = 80  # self.crawl_config.crawl_count


        # 먼저 확인해야함. 다시 수집시 DB->Config 정보 셋
        # TODO: 나중에 처리하도록 수정
        # self._check_crawl_configuration()

        self._result: list = []

        self._category: dict = None

        self.productInfo_arr = []
        self._current_page: int = 0
        self.last_crawled_date_time = datetime.datetime.now()

    def _upsert_crawl_configuration(self, start_page):
        """모든 분석이 끝나고 Config 정보 update"""
        # 조건
        _filter = {}
        # 변경 데이터
        _config = dict()
        _config['start_page'] = start_page

        self.database_manager.update(self.CRAWL_CONFIG_COLLECTION, _filter, _config)

    def _check_crawl_configuration(self):
        """Config 정보 set"""
        _config: dict = self.database_manager.find_one(self.CRAWL_CONFIG_COLLECTION)

        if _config.get('start_page') is not None:
            self._paging_start = _config['start_page']

        if _config.get('crawl_category_list') is not None:
            self.crawl_config.crawl_category = _config['crawl_category_list']

    def _category_getter(self, crawl_category: list) -> list:
        """ 카테고리 목록 조회해서 분석
        :return category 목록들"""
        _categories: list = []
        if crawl_category is None:
            crawl_category = self.crawl_config.crawl_category

        for item in crawl_category:
            query = self.database_manager.keyword_query('paths', item)
            _categories.extend(list(self.database_manager.find('category', query=query)))

        return _categories

    def make_url(self, paging_index: int, frm: str = "NVSHMDL", _filter: str = "") -> str:
        """category id, 페이지 사이즈, 페이지 넘버를 조합하여 url 생성"""
        _url = ("https://search.shopping.naver.com/search/category?catId={0}&frm={1}{2}&origQuery&pagingIndex={3}&pagingSize={4}&productSet=model&query&sort=rel&timestamp=&viewType=list")
        _cid = self._category['cid']
        return _url.format(_cid, frm, _filter, paging_index, self._view_size)

    async def parse(self, identifier: str, context: dict, crawl_category: list = None):
        """ 외부에서 파싱을 하기 위해 호출하는 함수 """

        _categories: list = self._category_getter(crawl_category)

        for category in _categories:
            await asyncio.sleep(1)

            jobs = context['jobs']

            job_info = jobs[identifier]
            job_info['status'] = 'in Progress'
            job_info['category'] = category.get('name')

            self._category = category
            """파싱 프로세스 시작"""
            self._current_page = 0
            # Default = 1
            _url = self.make_url(paging_index=1)
            _total_count, _filter = self._get_base_data(_url)

            # Page 조건 변경 필요
            _is_oversize = _total_count > 8000
            # Page 계산
            _page_size = Utils.calc_page(_total_count, self._view_size)

            if _is_oversize:
                self._filter_parse(_filter)

            else:
                await self._execute_parse(_page_size)

            logging.info('>>> end childCategory: ' + self._category.get('name') + ' Pg.' + str(self._current_page))

        job_info['status'] = 'done'

    def _make_list(self, _min, _max, _half):
        result = []
        a = [_min, _half]
        b = [_half, _max]
        result.append(a)
        result.append(b)

        return result

    def _filter_parse_recursive(self, min_value, max_value):
        _param = ("&maxPrice={0}&minPrice={1}".format(str(max_value), str(min_value)))
        _url = self.make_url(1, "NVSHPRC", _param)
        _total_count, _filter = self._get_base_data(_url)
        _is_oversize = _total_count > 8000
        _page_size = Utils.calc_page(_total_count, self._view_size)
        if _is_oversize:
            half_price = math.ceil((min_value + max_value) / 2)
            _range = self._make_list(min_value, max_value, half_price)

            for value in _range:
                self._filter_parse_recursive(value[0], value[1])

        else:
            await self._execute_parse(_page_size, _param)
        pass

    def _filter_parse(self, filters: list):
        # 한번만 호출된다.
        for _filter in filters:
            _filterAction = _filter.get('filterAction')
            _separator = "-"  # default = -
            _paramName = None
            if _filterAction is not None:
                _separator = _filterAction.get('separator')
                # price split
            _value: str = _filter.get('value')
            _param = ""
            _min = 0
            _max = 0
            if _value is not None:
                _min, _max = (int(_price) for _price in _value.split(_separator))

            logging.info("Filter Parse >> min{0} / max{1}".format(_min, _max))

            self._filter_parse_recursive(_min, _max)

    async def _execute_parse(self, page_number, filter_param: str = ""):

        for page_number in range(1, page_number):
            try:
                _url = self.make_url(page_number, _filter=filter_param)

                self.parse_data(self._get_product_json(_url))

                logging.info(">>> URL : " + _url)
                logging.info('>>> start parsing: ' + self._category.get('name') + ' Pg.' + str(page_number))

                self._current_page = page_number
            except Exception as e:
                logging.debug(">>> Category Collect Err " + str(self._current_page)
                              + "  name: " + self._category.get('name') + "  Err :" + str(e))

    def _get_product_json(self, url) -> dict:
        """
        상품 정보 가져오기
        :arg
        :param url: request URL
        :return: data_dict 상품 정보
        """
        # header 추가 필요.
        try:
            _headers = {'Content-Type': 'application/json;'}
            req = requests.get(url, _headers)

            html = req.text
            soup = BeautifulSoup(html, 'html.parser')  # html.parser를 사용해서 soup에 넣겠다

            json_data = soup.find('script', text=re.compile('application/json'))

            data_dict = json.loads(str(json_data.contents[0]))
        except Exception as e:
            data_dict = None
            # 슬립 시간 조정 필요 - 8초가 부족할 수 있음.
            time.sleep(8)
            # 비정상적인 요청이 감지됨 - 다시 URL을 요청한다.
            logging.error("no find Data request Error >> {0} | URL >> {1}".format(e, url))
            self._get_product_json(url)

        return data_dict

    def parse_data(self, data_dict):
        """ 데이터 파싱 """
        product_info: dict = self._get_data(data_dict, 'products')
        if product_info is not None:
            '''수집된 데이터가 있는 경우'''

            product_list: list = product_info.get('list')

            self._excepted_data_count = 0

            logging.info("수집 시작 - 상품 데이터 수: " + str(len(product_list)))
            if len(product_list) > 0:
                for product in product_list:
                    product_data = dict()

                    product_item = product.get('item')
                    if product_item.get('adId') is None:

                        '''광고 데이터가 아닌 경우에만 수집'''
                        # 카테고리 정보 Setting
                        self._set_category_info(product_data)
                        # 상품 정보 Setting
                        self._set_product_info(product_data, product_item)

                        self._insert_product_info(product_data)
                    else:
                        self._excepted_data_count += 1
            else:
                logging.error('!!! Exception: 상품 정보가 없습니다.')
            # if len(product_list) != len(products_data) + self._excepted_data_count:
            #     logging.error("!!! Exception: 데이터 수 확인이 필요 합니다.")
            #     logging.info("수집된 데이터 수: " + str(len(products_data)))
            #     logging.info("수집 제외된 데이터 수: " + str(self._excepted_data_count))
        else:
            logging.error('!!! Exception: 데이터가 수집되지 않았습니다.')

    def _set_category_info(self, product_data: dict):
        '''상품정보에 카테고리 정보 셋팅
            arg:
                products_data: 상품 정보 객체
        '''
        product_data['n_cid'] = self._category.get('cid')
        product_data['cid'] = self._category.get('_id')
        product_data['paths'] = self._category.get('paths')
        product_data['cname'] = self._category.get('name')

    def _set_product_info(self, product_data: dict, product_item):
        product_data['n_id'] = product_item.get('id')
        product_data['imageUrl'] = product_item.get('imageUrl')
        product_data['title'] = product_item.get('productTitle')
        product_data['price'] = product_item.get('price')

        # product_data['option'] = {}

        _attribute: str = product_item.get('attributeValue', "")
        _attribute_value: str = product_item.get('characterValue', "")

        if (_attribute != "") and (_attribute_value != ""):
            # 옵션 정보가 있는 경우
            product_option_key: list = product_item.get('attributeValue').split('|')  # 옵션 키값
            product_option_value: list = product_item.get('characterValue').split('|')  # 옵션 벨류값


            product_data['option'] = dict(zip(product_option_key, product_option_value))

    def _insert_product_info(self, value: dict):
        """db data insert"""
        try:
            # TODO: 값 비교는 어디서 하지?
            _selection = self.database_manager.find_query("n_id", value.get("n_id"))
            self.database_manager.update(self.PRODUCT_COLLECTION, _selection, value)
            pass
        except Exception as e:
            logging.error('!!! Fail: Insert data to DB: ', e)

    def _get_base_data(self, url):
        _data = self._get_product_json(url)

        _total_count = 0
        value_filters: Optional[dict] = None

        if _data is not None:
            products = self._get_data(_data, 'products')
            if products is not None:

                _total_count = products.get('total')
                if _total_count is not None:
                    _total_count = int(_total_count)
                else:
                    _total_count = 0

            filters = self._get_data(_data, 'mainFilters')
            if filters is not None:
                value_filters = self._get_filter(filters)

        return _total_count, value_filters

    def _get_data(self, data: dict, _type: str):
        return data.get('props', {}).get('pageProps', {}).get('initialState', {}).get(_type)

    def _get_filter(self, main_filters: dict) -> dict:
        value_filters = None

        for _filter in main_filters:
            _filterType: str = _filter.get('filterType')
            if (_filterType is not None) and (eq(_filterType, 'price')):
                value_filters = _filter.get('filterValues')
                if value_filters is not None:
                    break

        return value_filters


product_crawl = ProductCrawl()

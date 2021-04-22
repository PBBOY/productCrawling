'''
상품목록에서 상품 정보를 수집하는 crawler 입니다.

수집된 category의 id(cat_id)를 받아
해당 카테고리에 있는 상품을 수집합니다.
'''
import logging
import datetime
import math

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from common.util import Utils
from common.config.configmanager import ConfigManager, CrawlConfiguration
from common.database.dbmanager import DatabaseManager
from common.driver.seleniumdriver import Selenium



class ProductCrawlTest:
    '''
    상품목록에서 상품 정보를 수집하는 crawler 입니다.
    Attributes:
        driver
    '''
    PRODUCT_COLLECTION = "product"
    CRAWL_CONFIG_COLLECTION = "crawl_config"

    def __init__(self):

        logging.info('start product crawl')
        # 크롬 selenium Driver - singleton
        self._selenium = Selenium()

        self.driver = Selenium().driver

        # 크롤링 설정 정보 관리 - singleton
        self.crawl_config: CrawlConfiguration = ConfigManager().crawl_config
        # Database manager - 데이터 조회 및 저장을 여기서 합니다. - singleton
        self.database_manager = DatabaseManager()

        # start Page Default
        self._paging_start: int = 1
        self._paging_range: int = self.crawl_config.crawl_page_range
        self._view_size: int = self.crawl_config.crawl_count

        # self.base_url =

        # 먼저 확인해야함. 다시 수집시 DB->Config 정보 셋
        # TODO: 나중에 처리하도록 수정
        # self._check_crawl_configuration()

        self._result: list = []

        self._category: dict = None

        self.productInfo_arr = []
        self._current_page: int = 0
        self.last_crawled_date_time = datetime.datetime.now()

    def _insert_product_info(self, value: dict):
        """db data insert"""
        try:
            # TODO: 값 비교는 어디서 하지?
            _selection = self.database_manager.find_query("n_id", value.get("n_id"))
            self.database_manager.update(self.PRODUCT_COLLECTION, _selection, value)
        except Exception as e:
            logging.error('!!! Fail: Insert data to DB: ', e)

    def _check_crawl_configuration(self):
        """Config 정보 set"""
        _config: dict = self.database_manager.find_one(self.CRAWL_CONFIG_COLLECTION)

        if _config.get('start_page') is not None:
            self._paging_start = _config['start_page']

        if _config.get('crawl_category_list') is not None:
            self.crawl_config.crawl_category = _config['crawl_category_list']

    def _upsert_crawl_configuration(self, start_page):
        """모든 분석이 끝나고 Config 정보 update"""
        # 조건
        _filter = {}
        # 변경 데이터
        _config = dict()
        _config['start_page'] = start_page

        self.database_manager.update(self.CRAWL_CONFIG_COLLECTION, _filter, _config)

    def _category_getter(self) -> list:
        """ 카테고리 목록 조회해서 분석
        :return category 목록들"""
        _categories: list = []
        for item in self.crawl_config.crawl_category:
            query = self.database_manager.keyword_query('paths', item)
            _categories.extend(list(self.database_manager.find('category', query=query)))

        return _categories

    def parse(self):
        _categories: list = self._category_getter()

        for category in _categories:
            self._category = category

            self.start_parsing_process()

    def start_parsing_process(self):
        """파싱 프로세스 시작"""
        self._current_page = 0
        for page_number in range(1, self.calc_page(self.get_products_count())):
            try:
                _url = self.make_url(page_number)
                logging.info(">>> URL : " + _url)
                self.driver.get(url=_url)
                logging.info('>>> start parsing: ' + self._category.get('name') + ' Pg.' + str(page_number))

                self.scroll_page_to_bottom()
                logging.info(">>> page scroll end")

                # Utils.take_a_sleep(1, 2)

                self.parsing_data(self.crawling_html())

                self._current_page = page_number
            except Exception as e:
                logging.debug(">>> Category Collect Err " + str(self._current_page)
                              + "  name: " + self._category.get('name') + "  Err :" + str(e))

        logging.info('>>> end childCategory: ' + self._category.get('name') + ' Pg.' + str(self._current_page))

    def parsing_data(self, products: [WebElement]):
        for product in products:
            Utils.take_a_sleep(1, 2)
            # 결과 저장 dict 생성
            if self._is_ad(product):
                continue

            product_info = dict()
            product_info['n_cid'] = self._category.get('cid')
            product_info['cid'] = self._category.get('_id')
            product_info['paths'] = self._category.get('paths')
            product_info['cname'] = self._category.get('name')

            self._parsing_product_base_info(product, product_info)

            self.parsing_product_detail_info(
                self.get_product_detail_info_items(product), product_info
            )
            self._insert_product_info(product_info)

    def get_products_count(self):
        """
        가격 비교탭에서 상품 개수 가져오기

        self._category['cid'] 값이 할당된 이후에 호출되어야 함(url 때문에)
        :arg
        :return:
        """
        _url = self.make_url(1)
        self.driver.get(url=_url)
        element = self.driver.find_element(By.CLASS_NAME, "subFilter_seller_filter__3yvWP")
        compare_price_tab_item = element.find_element(By.CLASS_NAME, "active")
        _count: str = compare_price_tab_item.find_element_by_class_name('subFilter_num__2x0jq').text
        _count = _count.replace(",", "")

        return int(_count)

    def calc_page(self, products_count: int) -> int:
        """
        페이지를 계산해주는 함수
        :arg
            :param products_count: 상품 전체 수
        :return:
             self._view_size: 한화면에 로딩하는 상품 개수(20, 40, 60, 80)
        """
        try:
            _page_count = products_count/self._view_size
        except ZeroDivisionError:
            _page_count = 0

        return math.ceil(_page_count)

    def _is_ad(self, item) -> bool:
        """
        :param item: 상품 아이탬

        :return: bool
        """
        class_text: str = item.find_element_by_class_name('basicList_item__2XT81').get_attribute('class')
        return class_text.endswith('ad')

    # def get_page_number(self) -> int:
    #     """파싱 시작페이지 ~ 파싱 페이지 끝까지 페이지 넘버 넘겨주기"""
    #     # 변수 검증만 해보면됨.
    #     for page_number in range(self._paging_start, self._paging_start + self._paging_range):
    #         yield page_number

    def make_url(self, paging_index) -> str:
        """category id, 페이지 사이즈, 페이지 넘버를 조합하여 url 생성"""
        _url = ("https://search.shopping.naver.com/search/category?catId={0}&frm=NVSHMDL&origQuery&pagingIndex={1}&pagingSize={2}&productSet=model&query&sort=rel&timestamp=&viewType=list")
        _cid = self._category['cid']
        return _url.format(_cid, paging_index, self._view_size)

    def scroll_page_to_bottom(self):
        """스크롤 끝가지 내리기"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            # for _ in range(15):
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)
            Utils.take_a_sleep(1, 2)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def crawling_html(self) -> [WebElement]:
        """데이터 파싱"""
        # // *[ @ id = "__next"] / div / div[2] / div / div[3] / div[1] / ul
        crawled_items: [WebElement] = self.driver.find_elements_by_xpath(
            '//*[@id="__next"]/div/div[2]/div/div[3]/div[1]/ul/div/div'
        )

        return crawled_items

    def get_product_detail_info_items(self, item) -> WebElement:
        """크롤링 된 html에서 상품정보를 갖고 있는 객체 가져오기"""

        product_info_item = item.find_element_by_class_name('basicList_detail_box__3ta3h')
        self.driver.execute_script("arguments[0].style.overflow = 'visible';", product_info_item)
        Utils.take_a_sleep(1, 3)
        # List -> WebElement 로 변경함.
        # product_info_data_items = product_info_item.find_elements_by_class_name('basicList_detail__27Krk')
        # basicList_detail__27Krk
        return product_info_item

    def parsing_product_detail_info(self, product_info_data_item, product_info: dict) -> dict:
        """text로 수집된 데이터 ':'로 split 하여 dictionary 형태로 저장"""
        product_info_datas = product_info_data_item.text.split('|')

        _option_info = dict()
        for data in product_info_datas:
            # print(info_obj.text)
            info_data: list = data.split(":")
            if len(info_data) > 1:
                (key, value) = info_data
                _option_info[key.strip()] = value.strip()

        product_info['optionInfo'] = _option_info

    def _parsing_product_base_info(self, product, product_info):
        """파싱된 데이터 json 포멧에 맞게 넣도록 Setting
            img link, 상품 상세정보 link, 상품 naver id"""
        title_element = product.find_element_by_class_name('basicList_link__1MaTN')
        thumbnail_element = product.find_element_by_class_name('thumbnail_thumb__3Agq6')

        product_info['productName'] = title_element.text

        if thumbnail_element:
            element = self._selenium.find_element(By.TAG_NAME, thumbnail_element, 'img')

            if element:
                product_info['img'] = element.get_attribute('src')

        if title_element.get_attribute('href'):
            product_info['url'] = title_element.get_attribute('href')
            _value = title_element.get_attribute('data-nclick')
            _right = (Utils.separate_right(_value, 'i:'))
            product_info['n_id'] = Utils.separate_left(_right, ',r')


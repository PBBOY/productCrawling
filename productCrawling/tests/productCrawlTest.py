import unittest
import math
import openpyxl

import requests
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

from common.config.configmanager import ConfigManager, CrawlConfiguration
from common.database.dbmanager import DatabaseManager
import time

class MyTestCase(unittest.TestCase):



    def test_connect(self):
        res = requests.get('https://shopping.naver.com/')
        assert res.status_code == 200

    def test_get_crawl_config(self):
        '''
        파싱 설정 정보 값 가져오기
        :return: bool
        '''
        try:
            crawl_config: CrawlConfiguration = ConfigManager().crawl_config
            if crawl_config is None:
                return False
        except Exception as e:
            return False

    def test_get_categories_config(self):
        '''설정값에 선언한 수집할 카테고리 목록을 가져오는 함수'''
        _categories: list()
        try:
            crawl_config: CrawlConfiguration = ConfigManager().crawl_config
            database_manager: DatabaseManager = DatabaseManager()
        except Exception as e:
            return False

    def test_get_categories(self):
        '''
        DB에서 카테고리 정보 가져오기
        :return:
        '''
        crawl_category = ['사무용품']
        database_manager: DatabaseManager = DatabaseManager()
        _categories:list()

        for item in crawl_category:
            query = database_manager.keyword_query('paths', item)
            _categories.extend(list(database_manager.find('category', query=query)))
        if _categories is None:
            return False

    def test_create_excel_file_with_category_tab(self):
        '''
        카테고리의 별로 탭을 만들어 액셀 파일 만드는 함수
        :return: None
        '''
        categories = [1, 2, 3]
        wb = openpyxl.load_workbook('test.xlsx')

        for category in categories:
            wb.create_sheet(index=0, title=str(category)+" sheet")
            sheet = wb.active
            sheet['A1'] = 'SFU' + str(category)
        wb.save('test.xlsx')

    MAX_COUNT = 800
    def test_calc_dev_price(self, min_price:int=0, max_price:int=40000,
                            product_count:int=10000)->bool:
        '''
        가격 범위 내의 상품 개수가 수집 가능한 상품 개수 범위(MAX_COUNT) 보다 많을 경우
        가격 범위를 줄여 상품 개수를 MAX_COUNT 이하로 줄이는 함수

        :param min_price: 범위 시작 가격
        :param max_price: 범위 끝 가격
        :param product_count: 가격 범위 내 상품 수
        :return: true
        '''
        print(min_price, '~', max_price, ':', product_count)

        if product_count < self.MAX_COUNT:
            # start Parsing
            return True

        else:
            half_pric = math.ceil((min_price + max_price) / 2)

            self.calc_dev_price(min_price, max_price, math.ceil(product_count / 4))
            self.calc_dev_price(half_pric, max_price, math.ceil(product_count / 2))


if __name__ == '__main__':
    unittest.main()

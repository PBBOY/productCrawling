import uuid
import unittest
import selenium
from selenium import webdriver
from selenium.webdriver import ActionChains

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from selenium.webdriver.remote.webelement import WebElement


class SeleniumCrawlTest(unittest.TestCase):
    # URL = 'https://search.shopping.naver.com/search/category?catId=50000158&frm=NVSHMDL&origQuery&pagingIndex=1&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list'
    URL = 'https://search.shopping.naver.com/category/category/50000008'
    CATEGORY = 50000000
    def setUp(self) -> None:
        CHROMEDRIVER_PATH = r'D:\_1.project\WEBuilder\python_project\git_crawling\crawlingApp\resource\chromedriver.exe'
        WINDOW_SIZE = "1920,1080"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument( f"--window-size={ WINDOW_SIZE }" )

        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options)
        self.driver = driver

        self.driver.get(self.URL)

    def test_crawl_category_xpath(self):
        xpath = '//*[@id="__next"]/div/div[2]/div/div'
        # // *[ @ id = "__next"] / div / div[2] / div
        # // *[ @ id = "__next"] / div / div[2] / div / div[1]
        elements: [WebElement] = self.driver.find_elements_by_xpath(xpath)
        # // *[ @ id = "__next"] / div / div[2] / div / div[1]
        element: WebElement
        for element in elements:
            print('')

    def test_url_except(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            for _ in range(15):
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.SPACE)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def test_crawling_html(self):
        """데이터 파싱"""
        # // *[ @ id = "__next"] / div / div[2] / div / div[3] / div[1] / ul
        crawled_items: [WebElement] = self.driver.find_elements_by_xpath(
            '//*[@id="__next"]/div/div[2]/div/div[3]/div[1]/ul/div/div'
        )

        self.assertIsNotNone(crawled_items)


    def test_crawl_product_total_count(self):
        element = self.driver.find_element(By.CLASS_NAME, "subFilter_seller_filter__3yvWP")

        li_active = element.find_element(By.CLASS_NAME, "active")

        print('')

    def test_url_parse(self):

        splitvalue = self.separateRight(self.url, 'cat_id=')

        self.assertEqual(splitvalue, '50000805')

    def separateRight(self, value, delimiter):
        if value is not None:
            x = 0
            x = value.find(delimiter)
            if x != -1:
                x = x + len(delimiter) - 1
                return value[x + 1:len(value)]


if __name__ in '__main__':
    unittest.main()

import unittest
import requests
from lxml import html, etree
from lxml.html import HtmlElement


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        # 패션 의류 카테고리로 테스트 진행
        url = "https://search.shopping.naver.com/category/category/50000000"

        self.request = requests.get(url)
        _content = self.request.content
        self.tree: HtmlElement = html.fromstring(_content)

    def tearDown(self) -> None:
        self.request.close()

    def test_response_content_root_name(self):
        """root name parse"""
        _result = "패션의류"
        header_xpath = '//*[@id="__next"]/div/div[2]/h2'
        _root_name = self.tree.xpath(header_xpath)[0].text

        self.assertTrue(self.request.status_code == 200)
        self.assertEqual(_result, _root_name)

    def test_find_elements_and_parse_content(self):
        xpath = '//*[@id="__next"]/div/div[2]/div/div'
        elements: [HtmlElement] = self.tree.xpath(xpath)

        assert len(elements) > 0

    def test_find_element_index0_and_parse_element(self):
        _result = '여성의류'
        xpath = '//*[@id="__next"]/div/div[2]/div/div'
        element: HtmlElement = self.tree.xpath(xpath)[0]

        a_tag: HtmlElement = element[0].find('h3').find('a')
        _name = a_tag.find('strong').text
        _href = a_tag.get('href')

        self.assertEqual(_result, _name)

    def test_find_ulAnd_li_tags(self):
        xpath = '//*[@id="__next"]/div/div[2]/div/div'
        element: HtmlElement = self.tree.xpath(xpath)[0]

        ul_tag: HtmlElement = element[0].find('ul')

        if ul_tag is not None:
            li_tags = ul_tag.findall('li')

            assert len(li_tags) > 0

        self.assertIsNotNone(ul_tag)

    def test_find_li_element_index0_and_parse_element(self):
        _result = '니트/스웨터'

        xpath = '//*[@id="__next"]/div/div[2]/div/div'
        element: HtmlElement = self.tree.xpath(xpath)[0]

        ul_tag: HtmlElement = element[0].find('ul')

        self.assertIsNotNone(ul_tag)
        li_tags = ul_tag.findall('li')

        assert len(li_tags) > 0

        li = li_tags[0]

        li_a_tag = li.find('a')
        self.assertIsNotNone(li_a_tag)
        _name = li_a_tag.text

        self.assertEqual(_result, _name)


if __name__ == '__main__':
    unittest.main()

import requests
import uuid
from operator import eq
import time
import re
import json
from bs4 import BeautifulSoup
from lxml import html, etree
from lxml.html import HtmlElement
from multiprocessing import Pool, Process
from common.util import Utils
from itertools import chain

def is_not_none(value: dict, field):
    if value.get(field) is not None:
        return True
    else:
        return False


def parse(page: int):
    time.sleep(2)
    except_data_count: int = 0
    URL = "https://search.shopping.naver.com/search/category?catId=50007588&frm=NVSHMDL&origQuery&pagingIndex={0}&pagingSize=40&productSet=model&query&sort=rel&timestamp=&viewType=list"
    URL = URL.format(str(page))

    headers = {'Content-Type': 'application/json;'}
    req = requests.get(URL, headers)
    html = req.text

    print("Page index : " + str(page))
    soup = BeautifulSoup(html, 'html.parser')  # html.parser를 사용해서 soup에 넣겠다

    json_data = soup.find('script', text=re.compile('application/json'))
    try:
        data_dict = json.loads(str(json_data.contents[0]))

    except Exception as e:
        print('')



    product_info: dict = data_dict['props']['pageProps']['initialState']['products']
    product_list: dict = product_info['list']
    product_total_count: dict = product_info['total']

    main_filters: dict = data_dict['props']['pageProps']['initialState']['mainFilters']

    value_filters = None
    for _filter in main_filters:
        _filterType: str = _filter.get('filterType')
        if (_filterType is not None) and (eq(_filterType, 'price')):
            value_filters = _filter.get('filterValues')
            if value_filters is not None:
                break

    for _filter in value_filters:
        _filterAction = _filter.get('filterAction')
        _separator = "-"  # default = -
        _paramName = None
        if _filterAction is not None:
            _separator = _filterAction.get('separator')
            _paramName = _filterAction.get('paramName')
            # price split

        _value: str = _filter.get('value')
        _min = 0
        _max = 0
        if _value is not None:
            _min, _max = (int(_price) for _price in _value.split(_separator))

        # 네이버 검색 URL 변경시 사용
        if _paramName is not None:
            pass
            # _min_price, _max_price = _paramName.split(_separator)

        _param = ("&maxPrice={0}&minPrice={1}".format(str(_max), str(_min)))

        print(_param)





    products_data: list = []
    print("총 상품 수: " + str(product_total_count))
    print("수집 시작 데이터 수: " + str(len(product_list)))
    for product in product_list:
        product_data: dict = {}

        product_item = product['item']
        if( "adId" not in product_item):
            product_data['id'] = product_item['id']
            product_data['imageUrl'] = product_item['imageUrl']
            product_data['productTitle'] = product_item['productTitle']

            product_data['option'] = {}
            if(product_item['attributeValue']):
                product_data['productOptionKey'] = product_item['attributeValue'].split('|')
                product_data['productOptionValue'] = product_item['characterValue'].split('|')

                product_data['option'] = dict(zip(product_data['productOptionKey'], product_data['productOptionValue']))

            # print("parseData: " + product_data + '\n')

            products_data.append(product_data)
        else:
            except_data_count += 1
            print(str(except_data_count) + ".광고 데이터 제외")

    print("수집 완료 데이터 수: " + str(len(products_data)))
    print("수집 제외된 데이터 수: " + str(except_data_count))

    if len(product_list) != len(products_data) + except_data_count:
        print("!!!! EXCEPTION: 데이터 수 확인이 필요 합니다.")


def sub_category(element: HtmlElement, root_path: str):

    ul_tag: HtmlElement = element.find('ul')

    if ul_tag is not None:
        li_tags = ul_tag.findall('li')

        li: HtmlElement
        for li in li_tags:
            try:
                li_a_tag = li.find('a')
                if li_a_tag is not None:
                    href = li_a_tag.get('href')
                    text = li_a_tag.text
                    paths = Utils.join_path('#', root_path, text)
                    div_tag = li.find('div')
                    if div_tag is not None:
                        sub_category(div_tag, paths)

                    if li.find('ul') is not None:
                        sub_category(li, paths)
            except Exception as e:
                print('')


def category(i):
    # URL = "https://search.shopping.naver.com/category/category/" + str(i)
    URL = "https://search.shopping.naver.com/too-many-request"

    headers = {'Content-Type': 'application/json;'}

    req = requests.get(URL, headers)

    content = req.content
    soup = BeautifulSoup(content, 'html.parser')  # html.parser를 사용해서 soup에 넣겠다

    json_data = soup.find('script', text=re.compile('application/json'))
    try:
        data_dict = json.loads(str(json_data.contents[0]))

    except Exception as e:
        print('')

    # tree: HtmlElement = etree.fromstring(content)
    tree: HtmlElement = html.fromstring(content)
    header_xpath = '//*[@id="__next"]/div/div[2]/h2'
    header = tree.xpath(header_xpath)[0].text

    xpath = '//*[@id="__next"]/div/div[2]/div/div'
    elements: [HtmlElement] = tree.xpath(xpath)

    element: HtmlElement
    for i, element in enumerate(elements):
        print(i)
        try:
            if element.find('div') is not None:
                a_tag: HtmlElement = element[0].find('h3').find('a')
                href = a_tag.get('href')
                _cid = Utils.separate_right(href, "category?catId=")
                h3_tag = a_tag.find('strong').text
                paths = Utils.join_path('#', header, h3_tag)
                sub_category(element[0], paths)

        except Exception as e:
            print('')

def main():

    start = int(time.time())

    num_cores = 2

    # pool = Pool(num_cores)
    # pool.map(parse, range(1, 5))
    list(map(category, range(3, 5)))

    print("***run time(sec) :", int(time.time()) - start)


if __name__ == '__main__':
    main()
    pass
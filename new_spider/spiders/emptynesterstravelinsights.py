# -*- coding: utf-8 -*-

from scrapy import Spider, Request, FormRequest
from collections import OrderedDict
import json, csv, re
from scrapy.crawler import CrawlerProcess
import xml.etree.ElementTree
import urllib
def delettags(text):
    text = re.sub('<img.*?>|<a.*?>|</a>|<div.*?>|</div>|<figure.*?>|</figure>|<style.*?>|</style>|<code.*?>|</code>|<noscript.*?>|</noscript>', '', text)
    text = re.sub('<script.?>.*?</script>', '', text)
    return text

def imagefilter(text):
    img_url = text
    if '.jpg?' in img_url:
        img_url = img_url.split('.jpg?')[0] + '.jpg'
    elif '.png?' in img_url:
        img_url = img_url.split('.png?')[0] + '.png'
    elif '.jpeg?' in img_url:
        img_url = img_url.split('.jpeg?')[0] + '.jpeg'
    return img_url


class dasoertlicheSpider(Spider):
    name = "emptynesterstravelinsights"
    count = 0
    headers = ['label', 'English']
    models = {}
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://en.wikipedia.org/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        import xlrd

        path = 'game.xlsx'

        workbook = xlrd.open_workbook(path)
        worksheet = workbook.sheet_by_index(0)
        offset = 1

        rows = {}
        self.header = []
        for i, row in enumerate(range(worksheet.nrows)):
            if i <1:  # (Optionally) skip headers
                for j, col in enumerate(range(worksheet.ncols)):
                    self.header.append(worksheet.cell_value(i, col))
                continue
            r = []
            for j, col in enumerate(range(worksheet.ncols)):
                r.append(worksheet.cell_value(i, col))
            rows[r[0]] = r

        # path = 'food2.xlsx'
        # workbook1 = xlrd.open_workbook(path)
        # worksheet1 = workbook1.sheet_by_index(0)
        # header1 = []
        # for i, row in enumerate(range(worksheet1.nrows)):
        #     if i <= offset:  # (Optionally) skip headers
        #         for j, col in enumerate(range(worksheet.ncols)):
        #             header1.append(worksheet.cell_value(i, col))
        #         continue
        #     r = []
        #     for j, col in enumerate(range(header)):
        #         if col in header1:
        #             colum = header1.index(col)
        #             r.append(worksheet1.cell_value(i, colum))
        #         else:
        #             r.append('')
        #
        #     rows[r[0]] = r



        words = []
        with open('list_of_games.csv', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    # print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    if len(row) < 1: continue
                    words.append(row[0])
                    line_count += 1

        for word in words:
            if not word in rows.keys():
                r = []
                for key in self.header:
                    r.append('')
                r[0] = word
                self.models[word] = r

                params = {'search': word, 'title': 'Special:Search', 'go': 'Go'}
                url = 'https://en.wikipedia.org/w/index.php?{}'.format(urllib.parse.urlencode(params))
                item = OrderedDict()
                item['label'] = word
                item['English'] = ''
                yield Request(url, self.parse_products, meta={'word':word, 'item': item}, dont_filter=True)
            else:
                self.models[word] = rows[word]


    def parse_products(self, response):
        item = response.meta['item']
        result_url = response.xpath('//ul[@class="mw-search-results"]/li/div/a/@href').extract_first()
        if not result_url:
            title = ''.join(response.xpath('//h1[@id="firstHeading"]//text()').extract())
            options = []
            langs = response.xpath('//div[@id="p-lang"]//ul/li/a')
            for i, li in enumerate(langs):
                option = {}
                lang_key = li.xpath('./text()').extract_first()
                if not lang_key in self.headers:
                    self.headers.append(lang_key)
                url = li.xpath('./@href').extract_first()
                option[lang_key] = url
                options.append(option)

            if len(options) > 0:
                url = list(options[0].values())[0]
                item['English'] = title
                yield Request(response.urljoin(url), self.finalparse, meta={'item':item, 'options':options}, dont_filter=True, errback=self.err)
            else:
                if not 'search results' in title.lower():
                    item['English'] = title

                r = []
                for key in self.header:
                    if key in item.keys():
                        r.append(item[key])
                    else:
                        r.append('')
                self.models[item['label']] = r

                # self.models.append(item)
                self.count += 1
                print(self.count)
                yield item

        else:
            yield Request(response.urljoin(result_url), self.parse_products, meta=response.meta, errback=self.err)
    def err(self, response):
        self.count += 1
        print(self.count)
        item =response.request.meta['item']
        r = []
        for key in self.header:
            if key in item.keys():
                r.append(item[key])
            else:
                r.append('')
        self.models[item['label']] = r
        # self.models.append(response.request.meta['item'])
        yield response.request.meta['item']
    def finalparse(self, response):
        item = response.meta['item']
        title = ''.join(response.xpath('//h1[@id="firstHeading"]//text()').extract())
        options = response.meta['options']
        lang = list(options[0].keys())[0]
        item[lang] = title
        options.pop(0)
        if len(options) > 0:
            url = list(options[0].values())[0]
            yield Request(url, self.finalparse, meta={'item': item, 'options': options}, dont_filter=True, errback=self.err)
        else:
            # self.models.append(item)
            self.count+=1
            print(self.count)

            r = []
            for key in self.header:
                if key in item.keys():
                    r.append(item[key])
                else:
                    r.append('')
            self.models[item['label']] = r
            yield item


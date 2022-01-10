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
    name = "movie"
    count = 0
    headers = ['label', 'English']
    models = []
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://en.wikipedia.org/wiki/Lists_of_films'

    def start_requests(self):
        # import xlrd
        # words = []
        # words1 = []
        # with open('movie.csv', encoding="utf-8") as csv_file:
        #     csv_reader = csv.reader(csv_file, delimiter=',')
        #     line_count = 0
        #     for row in csv_reader:
        #         # if line_count == 0:
        #         #     # print(f'Column names are {", ".join(row)}')
        #         #     line_count += 1
        #         # else:
        #             if len(row) < 1: continue
        #             words.append(row[0])
        #             words1.append(row[1])
        #             line_count += 1
        #
        # path = 'movie.xlsx'
        # workbook = xlrd.open_workbook(path)
        # worksheet = workbook.sheet_by_index(0)
        # rows = []
        # offset = 1
        # for i, row in enumerate(range(worksheet.nrows)):
        #     # if i <= offset:  # (Optionally) skip headers
        #     #     continue
        #     r = []
        #     r.append(words[i])
        #     r.append(words1[i])
        #     for j, col in enumerate(range(worksheet.ncols)):
        #         r.append(worksheet.cell_value(i, j))
        #     rows.append(r)
        #
        # import os, xlsxwriter
        # filepath = 'movie1.xlsx'
        # if os.path.isfile(filepath):
        #     os.remove(filepath)
        # workbook1 = xlsxwriter.Workbook(filepath)
        # sheet = workbook1.add_worksheet('movie')
        #
        # for index, value in enumerate(rows):
        #     for col, key in enumerate(value):
        #         sheet.write(index, col, key)
        #
        #     print('row :' + str(index))
        #
        # workbook1.close()
        #
        # pass




        yield Request(self.start_url, self.parse)

    def parse(self, response):
        urls = response.xpath('//table[@class="wikitable"]//tr/td/a/@href').extract()
        for url in urls:
            yield Request(response.urljoin(url), self.parse1)


    def parse1(self, response):
        words = response.xpath('//div[@class="mw-parser-output"]//ul/li/i/a')

        for i, tag in enumerate(words):
            if i == len(words) - 2: break
            word = tag.xpath('./text()').extract_first()
            url = tag.xpath('./@href').extract_first()
            yield Request(response.urljoin(url), self.parse_products, meta={'word':word})


    def parse_products(self, response):
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
            item = OrderedDict()
            item['label'] = response.meta['word']
            item['English'] = title
            if len(options) > 0:
                url = list(options[0].values())[0]
                yield Request(response.urljoin(url), self.finalparse, meta={'item':item, 'options':options}, dont_filter=True)
            else:
                self.models.append(item)
                yield item

        else:
            yield Request(response.urljoin(result_url), self.parse_products, meta=response.meta)

    def finalparse(self, response):
        item = response.meta['item']
        title = ''.join(response.xpath('//h1[@id="firstHeading"]//text()').extract())
        options = response.meta['options']
        lang = list(options[0].keys())[0]
        item[lang] = title
        options.pop(0)
        if len(options) > 0:
            url = list(options[0].values())[0]
            yield Request(url, self.finalparse, meta={'item': item, 'options': options}, dont_filter=True)
        else:
            self.models.append(item)
            yield item


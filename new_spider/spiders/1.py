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
    name = "food1"
    count = 0
    headers = ['label', 'English']
    models = []
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://en.wikipedia.org/'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        words = []
        with open('list_of_foods1.csv', encoding="utf-8") as csv_file:
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
            params = {'search': word, 'title': 'Special:Search', 'go': 'Go'}
            url = 'https://en.wikipedia.org/w/index.php?{}'.format(urllib.parse.urlencode(params))
            item = OrderedDict()
            item['label'] = response.meta['word']
            item['English'] = word
            yield Request(url, self.parse_products, meta={'word':word, 'item': item}, dont_filter=True)


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
                yield Request(response.urljoin(url), self.finalparse, meta={'item':item, 'options':options}, dont_filter=True, errback=self.err)
            else:
                self.models.append(item)
                self.count += 1
                print(self.count)
                yield item

        else:
            yield Request(response.urljoin(result_url), self.parse_products, meta=response.meta, errback=self.err)
    def err(self, response):
        self.count += 1
        print(self.count)
        self.models.append(response.request.meta['item'])
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
            self.models.append(item)
            self.count+=1
            print(self.count)
            yield item


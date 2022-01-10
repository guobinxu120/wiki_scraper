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
    name = "hobby"
    count = 0
    headers = ['label', 'English']
    models = []
    def __init__(self, city=None, keyword=None, *args, **kwargs):
        super(dasoertlicheSpider, self).__init__(*args, **kwargs)
        self.start_url = 'https://en.wikipedia.org/wiki/List_of_hobbies'

    def start_requests(self):
        yield Request(self.start_url, self.parse)

    def parse(self, response):
        words = response.xpath('//div[@class="mw-parser-output"]//ul/li/a')

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
                yield Request(response.urljoin(url), self.finalparse, meta={'item':item, 'options':options})
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
            yield Request(url, self.finalparse, meta={'item': item, 'options': options})
        else:
            self.models.append(item)
            yield item


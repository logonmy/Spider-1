# -*- coding: utf-8 -*-
import scrapy


class ProxyDemoSpider(scrapy.Spider):
    name = 'proxy_demo'
    allowed_domains = ['httpbin.org']
    start_urls = ['https://httpbin.org/ip']

    def start_requests(self):
        for url in self.start_urls:
            req = scrapy.Request(url)
            req.meta['proxy'] = 'http://H4U23WF0BK7PY0OD:B8CD32E44A22A8F9@http-dyn.abuyun.com:9020'
            req.meta['dont_filter'] = True
            yield req

    def parse(self, response):
        print(response.text)


# -*- coding: utf-8 -*-
import scrapy


class CookieDemoSpider(scrapy.Spider):
    name = 'cookie_demo'
    allowed_domains = ['test.com']
    start_urls = ['http://www.baidu.com/']
    custom_settings = {
        'SITE': 'ZHI_LIAN',
        'DOWNLOADER_MIDDLEWARES': {
            'crwy.utils.scrapy_plugs.middlewares.CookieMiddleware': 100
        }
    }

    def start_requests(self):
        for url in self.start_urls:
            req = scrapy.Request(url)
            req.meta['keep_cookie_user'] = True
            yield req

    def parse(self, response):
        print(response.text)
        print(response.meta)

# -*- coding: utf-8 -*-
import datetime
import logging
import re

import scrapy
from scrapy_redis.spiders import RedisSpider
from crwy.utils.html.font_analysis import FontAnalysis, font_mapping
from crwy.utils.scrapy_plugs.settings import LoadSettingsFromConsul
from crwy.utils.common import datetime2str
from crwy.utils.common import dict2obj
from crwy.spider import BaseSpider

from five_eight.items import (
    SpiderSearchResumeRawItem, SpiderSearchResumeRawItemLoader)

settings = dict2obj(LoadSettingsFromConsul.get_settings(
    key='scrapy/five_eight/search', host='172.16.25.36'
))


class SearchSpider(BaseSpider, RedisSpider):
    name = 'search'
    allowed_domains = ['58.com']
    redis_key = 'task:search:FIVE_EIGHT'
    template_url = 'https://{city}.58.com/searchjob' \
                   '/pn{page}/pve_5593_{degree}/?key=' \
                   '{keyword}&age=18_30&postdate={postdate}&param8716=0'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;'
                  'q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/68.0.3440.84 Safari/537.36'
    }
    custom_settings = {
        'SITE': 'FIVE_EIGHT',
        'SPIDER_NAME': name,
        'DUPEFILTER_DO_HASH': False,
        'DUPEFILTER_CLASS':
            'crwy.utils.scrapy_plugs.dupefilters.RedisRFPDupeFilter',
        'DOWNLOADER_MIDDLEWARES': {
            'five_eight.middlewares.FiveEightDownloaderSearchMiddleware': 543,
        },
        # 'ITEM_PIPELINES': {
        #     'five_eight.pipelines.SpiderSearchResumeRawSavePipeline': 543,
        # },
        'REDIS_URL': 'redis://root:uV2ngVk9AC@'
                     'r-2ze0889fc8e3c784.redis.rds.aliyuncs.com:6379/6',
        'SQLALCHEMY_URI':
            'mysql+pymysql://bi_admin:bi_admin#@1mofanghr@'
            '10.0.3.52:3306/spider_search',
        'LOG_LEVEL': logging.DEBUG
    }

    @staticmethod
    def get_real_html(html):
        """
        还原html字体
        :param html:
        :return:
        """
        fa = FontAnalysis(html=html)
        real_font_mapping = fa.get_real_font_mapping(
            fa.analysis(), font_mapping)
        return fa.recover_html(
            html=html,
            real_font_mapping=real_font_mapping)

    @staticmethod
    def get_resume_id(url):
        resume_id = re.search('(?=3_).*?(?=&)', url).group()
        return resume_id[:16]

    @staticmethod
    def format_postdate(search_day):
        end = datetime.datetime.now() + datetime.timedelta(days=1)
        start = end - datetime.timedelta(days=search_day)

        postdate = datetime2str(start, fmt='%Y%m%d') + '000000_' \
                   + datetime2str(end, fmt='%Y%m%d') + '000000'
        return postdate

    def make_request_from_data(self, data):
        data = eval(data)
        query_args = {
            'city': data['city'],
            'city_name': data['city_name'],
            'page': 1,
            'degree': data['degree'],
            'keyword': data['keyword'],
            'postdate': self.format_postdate(settings.SEARCH_DAY)
        }

        url = self.template_url.format(**query_args)
        self.logger.info('fetch：{}'.format(url))
        req = scrapy.Request(url, headers=self.headers)
        req.meta['query_args'] = query_args
        req.meta['task'] = data
        req.meta['keep_cookie_user'] = True
        if data.get('username'):
            req.meta['cookie_user'] = data.get('username').encode('utf-8')
        return req

    def parse(self, response):
        meta = response.meta
        real_html = self.get_real_html(response.text)
        soups = self.html_parser.parser(real_html).find(
            'div', id='infolist').find_all('dl')

        # has_next = True if self.html_parser.parser(real_html).find(
        #     'div', class_='pagerout').find(
        #     'a', class_='next') else False
        #
        # if has_next:
        #     current_page = meta['query_args']['page']
        #     next_page = current_page + 1
        #     meta['query_args']['page'] = next_page
        #     query_args = meta['query_args']
        #     url = self.template_url.format(**query_args)
        #     yield scrapy.Request(url, headers=self.headers, meta=meta)

        for soup in soups:
            url = soup.find('dt').find('a').get('href')
            resume_id = self.get_resume_id(url)
            meta['dupefilter_key'] = resume_id.encode('utf-8')
            yield response.follow(url, meta=meta, callback=self.parse_item)
            # break

    def parse_item(self, response):
        real_html = self.get_real_html(response.text)
        now = datetime.datetime.now()
        item_loader = SpiderSearchResumeRawItemLoader(
            response=response, item=SpiderSearchResumeRawItem())
        item_loader.add_value('source', 'FIVE_EIGHT')
        item_loader.add_value('email', response.meta.get('cookie_user'))
        item_loader.add_value('subject', response.meta.get('dupefilter_key'))
        item_loader.add_value('content', real_html)
        item_loader.add_value('emailJobType',
                              response.meta.get('query_args').get('keyword'))
        item_loader.add_value('emailCity',
                              response.meta.get('query_args').get('city_name'))
        item_loader.add_value('createTime', now)
        item_loader.add_value('createBy', 'python3-scrapy')
        item_loader.add_value('rdCreateTime', now)
        return item_loader.load_item()

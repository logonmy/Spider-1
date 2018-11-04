# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class XiaomispiderItem(scrapy.Item):
    # 网站名称
    memname = scrapy.Field()
    # 企业名称
    compname = scrapy.Field()
    #投诉标题
    # title = scrapy.Field()
    # 企业id
    memid = scrapy.Field()
    # 投诉内容
    content = scrapy.Field()
    # 满意度
    satisfaction = scrapy.Field()

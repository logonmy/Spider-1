# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MyspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    #地点
    address = scrapy.Field()
    #投诉标题
    title = scrapy.Field()
    #时间
    complainttime = scrapy.Field()
    #公司
    companyname = scrapy.Field()
    #详情
    content = scrapy.Field()
    #url
    sourceurl = scrapy.Field()
    #平台名字
    sourcename = scrapy.Field()
    #标签
    tag = scrapy.Field()
    #省
    province = scrapy.Field()
    #市
    cityname= scrapy.Field()
    #图片
    content_pic = scrapy.Field()
    addtime= scrapy.Field()

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MispiderItem(scrapy.Item):
    # define the fields for your item here like:
    # 图片标题
    title = scrapy.Field()
    # 缩略图地址
    smallpicurl = scrapy.Field()
    # 大图地址
    bigpicurl = scrapy.Field()
    # 图片说明
    content = scrapy.Field()
    # 标签
    tag = scrapy.Field()
    # 物理大图名称
    physicalname = scrapy.Field()
    # 物理缩略图名称
    thumbnailname = scrapy.Field()
    # 图片id
    pictureid = scrapy.Field()
    # 详情页url
    detailsurl = scrapy.Field()



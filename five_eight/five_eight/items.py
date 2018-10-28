# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from scrapy.loader import ItemLoader


class SpiderSearchResumeRawItemLoader(ItemLoader):
    pass


class SpiderSearchResumeRawItem(scrapy.Item):
    source = scrapy.Field()
    email = scrapy.Field()
    subject = scrapy.Field()
    content = scrapy.Field()
    processStatus = scrapy.Field()
    parsedTime = scrapy.Field()
    reason = scrapy.Field()
    emailJobType = scrapy.Field()
    emailCity = scrapy.Field()
    deliverJobName = scrapy.Field()
    deliverJobCity = scrapy.Field()
    createTime = scrapy.Field()
    createBy = scrapy.Field()
    updateTime = scrapy.Field()
    updateBy = scrapy.Field()
    trackId = scrapy.Field()
    resumeUpdateTime = scrapy.Field()
    resumeSubmitTime = scrapy.Field()
    rdCreateTime = scrapy.Field()


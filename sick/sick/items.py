# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SickItem(scrapy.Item):
    # 问题类目一
    catOne = scrapy.Field()
    # 问题类目二
    catTwo = scrapy.Field()
    # 问题类目三
    catThree = scrapy.Field()
    # 问题类目四
    catFour = scrapy.Field()

    # 问题标题
    title = scrapy.Field()
    # 患者性别
    gender = scrapy.Field()
    # 年龄
    age = scrapy.Field()
    # 发病时间
    startTime = scrapy.Field()
    # 问题描述
    question = scrapy.Field()
    # 提问时间
    questionTime = scrapy.Field()
    # 问题标签
    questionTag = scrapy.Field()
    # 问题链接
    questionUrl = scrapy.Field()

    # doctor
    # 医生姓名
    # name = scrapy.Field()
    # # 医生级别
    # level = scrapy.Field()
    # # 工作单位
    # company = scrapy.Field()
    # # 擅长的领域
    # good = scrapy.Field()
    # # 回答答案
    # detail = scrapy.Field()
    # # 回答时间
    # time = scrapy.Field()

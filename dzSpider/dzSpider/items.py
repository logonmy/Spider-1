# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DzspiderItem(scrapy.Item):
    #信息源
    sourcename = scrapy.Field()
    #来源url
    sourceurl = scrapy.Field()
    #公司名
    companyname = scrapy.Field()
    #地址
    address = scrapy.Field()
    #电话
    tel = scrapy.Field()
    #公司介绍
    compcontent = scrapy.Field()
    #合同均价
    avgprice = scrapy.Field()

class DzcspiderItem(scrapy.Item):
    # 信息源
    sourcename = scrapy.Field()
    # 公司名
    companyname = scrapy.Field()
    #来源url
    sourceurl = scrapy.Field()
    #用户名
    username = scrapy.Field()
    # 评论时间
    commtime = scrapy.Field()
    # 评论内容
    commcontent = scrapy.Field()
    # 装修形式
    formstyle = scrapy.Field()
    # 装修类型
    category = scrapy.Field()
    # 面积
    areas = scrapy.Field()
    # 费用
    price = scrapy.Field()
    # 阶段
    stage = scrapy.Field()
    # 施工分值
    constructinscore = scrapy.Field()
    # 服务分值
    servicescore = scrapy.Field()


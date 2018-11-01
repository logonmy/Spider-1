# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Jk39SpdierItem(scrapy.Item):
    # 姓名
    name = scrapy.Field()
    # 职业
    job = scrapy.Field()
    # 医院
    hospital = scrapy.Field()
    # 擅长
    good = scrapy.Field()
    # 详情
    detail = scrapy.Field()
    # 时间
    time = scrapy.Field()
    # 科室？
    room = scrapy.Field()
    # 追问
    zw = scrapy.Field()
    # 帮助人数
    helper = scrapy.Field()
    # 网址
    link = scrapy.Field()

    def get_insert_sql(self):
        sql = "insert into jk_doctor(id,name,job,hospital,good,detail,time,room,zw,helper,link) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

        sdict = (0, self['name'], self['job'], self['hospital'], self['good'], self['detail'], self['time'],
                 self['room'], self['zw'], self['helper'], self['link']
                 )

        return (sql, sdict)

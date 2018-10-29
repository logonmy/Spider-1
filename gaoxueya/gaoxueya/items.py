# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class GaoxueyaItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    question_time = scrapy.Field()
    disease = scrapy.Field()
    question = scrapy.Field()
    doctor = scrapy.Field()
    good_num = scrapy.Field()
    bad_num = scrapy.Field()
    answers = scrapy.Field()
    answers_time = scrapy.Field()
    wt_url = scrapy.Field()
    level = scrapy.Field()


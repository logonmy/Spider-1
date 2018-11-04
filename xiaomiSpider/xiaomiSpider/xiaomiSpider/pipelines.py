# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json


class XiaomispiderPipeline(object):
    '''
    该类用来处理数据保存
    将加载的数据保存成json格式
    '''
    def open_spider(self, spider):
        self.file = open(spider.name + ".json", "w", encoding="utf-8")

    def process_item(self, item, spider):
        self.file.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        return item

    def close_spider(self, spider):
        self.file.close()


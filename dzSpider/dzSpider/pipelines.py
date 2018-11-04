# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import psycopg2
from dzSpider.items import DzspiderItem,DzcspiderItem

class DzspiderPipeline(object):

    # def __init__(self):
    #     self.conn = psycopg2.connect(database="test1", user="gpadmin", password="gpadmin", host="192.168.0.2",port="5432")
    #     self.cursor = self.conn.cursor()

    def open_spider(self, spider):
        self.file1 = open(spider.name + ".json", "w", encoding="utf-8")
        self.file2 = open(spider.name +  'zt' +".json", "w", encoding="utf-8")

    def process_item(self, item, spider):
        if isinstance(item, DzspiderItem):
            # sourcename = item.get('sourcename')
            # sourceurl = item.get('sourceurl')
            # companyname = item.get('companyname')
            # address = item.get('address')
            # tel = item.get('tel')
            # compcontent = item.get('compcontent')
            # avgprice = item.get('avgprice')
            #
            # try:
            #     insert_sql = """
            #                          insert into company_info(sourcename,sourceurl,companyname,address,tel,compcontent,avgprice) values (%s,%s,%s,%s,%s,%s,%s)
            #                     """
            #     self.cursor.execute(insert_sql, (sourcename,sourceurl,companyname,address,tel,compcontent,avgprice))
            #     self.conn.commit()
            #     # log.msg("Data added to PostgreSQL database!",
            #     #         level=log.DEBUG, spider=spider)
            # except Exception as e:
            #     print('insert record into table failed')
            #     print(e)
            # return item
            #存为json格式
            self.file1.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
            return item
        elif isinstance(item, DzcspiderItem):
            # sourcename = item.get('sourcename')
            # companyname = item.get('companyname')
            # sourceurl = item.get('sourceurl')
            # username = item.get('username')
            # commtime = item.get('commtime')
            # commcontent = item.get('commcontent')
            # formstyle = item.get('formstyle')
            # category = item.get('category')
            # areas = item.get('areas')
            # price = item.get('price')
            # stage = item.get('stage')
            # constructinscore = item.get('constructinscore')
            # servicescore = item.get('servicescore')
            #
            # try:
            #     insert_sql = """
            #                          insert into company_comment(sourcename,companyname,sourceurl,username,commtime,commcontent,formstyle,category,areas,price,stage,constructinscore,servicescore)
            #                          values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            #                     """
            #     self.cursor.execute(insert_sql, (sourcename,companyname,sourceurl,username,commtime,commcontent,formstyle,category,areas,price,stage,constructinscore,servicescore))
            #     self.conn.commit()
            #     # log.msg("Data added to PostgreSQL database!",
            #     #         level=log.DEBUG, spider=spider)
            # except Exception as e:
            #     print('insert record into table failed')
            #     print(e)
            # return item
            # 存为json格式
            self.file2.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
            return item

    # def close_spider(self, spider):
    #     self.cursor.close()
    #     self.conn.close()

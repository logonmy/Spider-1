# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json
import psycopg2
# import logging
# logger = logging.getLogger('MyspiderPipeline')

class MyspiderPipeline(object):
    def __init__(self):
        self.conn = psycopg2.connect(database="webspider", user="gpadmin", password="gpadmin", host="192.168.0.2",port="5432")
        self.cursor = self.conn.cursor()

    # def open_spider(self, spider):
    #     self.file = open(spider.name + '.json', 'w', encoding='utf-8')
    #     print('开始爬取')

    def process_item(self, item, spider):
        sourcename = item.get('sourcename')
        sourceurl = item.get('sourceurl')
        title = item.get('title')
        companyname = item.get('companyname')
        province = item.get('province')
        cityname = item.get('cityname')
        complainttime = item.get('complainttime')
        content = item.get('content')
        tag = item.get('tag')
        addtime = item.get('addtime')

        try:
            insert_sql = """
                         insert into decompany(sourcename,sourceurl,title,companyname,province,cityname,complainttime,content,tag,addtime)
                         values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """
            self.cursor.execute(insert_sql,(sourcename,sourceurl,title,companyname,province,cityname,complainttime,content,tag,addtime))
            self.conn.commit()
            # log.msg("Data added to PostgreSQL database!",
            #         level=log.DEBUG, spider=spider)
        except Exception as e:
            print('insert record into table failed')
            print(e)
        return item

        # content = json.dumps(dict(item), ensure_ascii=False) + '\n'
        # self.file.write(content)
        # return item

    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()


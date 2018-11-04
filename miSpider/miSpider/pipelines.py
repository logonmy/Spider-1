# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from scrapy import log
from scrapy.pipelines.images import ImagesPipeline
import scrapy
import json

#图片下载器
class MispiderImagePipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        img_urls = []
        smallpicurl = item["smallpicurl"]
        img_urls.append(smallpicurl)
        bigpicurl = item['bigpicurl']
        img_urls.append(bigpicurl)
        for url in img_urls:

            yield scrapy.Request(url,meta={'pictureid':item['pictureid'],'smallpicurl':item["smallpicurl"],'bigpicurl':item['bigpicurl']})

        # 图片重命名

    def file_path(self, request, response=None, info=None):
        if request.url == request.meta['smallpicurl']:
            objid = request.meta['pictureid']
            #mats = response.url.split(".")[-1]
            #name = request.url.split('/')[-1]
            name = "s" + "_" + str(objid) + ".jpg"

        if request.url == request.meta['bigpicurl']:
            objid = request.meta['pictureid']
            #matb = response.url.split(".")[-1]
            #name = request.url.split('/')[-1]
            name = "b" + "_" + str(objid) + ".jpg"
        print("=-========", name)
        return name

    def item_completed(self, results, item, info):
        physicalname = [x["path"] for ok, x in results if ok]
        if len(physicalname)> 0:
             print("image_path==",physicalname)
             item["physicalname"] = str(physicalname[1])

        thumbnailname = [x["path"] for ok, x in results if ok]
        if len(thumbnailname) > 0:
            print("image_path==", thumbnailname)
            item["thumbnailname"] = str(thumbnailname[0])
        return item


class MispiderPipeline(object):
    def open_spider(self,spider):
        self.file = open(spider.name+".json","w",encoding="utf-8")
    def close_spider(self,spider):
        self.file.close()

    def process_item(self, item, spider):

        self.file.write(json.dumps(dict(item),ensure_ascii=False)+"\n")
        return item


# 将数据保存到数据库
import psycopg2
import scrapy
import logging
logger = logging.getLogger('CrawlfangImagePipeline')

class CrawlfangPipeline(object):
    def __init__(self):
        self.conn = psycopg2.connect(database="webspider", user="gpadmin", password="gpadmin", host="192.168.0.2", port="5432")
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        title = item.get('title')
        smallpicurl = item.get('smallpicurl')
        bigpicurl = item.get('bigpicurl')
        tag = item.get('tag')
        content = item.get('content')
        physicalname = item.get('physicalname')
        thumbnailname = item.get('thumbnailname')
        pictureid = item.get('pictureid')

        try:
            insert_sql = """
                 insert into beepic(title,smallpicurl,bigpicurl,tag,content,physicalname,thumbnailname,pictureid)
                 values (%s,%s,%s,%s,%s,%s,%s,%s)
            """
            self.cursor.execute(insert_sql,(title,smallpicurl,bigpicurl,tag,content,physicalname,thumbnailname,pictureid))
            self.conn.commit()
            log.msg("Data added to PostgreSQL database!",
                    level=log.DEBUG, spider=spider)
        except Exception as e:
            print('insert record into table failed')
            print (e)
        return item


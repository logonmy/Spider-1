# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql

from scrapy.conf import settings


class SickPipeline(object):

    def process_item(self, item, spider):
        host = settings['MYSQL_HOST']
        user = settings['MYSQL_USER']
        psd = settings['MYSQL_PASSWORD']
        db = settings['MYSQL_DBNAME']
        port = settings['MYSQL_PORT']

        con = pymysql.connect(host=host, user=user, passwd=psd, db=db, port=port)

        cue = con.cursor()

        try:

            cue.execute(
                "insert into jk_question(catOne,catTwo,catThree,catFour,title,gender,age,startTime,question,questionTime,questionTag,questionUrl) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [item['catOne'], item['catTwo'], item['catThree'], item['catFour'], item['title'], item['gender'],
                 item['age'], item['startTime'], item['question'], item['questionTime'], item['questionTag'],
                 item['questionUrl']]
            )

        except Exception as e:
            print('Insert error:', e)
            con.rollback()
        else:
            con.commit()
        con.close()
        return item

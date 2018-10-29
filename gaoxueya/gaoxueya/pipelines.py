# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql
from scrapy.conf import settings

class GaoxueyaPipeline(object):
    def process_item(self, item, spider):
        host = settings['MYSQL_HOST']
        user = settings['MYSQL_USER']
        psd = settings['MYSQL_PASSWORD']
        db = settings['MYSQL_DBNAME']
        port = settings['MYSQL_PORT']

        con=pymysql.connect(host=host,user=user,passwd=psd,db=db,port=port)

        cue=con.cursor()

        try:
            cue.execute("insert into gaoxueya_doctor(doctor,level,good_num,bad_num,answers_time,answers,wt_url) values(%s,%s,%s,%s,%s,%s,%s)",
                        [item['doctor'], item['level'], item['good_num'], item['bad_num'], item['answers_time'], item['answers'],item['wt_url']])
            cue.execute("insert into gaoxueya_answers(question_title,question_time, disease, question, question_url) VALUES(%s,%s,%s,%s,%s)",
                        [item['title'], item['question_time'], item['disease'], item['question'], item['wt_url']])
        except Exception as e:
            print('Insert error:', e)
            con.rollback()
        else:
            con.commit()
        con.close()
        return item




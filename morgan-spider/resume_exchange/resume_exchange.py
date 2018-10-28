#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue@mofanghr.com
@software: PyCharm
@file: resume_exchange.py
@create at: 2017-11-24 13:27

这一行开始写关于本文件的说明与解释
"""

from __future__ import print_function
import base64
import gzip
import json
import uuid
from StringIO import StringIO

import datetime
import xlrd
import sys

from mns.account import Account
from mns.queue import Message

from crwy.spider import Spider
import pymysql

job_type_mapping = {
    "JAVA": "Java",
    "NET": ".NET",
    "ANDROID": "Android",
    "IOS": "iOS",
    "UI": "UI设计师",
    "UE": "UE设计",
    "安卓": "Android",
    "PHP": "PHP开发工程师",
    "C++": "C++",
    "U3D": "U3D",
    "ETL": "ETL",
    "WEB": "WEB前端开发",
    "系统工程师": "系统工程师",
    "数据挖掘": "数据挖掘",
    "测试": "软件测试",
    "开发工程师": "互联网软件开发工程师",
    "运维": "IT运维",
    "福利专员": "薪酬福利专员/助理",
    "业务代表": "业务代表",
    "前台": "前台",
    "售前": "售前/售后技术支持工程师",
    "文员": "助理/秘书/文",
    "会计助理": "会计助理/文员",
    "翻译": "翻译",
    "运营专员": "运营主管/专员",
    "销售顾问": "销售顾问",
    "行政专员": "行政专员/助理",
    "行政经理": "行政经理/主管/办公室主",
    "销售专员": "销售专员",
    "绩效专员": "绩效专员",
    "运营经理": "运营经理",
    "出纳": "出纳员",
    "开发部文员": "IT技术文员/助理",
    "研发主管": "研发主管",
    "产品经理": "产品经理",
    "HR": "招聘HR",
    "文案编辑": "店铺文案编辑",
    "文案策划": "文案策划"
}

MYSQL_CONF = {
    'charset': 'utf8mb4',
    # 'cursorclass': pymysql.cursors.DictCursor,
    'host': 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'spider_admin',
    'password': 'n4UZknFH6F',
    'db': 'spider'
}

MYSQL_CONF_TEST = {
    'charset': 'utf8mb4',
    # 'cursorclass': pymysql.cursors.DictCursor,
    'host': '10.0.3.52',
    'port': 3306,
    'user': 'bi_admin',
    'password': 'bi_admin#@1mofanghr',
    'db': 'spider'
}

MNS_ACCID = 'LTAIf2I0xlEogGx5'
MNS_ACCKEY = '14EJ0FhqZL5czEdw5E54pAjyVkdtbI'
# MNS_ENDPOINT = 'http://1315265288610488.mns.cn-beijing-' \
#                'internal-vpc.aliyuncs.com'
MNS_ENDPOINT = 'http://1315265288610488.mns.cn-beijing.aliyuncs.com'
MNS_TOKEN = ''
MNS_QUEUE = 'morgan-queue-resume-parse'
#
# MNS_QUEUE = 'morgan-queue-test-resume-parse'

PROJECT_NAME = 'resume_exechange'


class ResumeExchange(Spider):
    def __init__(self):
        super(ResumeExchange, self).__init__()
        self.mns_account = Account(MNS_ENDPOINT, MNS_ACCID, MNS_ACCKEY,
                                   MNS_TOKEN)
        self.mns_client = self.mns_account.get_queue(MNS_QUEUE)

    def get_targetJobType(self, emailJobType):
        for item in job_type_mapping:
            if item.upper() in emailJobType:
                return job_type_mapping[item]
        return

    def save2db(self, sql, data):
        # conn = pymysql.Connect(**MYSQL_CONF_TEST)
        conn = pymysql.Connect(**MYSQL_CONF)
        cur = conn.cursor()
        try:

            cur.execute(sql, data)
            conn.commit()
            cur.execute("select last_insert_id()")
            sql_id = cur.fetchone()[0]
            self.logger.info("入库成功. %s" % sql_id)
            return sql_id
        except Exception as e:
            self.logger.exception(e)
            return
        finally:
            cur.close()
            conn.close()

    def save2mns(self, sql_id, data_for_mns, trackId):
        try:
            kafka_data = {
                "content": data_for_mns,
                "channelType": "WEB",
                "interfaceType": "NORMAL",
                "resourceDataType": "PARSED",
                "resourceType": "RESUME_INBOX",
                "source": data_for_mns['source'],
                "traceID": trackId,
                "callSystemID": PROJECT_NAME
            }
            dumps = json.dumps(kafka_data, ensure_ascii=False)

            buf = StringIO()
            f = gzip.GzipFile(mode='wb', fileobj=buf)
            f.write(dumps)
            f.close()
            msg_body = base64.b64encode(buf.getvalue())
            msg = Message(msg_body)
            self.mns_client.send_message(msg)
            self.logger.info("推送mns成功. %s" % str(sql_id))
        except Exception as e:
            self.logger.exception("推送mns失败: %s" % e)

    def run(self, file_path):
        try:
            with open(file_path, 'r') as file:
                self.logger.info("开始上载简历.")
                for index, line in enumerate(file):
                    # self.process1(index=index,line=line)
                    self.process2(index=index, line=line)
        except Exception as e:
            self.logger.exception(e)

    def process2(self, index, line):
        try:
            self.logger.info('当前处理的内如：%s %s' % (index, line))
            name, mobile, gender, degree, age, work_exp, target_job_type, register_location = line.strip(
                '\n').split('\t')
        except ValueError:
            self.logger.warning("该行读取错误: " + str(index))
            return
        now_year = datetime.datetime.now().year
        birthday = ''
        if age:
            birthday = str(now_year - int(age)) + '-05-15'
        uuid_ = str(uuid.uuid1())
        data = (
            name, mobile, gender, degree, birthday, work_exp, target_job_type, register_location,
            datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d'),
            datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
            datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
            uuid_
        )
        sql = '''
            INSERT INTO spider.resume_parsed
            (name,mobile,gender,degree,birthday,workExperience,targetJobType,registerLocation,targetWorkLocation,workType,status,source,targetSalary,resumeUpdateTime,createTime,updateTime,trackId) 
            VALUES (%s, %s, %s,  %s, %s, %s, %s, %s,'西安','全职','正在找工作','RESUME_EXCHANGE','面议',%s,%s,%s,%s)
        '''
        sql_id = self.save2db(sql=sql, data=data)
        self.logger.info('解析入库成功 %s' % sql_id)
        data_for_mns = {
            'id': sql_id,
            'name': name,
            'mobile': mobile,
            'gender': gender,
            'degree': degree,
            'birthday': birthday,
            'workExperience': work_exp,
            'targetJobType': target_job_type,
            'registerLocation': register_location,
            'targetWorkLocation': '西安',
            'workType': '全职',
            'status': '正在找工作',
            'source': 'RESUME_EXCHANGE',
            'targetSalary': '面议',
            'resumeUpdateTime': datetime.datetime.strftime(
                datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
            'createTime': datetime.datetime.strftime(
                datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
            'updateTime': datetime.datetime.strftime(
                datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
            'trackId': uuid_,
        }

        self.save2mns(sql_id, data_for_mns, uuid_)
        self.logger.info('处理完毕 %s' % sql_id)

    def process1(self, index, line):
        try:
            name, emailJobType, targetJobType, gender, birthday, mobile, \
            workExperience, email, currentLocation, registerLocation, \
            career, education, degree, targetSalary = line.strip(
                '\n').split('\t')
        except ValueError:
            self.logger.warning("该行读取错误: " + str(index))
            return
        try:
            emailJobType = emailJobType.replace(
                '北京', '').replace('求职', '').replace('/', ',')
            targetJobType = self.get_targetJobType(emailJobType)
            if not targetJobType:
                targetJobType = emailJobType

            birthday = birthday.replace('/', '-')
            career_lst = []
            if career:
                for item in career.split('|$|'):
                    career_lst.append({"companyName": item})
                career = json.dumps(career_lst, ensure_ascii=False)

            education_lst = []

            if education:
                for item in education.split('|$|'):
                    education_lst.append({"schoolName": item})
                education = json.dumps(education_lst, ensure_ascii=False)
            now = datetime.datetime.now()
            trackId = str(uuid.uuid1())
            data = (name, emailJobType, targetJobType, gender,
                    birthday, mobile,
                    workExperience, email, currentLocation,
                    registerLocation,
                    career, education, degree, targetSalary,
                    now,
                    '2017-11-01 00:00:00',
                    trackId)
            sql = """
                      INSERT INTO spider.resume_parsed(name, emailJobType, 
                      targetJobType, gender, birthday, mobile, \
                              workExperience, email, currentLocation, registerLocation, \
                              career, education, degree, targetSalary, createTime, 
                              updateTime, trackId,
                              createBy, source, workType, status) VALUES (%s, %s, %s, 
                              %s, %s, %s, %s, %s, %s, 
                              %s, %s, %s, %s, %s, %s, %s, %s, 'PYTHON', 
                              'RESUME_EXCHANGE', 
                              '全职', '正在找工作')
                      """
            sql_id = self.save2db(sql=sql, data=data)
            if not sql_id:
                return
            data_for_mns = {
                'id': sql_id,
                'name': name,
                'emailJobType': emailJobType,
                'targetJobType': targetJobType,
                'gender': gender,
                'birthday': birthday,
                'mobile': mobile,
                'workExperience': workExperience,
                'email': email,
                'currentLocation': currentLocation,
                'registerLocation': registerLocation,
                'career': career_lst,
                'education': education_lst,
                'degree': degree,
                'targetSalary': targetSalary,
                'createTime': datetime.datetime.strftime(
                    now, '%Y-%m-%d %H:%M:%S'),
                'updateTime': '2017-11-01 00:00:00',
                'trackId': trackId,
                'source': 'RESUME_EXCHANGE',
                'workType': '全职',
                'status': '正在找工作'
            }

            self.save2mns(sql_id, data_for_mns, trackId)
            self.logger.info(
                '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % (
                    index, name, emailJobType, targetJobType,
                    gender,
                    birthday, mobile,
                    workExperience, email, currentLocation,
                    registerLocation,
                    career, education, degree, targetSalary))
        except Exception as e:
            self.logger.exception(e)
            return


if __name__ == '__main__':
    runner = ResumeExchange()
    # runner.run()
    try:
        runner.run(file_path=sys.argv[1])
    except IndexError:
        print("未指定目标文件.\n")

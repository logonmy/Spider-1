#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com

from __future__ import print_function

import sys
from gevent import monkey

monkey.patch_all()
import re
import json
import time
import datetime
import uuid
import gevent
import base64
import gzip
import logging.config
from StringIO import StringIO
from utils.db import Database, ResumeRaw, TEmail
from crwy.utils.queue.RedisQueue import RedisQueue
from crwy.utils.extend.dingding_robot import DingDingRobot
from crwy.utils.logger import Logger
from mns.account import Account
from mns.queue import Message
from conf.settings import *
# from mf_utils.data.RedisHash import RedisHash
from mf_utils.mail import MailReceiver
from mf_utils.common import remove_emoji
from mf_utils.decorates import cls_catch_exception
from retrying import retry

logging.config.fileConfig("./conf/logger.conf")

project_name = "mail_auto"

RECEIVER_NUM = 10

WARNING_NUM = 500


RUN_STATUS = {}


class Runner(object):
    def __init__(self):
        # 读取邮箱信息
        self.db = Database(
            'mysql+mysqldb://spider_admin:'
            'n4UZknFH6F@rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com:'
            '3306/spider?charset=utf8', encoding='utf-8')

        # 初始化数据库
        self.db1 = Database('mysql+mysqldb://%s:%s@%s:%s/%s?charset=utf8'
                            % (MYSQL_USER, MYSQL_PASSWD,
                               MYSQL_HOST, MYSQL_PORT, MYSQL_DB),
                            encoding='utf-8')

        # 初始化MNS
        self.mns_account = Account(MNS_ENDPOINT, MNS_ACCID, MNS_ACCKEY,
                                   MNS_TOKEN)
        self.mns_client = self.mns_account.get_queue(MNS_QUEUE)

        self.logger = Logger.timed_rt_logger()
        self.queue = RedisQueue('t_mail', host=REDIS_HOST, port=REDIS_PORT)
        # self.h = RedisHash('t_mail_run_status', host=REDIS_HOST,
        #                    port=REDIS_PORT)
        self.robot = DingDingRobot(
            access_token="eb749abfe9080a69da6524b77f589b8f6ddbc"
                         "c182c7a41bf095b095336edb0a1")

    def deliver(self, subject):
        try:
            if '51job.com' in subject:
                source = "FIVE_ONE"
                deliverJobName = re.search('(?<=申请贵公司).*(?=（)',
                                           subject).group().strip()
                subject_ = subject.replace('（', '(').replace('）', ')')
                deliverCity = re.findall('(?<=\().*?(?=\))', subject_)[
                    -1].strip()

            elif '58.com' in subject:
                # (58.com)应聘贵公司供应链管理8k六险一金-北京 朝阳-刘春雨
                source = "FIVE_EIGHT"
                deliverJobName = re.search('(?<=应聘贵公司).*?(?=-)',
                                           subject).group().strip()
                deliverCity = re.findall('(?<=-).*?(?=\s+)', subject)[
                    -1].strip()
            elif 'Zhaopin.com' in subject:
                source = "ZHI_LIAN"
                deliverJobName = re.search(
                    '(?<=应聘).*?(?=-)', subject).group().strip()
                deliverCity = re.findall('(?<=-).*?(?=-)', subject)[-1].strip()

            elif '来自猎聘网' in subject:
                print(subject)
                source = "LIE_PIN"
                deliverJobName = re.search(
                    '(?<=【).*?(?=_)', subject).group().strip()
                deliverCity = re.search(
                    '(?<=_).*(?=】)', subject).group().strip()
            else:
                return None, None, None
            return source, deliverJobName, deliverCity
        except:
            return None, None, None

    def save2db(self, source, email, subject, content, emailJobType,
                emailCity, deliverJobName, deliverJobCity, trackId):
        try:
            createTime = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
            data = {
                'source': source,
                'email': email,
                'subject': subject,
                'content': content,
                'emailJobType': emailJobType,
                'emailCity': emailCity,
                'createBy': email,
                'updateBy': 'PYTHON-RECEIVER',
                'deliverJobName': deliverJobName,
                'deliverJobCity': deliverJobCity,
                'createTime': createTime,
                'trackId': trackId
            }
            try:
                self.db1.session.execute(
                    ResumeRaw.__table__.insert(), data
                )
                self.db1.session.commit()
            except Exception as e:
                self.db1.session.rollback()
                self.logger.exception("入库失败, 回滚： %s" % e)
                self.robot.send_text("邮箱采集，入库失败： %s" % email)
                time.sleep(600)
                return
            sql_id = self.db1.session.execute(
                "select last_insert_id()").first()[0]
            # print(sql_id)

            self.logger.info("入库成功. %s" % str(sql_id))
            return sql_id
        except Exception as e:
            self.logger.exception("入库失败： %s" % e)
            return

    def save2mns(self, sql_id, source, content, emailJobType, emailCity,
                 deliverJobName, deliverJobCity, trackId):
        try:
            resume_uuid = uuid.uuid1()
            kafka_data = {
                "channelType": "WEB",
                "content": {
                    "content": content,
                    "id": sql_id,
                    "createBy": "python",
                    "createTime": int(time.time() * 1000),
                    "ip": '',
                    'emailJobType': emailJobType,
                    'emailCity': emailCity,
                    'deliverJobName': deliverJobName,
                    'deliverJobCity': deliverJobCity,
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": '',
                    "source": source,
                    "trackId": str(resume_uuid),
                    "avatarUrl": '',
                    'trackId': trackId
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_EMAIL",
                "source": source,
                "trackId": trackId,
                "traceID": trackId,
                "callSystemID": project_name
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

    def producer(self):
        # self.queue.clean()
        res = self.db.session.query(TEmail).filter_by(valid=1).all()
        # res = self.db.session.query(TEmail).filter(TEmail.email.in_((
        #     'wenwen2.li@911791.com',
        # )))
        if not self.queue.empty():
            self.logger.info("剩余%s个企业邮箱未处理！" % str(self.queue.qsize()))
            sys.exit()
        # self.queue.clean()
        for item in res:
            self.queue.put((item.pop3_host.encode('utf-8'),
                            item.username.encode('utf-8'),
                            item.password.encode('utf-8'),
                            item.position_type.encode('utf-8'),
                            item.preferred_city.encode('utf-8'),
                            item.source.encode('utf-8')))
        self.logger.info("总计加载%s个企业邮箱！" % str(self.queue.qsize()))

    @retry(stop_max_attempt_number=3)
    @cls_catch_exception
    def deal_with_messages(self, imap, message_list, username,
                           delete_folder, position_type, preferred_city):
        message_list, msg_data = imap.download_message_list(message_list)

        if not msg_data:
            self.logger.warning("%s: 没有收到新邮件." % username)
            return

        self.logger.info("%s: 收到%s个新邮件"
                         % (username, str(len(message_list))))
        # print(message_list)
        for msg_id, message in msg_data.items():

            res = imap.get_content(message)
            if not res:
                # message_list.append(message)
                continue
            try:
                subject = res.get('subject').encode('utf-8',
                                                    'ignore')
            except UnicodeDecodeError:
                subject = res.get('subject')
            content = res.get('body')
            content = remove_emoji(content)

            source, deliverJobName, deliverJobCity = self.deliver(
                subject)
            if not deliverJobName:
                self.logger.warning("%s: 收到非期待邮件. subject: %s"
                                    % (username, subject))
                try:
                    imap.delete_message([msg_id], delete_folder)
                    self.logger.info("%s: 非期待邮件<%s>成功转移到“已删除”"
                                     % (username, msg_id))
                except Exception as e:
                    self.logger.exception(
                        "%s: 非期待邮件<%s>转移到“已删除”失败 %s" % (
                            username, msg_id, e))
                continue

            self.logger.info("%s\t%s\t%s\t" % (source,
                                               deliverJobName,
                                               deliverJobCity))

            trackId = str(uuid.uuid4())

            sql_id = self.save2db(
                source, username, subject, content,
                position_type, preferred_city,
                deliverJobName, deliverJobCity, trackId=trackId
            )

            if not sql_id:
                continue

            self.save2mns(sql_id, source.encode('utf-8'),
                          content.encode('utf-8'),
                          position_type, preferred_city,
                          deliverJobName, deliverJobCity, trackId)

            try:
                imap.delete_message([msg_id], delete_folder)
                self.logger.info("%s: 邮件<%s>成功转移到“已删除”"
                                 % (username, msg_id))
            except Exception as e:
                self.logger.exception(
                    "%s: 邮件<%s>转移到“已删除”失败 %s" % (
                        username, msg_id, e))

    def inactive_account(self, username):
        global RUN_STATUS
        RUN_STATUS[username] = ''
        self.logger.info('该帐号[%s]运行完毕.' % username)

    def consumer(self):
        while True:
            try:
                if not self.queue.empty():
                    host, username, password, position_type, preferred_city, \
                    source1 = eval(self.queue.get())
                    # print(host, username, password)
                    try:
                        if RUN_STATUS.get(username, ''):
                            self.logger.warning('该帐号[%s]当前正在运行.' % username)
                            continue
                        RUN_STATUS[username] = 1
                        self.logger.info('将该帐号[%s]标识为正在运行.' % username)

                        imap = MailReceiver(host, username, password)
                        try:
                            imap.server.login(username, password)
                            self.logger.info("%s: 登录成功 <%s>"
                                             % (username, self.queue.qsize()))
                        except Exception as e:
                            if "LOGIN Login error" in e:
                                self.robot.send_text("邮箱登录异常： %s %s %s"
                                                     % (username, password, host))
                            self.logger.exception("%s: 登录失败 %s <%s>"
                                                  % (username, e,
                                                     self.queue.qsize()))
                            self.inactive_account(username)
                            continue
                        try:
                            folder_list = imap.folder_list()
                        except Exception as e:
                            self.logger.exception("%s: 邮件箱加载失败 %s"
                                                  % (username, e))
                            self.inactive_account(username)
                            continue

                        if not folder_list:
                            self.inactive_account(username)
                            continue
                        # print(folder_list)
                        if "Deleted Messages" in folder_list:
                            delete_folder = u"Deleted Messages"
                        elif "已删除邮件" in folder_list:
                            delete_folder = u"已删除邮件"
                        else:
                            delete_folder = u"已删除"

                        self.logger.info("%s: 开始收取邮件." % username)
                        try:
                            message_list = imap.message_list()
                        except Exception as e:
                            self.logger.exception("%s: 邮件list加载失败 %s"
                                                  % (username, e))
                            self.inactive_account(username)
                            continue

                        if len(message_list) > WARNING_NUM:
                            self.robot.send_text("%s邮件数量超过告警阈值：%s"
                                                 % (username, WARNING_NUM))

                        if len(message_list) > RECEIVER_NUM:
                            tmp_lst = []
                            for item in xrange(0, len(message_list), RECEIVER_NUM):
                                tmp_lst.append(
                                    message_list[item:item + RECEIVER_NUM])

                            self.logger.info("%s: 共收到邮件%s封，开始进行分组收取，总计%s组"
                                             % (username, len(message_list),
                                                len(tmp_lst)))

                            for index, tmp in enumerate(tmp_lst):
                                self.logger.info("%s: 当前开始收取第%s组邮件."
                                             % (username, index+1))
                                self.deal_with_messages(imap, tmp,
                                                        username,
                                                        delete_folder,
                                                        position_type,
                                                        preferred_city)
                        else:
                            self.logger.info("%s: 共收到邮件%s封。"
                                             % (username, len(message_list)))
                            self.deal_with_messages(imap, message_list,
                                                    username,
                                                    delete_folder,
                                                    position_type,
                                                    preferred_city)
                        imap.close()
                        self.inactive_account(username)
                    except Exception as e:
                        self.inactive_account(username)
                        self.logger.exception(e)
                    # else:
                    #     self.logger.info("finished!")
                    #     break
            except Exception as e:
                global RUN_STATUS
                RUN_STATUS = {}
                self.logger.exception(e)


def main():
    runner = Runner()
    runner.consumer()


if __name__ == '__main__':

    try:
        worker = sys.argv[1]
    except IndexError:
        print("Usage: python mail_auto.py [worker]\n")
        sys.exit()

    if worker == "producer":
        runner = Runner()
        runner.producer()
    elif worker == "consumer":
        gevent.joinall([
            gevent.spawn(main) for i in xrange(COROUTINE)
        ])
    else:
        print("Invalid worker [%s]\n" % worker)
        sys.exit()

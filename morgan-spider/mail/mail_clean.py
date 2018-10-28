#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: mail_clean.py
@create at: 2018-01-03 18:23

这一行开始写关于本文件的说明与解释
"""

import logging.config

import datetime
from mf_utils.sql.mysql import MysqlHandle
from mf_utils.core import BaseInitCore
from mf_utils.logger import Logger
from mf_utils.mail import MailReceiver
from mf_utils.extend.dingding_robot import DingDingRobot
from mf_utils.common import datetime2str

logging.config.fileConfig('./conf/logger_clean.conf')


class MailClean(BaseInitCore):
    def __init__(self):
        super(MailClean, self).__init__()
        self.logger = Logger.rt_logger()
        self.logger.setLevel(logging.DEBUG)
        self.mysql_handle = MysqlHandle(
            host='rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
            port=3306,
            user='spider_admin',
            passwd='n4UZknFH6F'
        )
        self.robot = DingDingRobot(
            access_token="eb749abfe9080a69da6524b77f589b8f6ddbc"
                         "c182c7a41bf095b095336edb0a1")

    def run(self):
        try:
            email_lst = self.mysql_handle.query_by_sql(
                '''
                select email, password, pop3_host from spider.t_email 
                WHERE valid=1 and pop3_host!='imap.exmail.qq.com'
                '''
            )

            if email_lst:
                self.logger.info("总计加载邮箱%s个." % len(email_lst))
            for index, item in enumerate(email_lst):
                username, password, host = item
                self.logger.info("开始处理： %s | %s | %s"
                                 % item)
                imap = MailReceiver(host, username, password)
                try:
                    imap.server.login(username, password)
                    self.logger.info("%s: 登录成功 <%s>"
                                     % (username, index))
                except Exception as e:
                    if "LOGIN Login error" in e:
                        self.robot.send_text("邮箱登录异常： %s %s %s"
                                             % (username, password, host))
                    self.logger.exception("%s: 登录失败 %s <%s>"
                                          % (username, e, index))
                    continue

                try:
                    folder_list = imap.folder_list()
                except Exception as e:
                    self.logger.exception("%s: 邮件箱加载失败 %s" % (username, e))
                    continue

                if not folder_list:
                    continue
                # print(folder_list)
                if "Deleted Messages" in folder_list:
                    # 腾讯
                    delete_folder = u"Deleted Messages"
                elif "已删除邮件" in folder_list:
                    # 阿里云
                    delete_folder = u"已删除邮件"
                else:
                    # 163
                    delete_folder = u"已删除"

                # print delete_folder

                before_day = 7
                check_day = 60

                start_date = datetime.datetime.now() - datetime.timedelta(
                    days=before_day)
                # date = datetime.datetime.now()
                end_date = start_date - datetime.timedelta(days=check_day)

                self.logger.info("当前处理时间段为： %s 到 %s" %
                                 (datetime2str(start_date, fmt='%Y-%m-%d'),
                                  datetime2str(end_date, fmt='%Y-%m-%d')))

                # search_ = 'BEFORE %s' % fmt_date
                for day in xrange(check_day):
                    date = start_date - datetime.timedelta(days=day)
                    fmt_date = datetime.datetime.strftime(date, "%d-%b-%Y")

                    search_ = 'ON %s' % fmt_date

                    try:
                        message_list = imap.message_list(
                            mailbox=delete_folder, search_=search_)
                    except Exception as e:
                        self.logger.exception("%s: 邮件list加载失败 %s"
                                              % (username, e))
                        continue

                    if not message_list:
                        self.logger.debug("%s: 没有 [%s] 已删除的邮件"
                                          % (username, search_))
                        continue

                    self.logger.info("%s: [%s] 匹配到邮件%s个"
                                     % (username, search_, len(message_list)))

                    if imap.delete_message(message_list,
                                           deleted_folder=None) is not True:
                        self.logger.warning("%s 删除失败." % username)
                        continue
                    self.logger.info("%s 删除成功." % username)

                self.logger.info('%s 邮箱处理完毕.' % username)
                try:
                    imap.close()
                except Exception as e:
                    self.logger.exception('imap close 异常： %s ' % e)
                    continue

        except Exception as e:
            self.logger.exception(e)


if __name__ == '__main__':
    runner = MailClean()
    runner.run()

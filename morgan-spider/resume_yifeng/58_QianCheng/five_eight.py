#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com

import gevent
import json
import time
from spider import ResumeSpider
from gevent import monkey
from utils.decorator import retry
monkey.patch_all()


class FiveEight(ResumeSpider):
    def __init__(self, worker=None, site=None):
        super(FiveEight, self).__init__(worker=worker, site=site)
        self.cookies = {'isSaveUserInfo': '1', 'status': '1', 'userEmail': '549409587&qq.com', 'shareCode': '21053b6m', 'JSESSIONID': 'B098AF7E91E3A7143B8373D9BC6BD8CA'}

    @retry(attempt=3)
    def get_resume_list(self, *args, **kwargs):
        flag = True
        while flag:
            url = "http://www.yifengjianli.com/wbresume/wbResuSearch"
            data = {
                'resumeKeyword': '',
                'resumeKeyword_name': '',
                'currentCity': 'bj',
                'currentCity_name': 'bj$北京',
                'currentJob': '',
                'currentJob_name': '',
                'updateTime': '',
                'updateTime_name': '',
                'sex': '',
                'sex_name': '',
                'age': '',
                'age_name': '',
                'minAge': '',
                'minAge_name': '',
                'maxAge': '',
                'maxAge_name': '',
                'workExperience': '',
                'workExperience_name': '',
                'education': '',
                'education_name': '',
                'expectSalary': '',
            }
            res = self.downloader.download(url=url, method='POST', data=data,
                                           cookies=self.cookies,
                                           proxies=self.proxies)
            if json.loads(res.content).get("code") == 300:
                self.log.warning("%s[%s]: get_resume_list 当前处于未登录状态！" %
                                 (self.site, self.worker))
                flag = False
                self.login()
                continue
            else:
                return json.loads(res.content).get("resumeList").get("resumeList")

    @retry(attempt=3)
    def get_resume(self, *args, **kwargs):
        flag = True
        while flag:
            url = "http://www.yifengjianli.com/wbresume/wbResuDetail"
            data = {
                'id': args[0]
            }
            res = self.downloader.download(url=url, method='POST', data=data,
                                           cookies=self.cookies,
                                           proxies=self.proxies)
            if res.status_code != 200:
                flag = False
                self.login()
                continue
            else:
                return res.content

    def download_resume(self, *args, **kwargs):
        print kwargs


def run(worker="worker0"):
    do = FiveEight(worker=worker, site="YI_FENG_58")
    # do.login('408742431@qq.com', 'qwer1234')
    page_num = 1
    flag = True
    while flag:
        resume_list = do.get_resume_list(page_num=page_num)
        if len(resume_list) == 0:
            flag = False
            do.log.info("爬完了 ^_^!!!")
            continue

        for item in resume_list:
            id = item.get('id')
            if do.s_filter.sadd(str(id)) is False:
                do.log.info("该简历已经采集过了: %s" % id.encode('utf-8'))
                continue
            resume_result = do.get_resume(item.get('id'))
            time.sleep(2)
            print page_num, resume_result
            do.save(resume_result=resume_result)
        page_num += 1
        continue

if __name__ == '__main__':
    run()
    # gevent.joinall(
    #     [gevent.spawn(run, worker="worker%d" % i) for i in range(3)]
    # )


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


class FiveOne(ResumeSpider):
    def __init__(self, worker=None, site=None):
        super(FiveOne, self).__init__(worker=worker, site=site)

    @retry(attempt=3)
    def get_resume_list(self, *args, **kwargs):
        if kwargs['page_num'] > 5:
            kwargs['page_num'] = '_ma'
        flag = True
        while flag:
            url = "http://www.yifengjianli.com/jobResume/jobResuSearch"
            data = {
                'hidAddress': '',
                'age': '年龄',
                'minAge': '',
                'maxAge': '',
                'expJob': '',
                'expIndustry': '',
                'expJobArea': '期望工作地',
                'hidExpJobArea': '',
                'jobYear': '',
                'minJobYear': '',
                'maxJobYear': '',
                'education': '',
                'minEducation': '',
                'maxEducation': '',
                'language': '不限',
                'shuLian': '不限',
                'lanShuLian': '语言',
                'nowSalary': '',
                'nowMinSalary': '不限',
                'nowMaxSalary': '不限',
                'expSalary': '',
                'expMinSalary': '不限',
                'expMaxSalary': '不限',
                'hukou': '户口',
                'hidHukou': '',
                'major': '专业',
                'hidMajor': '',
                'sex': '性别',
                'updateTime': '近1年',
                'jobStatus': '求职状态',
                'englishlevel': '英语等级',
                'hidSearchValue': '##0####################近1年|6##1#0###0#0#0',
                'pageIndex': 'pagerBottomNew_btnNum%s'
                             % str(kwargs['page_num']),
                'pageSize': '',
                'send_cycle': '1',
                'send_time': '7',
                'send_sum': '10',
                'hidDisplayType': '0',
                'currentSource': '1',
            }
            res = self.downloader.download(url=url, method='POST',
                                           data=data, cookies=self.cookies,
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
            url = "http://www.yifengjianli.com/jobResume/jobResuDetail"
            detailUrl, detailId = args
            data = {
                'detailUrl': detailUrl,
                'detailId': detailId
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
    do = FiveOne(worker=worker, site="YI_FENG_51")
    # do.login('549409587@qq.com', '891211')
    print do.cookies
    page_num = 1
    flag = True
    while flag:
        resume_list = do.get_resume_list(page_num=page_num)
        if len(resume_list) == 0:
            flag = False
            do.log.info("爬完了 ^_^!!!")
            continue

        for item in resume_list:
            detail_url = item.get('detail_url')
            detail_id = item.get('detail_id')

            if do.s_filter.sadd(str((detail_url,
                                     detail_id))) is False:
                do.log.info("该简历已经采集过了: %s" % detail_id.encode('utf-8'))
                continue
            resume_result = do.get_resume(detail_url, detail_id)
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

#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: company_position.py
@create at: 2018-08-17 11:45

这一行开始写关于本文件的说明与解释
"""

import gevent
import json
import re

from mf_utils.core import BaseInitCore
from mf_utils.logger import Logger
from mf_utils.decorates import cls_catch_exception
from mf_utils.sql.redis_m import get_redis_client
from conf import settings
from gevent import monkey
monkey.patch_all()


redis_client = get_redis_client(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD
)


def format_zhi_lian_salary(salary):
    if u'薪资面议' in salary:
        return ''
    elif u'K以下' in salary:
        salary = re.findall('\d+', salary)[0]
        return '0-' + str(int(salary) * 1000)
    elif u'K' in salary:
        l, r = salary.encode('utf-8').replace('K', '').split('-')
        return '-'.join([str(int(float(l) * 1000)), str(int(float(r) * 1000))])
    return salary


def format_five_one_salary(salary):
    if u'千/月' in salary:
        l, r = salary.strip(u'千/月').split('-')
        return '-'.join([str(int(float(l) * 1000)), str(int(float(r) * 1000))])
    elif u'万/月' in salary:
        l, r = salary.strip(u'万/月').split('-')
        return '-'.join(
            [str(int(float(l) * 10000)), str(int(float(r) * 10000))])
    elif u'万/年' in salary:
        l, r = salary.strip(u'万/年').split('-')
        return '-'.join([str(int(float(l) * 10000) / 12),
                         str(int(float(r) * 10000) / 12)])

    return salary


class CompanyPosition(BaseInitCore):
    def __init__(self):
        super(CompanyPosition, self).__init__()
        self.logger = Logger.timed_rt_logger()

    def get_zhi_lian_position_list(self, company_name, start=0, res_lst=None):
        try:
            url = 'https://fe-api.zhaopin.com/c/i/sou?' \
                  'start={start}&pageSize=60&cityId=489' \
                  '&kw={company_name}' \
                  '&kt=2'.format(start=start, company_name=company_name)
            res = self.html_downloader.download(url)
            data_lst = json.loads(res.text).get('data').get('results')
            total = int(json.loads(res.text).get('data').get('numFound'))
            current_page = int(re.findall(
                '(?<=start=).*?(?=&)', res.url)[0]) / 60 + 1
            self.logger.debug('current_page - %s' % current_page)

            for data in data_lst:
                position_info = dict()
                position_info['site'] = 'ZHI_LIAN'
                position_info['city'] = data.get('city').get('display')
                position_info['jobName'] = data.get('jobName')
                position_info['jobId'] = data.get('number')
                try:
                    position_info[
                        'jobDescription'] = self.get_zhi_lian_position_detail(
                        job_id=position_info['jobId']
                    )
                except Exception:
                    continue
                position_info['salary'] = format_zhi_lian_salary(
                    data.get('salary'))
                position_info['workExp'] = data.get('workingExp').get('code')
                position_info['degree'] = data.get('eduLevel').get('name')
                position_info['pubDate'] = data.get('updateDate')
                # print json.dumps(position_info, ensure_ascii=False)

                if len(res_lst) >= 60:
                    return res_lst
                res_lst.append(position_info)

            start = current_page * 60
            if (current_page - 1) * 60 < total:
                self.get_zhi_lian_position_list(
                    company_name, start=start, res_lst=res_lst)

            return res_lst
        except Exception as e:
            self.logger.exception(e)
            return res_lst

    def get_five_one_position_list(self, company_name, page=1, res_lst=None):
        try:
            url = 'https://search.51job.com/list/000000,' \
                  '000000,0000,00,9,99,{company_name}' \
                  ',1,{page}.html'.format(company_name=company_name, page=page)

            res = self.html_downloader.download(url)
            soups = self.html_parser.parser(res.content)

            current_page = int(soups.find(
                'div', class_='p_in').find('li', class_='on').text)
            total_page = int(re.findall('\d+', soups.find(
                'div', class_='p_in').find('span', class_='td').text)[0])
            self.logger.debug('current_page - %s' % current_page)

            data_lst = soups.find(
                'div', id='resultList').find_all('div', class_='el')[1:]

            for data in data_lst:
                position_info = dict()
                position_info['site'] = 'FIVE_ONE'
                position_info['jobName'] = data.find('a').get('title')
                position_info['jobId'] = data.find('input').get('value')
                try:
                    city, exp, degree, desc = self.get_five_one_position_detail(
                        job_id=position_info['jobId']
                    )
                except Exception:
                    continue
                position_info['city'] = city
                position_info['jobDescription'] = desc
                position_info['salary'] = format_five_one_salary(
                    data.find('span', class_='t4').text)
                position_info['workExp'] = exp
                position_info['degree'] = degree
                position_info['pubDate'] = data.find('span', class_='t5').text
                # print json.dumps(position_info, ensure_ascii=False)

                if len(res_lst) >= 30:
                    return res_lst
                res_lst.append(position_info)

            if current_page < total_page:
                page += 1
                self.get_five_one_position_list(
                    company_name, page=page, res_lst=res_lst)

            return res_lst
        except Exception as e:
            self.logger.exception(e)
            return res_lst

    @cls_catch_exception
    def get_zhi_lian_position_detail(self, job_id):
        url = 'https://jobs.zhaopin.com/{}.htm'.format(job_id)
        headers = {
            'Cookie': 'ZP_OLD_FLAG=false;'
        }
        res = self.html_downloader.download(url, headers=headers)
        self.logger.debug('get detail {}'.format(job_id))
        soups = self.html_parser.parser(res.content)
        position_desc = soups.find('div', class_='pos-ul').text.strip()
        return position_desc

    @cls_catch_exception
    def get_five_one_position_detail(self, job_id):
        url = 'https://jobs.51job.com/all/{}.html'.format(job_id)
        res = self.html_downloader.download(url)
        self.logger.debug('get detail {}'.format(job_id))
        soups = self.html_parser.gbk_parser(res.content)

        city, exp, degree = soups.find(
            'p', class_='msg ltype').text.strip().replace(u' ', '').split('|')[
                            :3]

        if u'招' in degree:
            degree = ''
        position_desc_lst = soups.find(
            'div', class_='bmsg job_msg inbox').find_all('p', recursive=False)
        position_desc = ''.join(
            map(lambda x: x.text.strip(), position_desc_lst)).replace('\n', ' ')

        return city, exp, degree, position_desc


def main():
    key = 'HR_USER_ID_COMPANY_NAME'
    cp = CompanyPosition()
    cp.logger.info('start company position search. redis_queue: {}'.format(key))
    while True:
        try:
            _, task = redis_client.blpop(key)
            user_id, company_name = task.split('_')
            cp.logger.info('start_task： {} | {}'.format(user_id, company_name))
            zhi_lian_lst = cp.get_zhi_lian_position_list(company_name,
                                                         res_lst=[])
            five_one_lst = cp.get_five_one_position_list(company_name,
                                                         res_lst=[])
            res_lst = zhi_lian_lst + five_one_lst

            res = json.dumps(res_lst, ensure_ascii=False)
            # print json.dumps(res_lst, ensure_ascii=False, indent=4)

            redis_client.set(task, res)
            redis_client.expire(task, 86400)
            cp.logger.info(
                'match position : ZHI_LIAN {}, FIVE_ONE {}, TOTAL '
                '{}'.format(len(zhi_lian_lst), len(five_one_lst), len(res_lst)))
        except Exception as e:
            cp.logger.exception(e)


if __name__ == '__main__':
    # main()
    gevent.joinall([
        gevent.spawn(main, ) for i in xrange(settings.COROUTINE_NUM)
    ])


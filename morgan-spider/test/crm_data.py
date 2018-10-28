#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/16 0016 9:14
# @Author  : huangyee
# @Email   : 1173842904@qq.com
# @File    : crm_data.py
# @Software: PyCharm
import sys
import os
import logging.handlers
import json

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
current_file_name = os.path.basename(__file__)
logger = logging.getLogger()

sql = '''
inserst into hunt_mapping(mfName,mfCode,type,source,createBy,createTime)values('%s','%s','%s','%s','python',now())
'''


def read_file(path):
    if not path:
        return
    data = {}

    file = open(path)
    try:
        for line in file.readlines():
            array = line.split('=')
            data[array[0]] = eval(array[1].strip('\n'))
    finally:
        file.close()
    return data


def process_job():
    source = 'ZHI_LIAN'
    type = 'job'
    job_content = read_file('')
    job_json = json.loads(job_content, encoding='utf8')
    for first in job_json:
        print sql % (first.get('name'), first.get('code'), type, source)
        for second in first.get('val'):
            print sql % (second.get('name'), second.get('code'), type, source)
            for third in second.get('val'):
                print sql % (third.get('name'), third.get('code'), type, source)


update_sql = '''
    UPDATE hunt_mapping SET currentCode='%s',currentName='%s',parentCode='%s',parentName='%s' WHERE id=%s
    '''


def load_zhilian_city(data):
    file = open('/data/zhilian_city.txt')
    city_array = data.get('arrCity')
    dis_array = data.get('arrDistrict')
    repeat = {}
    try:
        for line in file.readlines():
            array = line.strip('\n').split('=')
            flg = False
            # for arr in city_array:
            #     if array[1] == arr[2]:
            #         # flg = True
            #         # print 'city 找到映射了 %s == %s' % (array[1], arr[0])
            #         print update_sql % (arr[0], arr[2], arr[1], '', array[0])
            #         # repeat[array[:4][0]] = {'name': array[1], 'code': arr[0]}
            # print '找不到映射 %s' % array[1]
            # if not flg:
            #     # parent_code = str(array[1]).
            for dis in dis_array:
                if str(dis[2]) == (array[1] + '区') and dis[1] == '765':
                    flg = True
                    # print 'dis 找到映射了 %s == %s' % (array[1], dis[0])
                    print update_sql % (dis[0], dis[2], dis[1], '', array[0])

        # if not flg:
        #     print '完了啊，找不到映射 %s ' % array[1]

    finally:
        file.close()


def process_city():
    source = 'ZHI_LIAN'
    type = 'city'
    city_content = read_file('')
    city_json = json.loads(city_content, encoding='utf8')
    for first in city_json:
        print sql % (first.get('name'), first.get('code'), type, source)
        for second in first.get('city'):
            print sql % (second.get('name'), second.get('code'), type, source)


def process_job(data):
    job_sql = '''
    UPDATE dim_function_mapping SET origin_func_code='%s',parentName='%s',parentCode='%s' WHERE origin_func_name='%s'
    '''
    first_job = data.get('arrJobtype')
    second_job = data.get('arrSubjobtype')
    file = open('/data/zhilian_job.txt')
    try:
        for line in file.readlines():
            array = line.strip('\n').split('=')
            flg = False
            for f in first_job:
                if array[1] == f[2]:
                    # print 'first find: %s== %s' % (array[1], f[0])
                    print job_sql % (f[0], '', f[1], array[1])
                    flg = True
            if not flg:
                for f in second_job:
                    if (array[1] == f[2]):
                        # print 'second find: %s== %s' % (array[1], f[0])
                        print job_sql % (f[0], '', f[1], array[1])
                        flg = True
            # if not flg:
            #     print '沒找到呀 %s ' % array[1]


    finally:
        file.close()


def process_51city(data):
    city_array = data.get('ctJobareaAss')
    file = open('/data/511.txt')
    try:
        for line in file.readlines():
            array = line.strip('\n').split('=')
            flg = False
            for c in city_array:
                if array[1] == c.get('value'):
                    # print 'city 找到了 %s--->>%s == %s ' % (array[1], c.get('value'), c.get('code'))
                    flg = True
                    print update_sql % (c.get('code'), c.get('value'), '', '', array[0])

                # if not flg:
                #     ss = str(c.get('value')).split('-')
                #     if array[1] in ss[1]:
                #         print 'dis 找到了 %s--->>%s == %s ' % (array[1], c.get('value'), c.get('code'))
                #         flg = True
            # if not flg:
            #     print '没有找到 %s ' % array[1]

    finally:
        file.close()


def process_51_job():
    sql = '''
    
    update dim_function_mapping set origin_func_code='%s',parentName='%s',parentCode='%s' where origin_func_name='%s'
    '''
    file1 = open('/data/51job.txt')
    try:
        content = file1.read()
        array1 = content.decode('utf8').split('$')
        for a in array1:
            array2 = a.split('|')
            # print '一级职能 %s ' % array2[0]
            parentarray = array2[0].split('@')
            print sql % (parentarray[1],'','',parentarray[0])
            for b in array2[1:]:
                array3 = b.split('@')
                # print '三级职能：%s = %s parentname=%s,parentcode=%s' % (
                # array3[0], array3[1], parentarray[0], parentarray[1])
                print sql % (array3[1], parentarray[0], parentarray[1], array3[0])

    finally:
        file1.close()

    file = open('/data/51job1.txt')
    pass


def process():
    # process_job()
    # process_city()
    # load_zhilian_city(data)
    # process_51city(data)
    process_51_job()
    pass


if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', 'crm_data'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)
    process()
    pass

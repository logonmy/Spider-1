#!coding:utf8
import random
import sys

sys.path.append('../common')
import utils
import common_settings
import uuid
import json
import time
import datetime
import MySQLdb
from DBUtils.PersistentDB import PersistentDB

# 从settings.py中加载配置文件
# from conf import settings

# 从consul k-v中加载配置文件
# http://172.16.25.36:8500/ui/dc1/kv/no_scrapy/resume_zhaopingou

from mf_utils.common import dict2obj
from mf_utils.load_settings import LoadSettingsFromConsul

settings = dict2obj(LoadSettingsFromConsul.get_settings(
    key='no_scrapy/resume_zhaopingou', host='172.16.25.36'), change_dict=False)

city_dict = settings.CITY_DICT
use_static_proxy_list = settings.USE_STATIC_PROXY_LIST
city_order = city_dict.keys()


def create_task_from_mysql(use_keyword='0'):
    logger = utils.get_logger()
    logger.info('start create task from mysql.')
    mysql_pool = PersistentDB(
        MySQLdb,
        host=common_settings.MYSQL_HOST,
        user=common_settings.MYSQL_USER,
        passwd=common_settings.MYSQL_PASSWD,
        db='spider',
        port=common_settings.MYSQL_PORT,
        charset='utf8'
    )
    conn = mysql_pool.connection()
    cur = conn.cursor()
    # city_number = cur.execute('select code from city_entrence where source="ZHAO_PIN_GOU" and valid=1')
    # cities = cur.fetchall()
    function_number = cur.execute('select * from function_entrence where source="ZHAO_PIN_GOU" and valid=1')
    functions = cur.fetchall()
    # logger.info('the number of city and functions is:%s, %s' % (city_number, function_number))
    # if not city_number or not function_number:
    #     return

    logger.info('the number of  functions is:%s, %s' % (len(city_order), function_number))
    if not function_number:
        return

    add_task_url = common_settings.TASK_URL + common_settings.CREATE_TASK_PATH
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8', }
    today = datetime.datetime.today()
    next_datetime = datetime.datetime(today.year, today.month, today.day, 0, 0, 0) + datetime.timedelta(days=1)
    deadline = int(time.mktime(time.strptime(next_datetime.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))) * 1000
    # use_keyword = '0' if datetime.datetime.now().hour<12 else '1'

    # city_result = []
    # if cities:
    #     cities = [i[0] for i in cities]
    #     for i in city_order:
    #         if i in cities:
    #             city_result.append(i)
    #             cities.remove(i)
    #     city_result = city_result + cities
    random.shuffle(city_order)
    for city in city_order:
        for function in functions:
            add_task_data = {
                "callSystemID": "morgan-zhaopingou-resume-1",
                "source": 'ZHAO_PIN_GOU',
                "traceID": str(uuid.uuid1()),
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps(
                    {"fenleiName": function[4], "pFenLeiName": function[1], "positionName": function[7],
                     "hopeAdressStr": city, "fId": int(function[5]), "pFId": int(function[2]), "pId": int(function[8]),
                     "id": int(function[11]), 'use_keyword': use_keyword}, ensure_ascii=False),
                "taskType": "RESUME_FETCH",
                "deadline": deadline
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post',
                                             data=add_task_data)
    logger.info('done.')


def create_task_for_meituan():
    logger = utils.get_logger()
    logger.info('start create task for meituan.')

    logger = utils.get_logger()
    logger.info('start create task from mysql.')
    mysql_pool = PersistentDB(
        MySQLdb,
        host=common_settings.MYSQL_HOST,
        user=common_settings.MYSQL_USER,
        passwd=common_settings.MYSQL_PASSWD,
        db=common_settings.MYSQL_DB,
        port=common_settings.MYSQL_PORT,
        charset='utf8'
    )
    conn = mysql_pool.connection()
    cur = conn.cursor()
    function_number = cur.execute(
        'select * from function_entrence where source="ZHAO_PIN_GOU" '
        'and valid=1 and thirdFunctionCode in '
        '(262, 265, 261, 257, 256, 252, 253, 250, 254, 370, 372, 371, 369)')
    functions = cur.fetchall()
    logger.info('the number of functions is: %s' % (function_number))
    if not function_number:
        return

    add_task_url = common_settings.TASK_URL + common_settings.CREATE_TASK_PATH
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8', }
    deadline = datetime.datetime.now() + datetime.timedelta(days=1)
    deadline = int(time.mktime(deadline.timetuple())) * 1000

    city_dict = {
        u'石家庄': '7',
        u'邢台': '11',
        u'衡水': '17',
        u'保定': '12',
        u'沧州': '15',
        u'扬州': '66',
    }

    for city in [u'石家庄', u'邢台', u'衡水', u'保定', u'沧州']:
        for function in functions:
            add_task_data = {
                "callSystemID": "morgan-zhaopingou-resume-1",
                "source": 'ZHAO_PIN_GOU',
                "traceID": str(uuid.uuid1()),
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps(
                    {"fenleiName": function[4], "pFenLeiName": function[1], "positionName": function[7],
                     "hopeAdressStr": city_dict[city], "fId": int(function[5]), "pFId": int(function[2]),
                     "pId": int(function[8]), "id": int(function[11])}, ensure_ascii=False),
                "taskType": "RESUME_FETCH",
                "deadline": deadline
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post',
                                             data=add_task_data)


if __name__ == '__main__':
    utils.set_setting({"PROJECT_NAME": 'resume_zhaopingou_create_task', })
    # create_task_for_meituan()
    create_task_from_mysql()

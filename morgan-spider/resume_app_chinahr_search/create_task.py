#!coding:utf8
import sys

sys.path.append('../common')
import utils
from lxml import etree
import common_settings
import uuid
import json
import time
import datetime
import requests
import settings
import traceback
import MySQLdb
from DBUtils.PersistentDB import PersistentDB

city_order = [
    u'北京',
    u'上海',
    u'武汉',
    u'成都',
    u'天津',
    u'广州',
    u'深圳',
    u'石家庄',
    u'扬州',
    u'邢台',
    u'衡水',
    u'保定',
    u'沧州',
    u'镇江',
    u'淮安',
    u'泰州',
    u'南京',
    u'大连',
    u'佛山',
    u'沈阳',
    u'杭州',
    u'青岛',
    u'重庆',
    u'济南',
    u'西安',
    u'中山',
    u'厦门',
    u'东莞',
    u'合肥'
]


def create_task_from_mysql():
    logger = utils.get_logger()
    logger.info('start create task from mysql.')
    mysql_pool = PersistentDB(
        MySQLdb, 
        host=common_settings.MYSQL_HOST, 
        user=common_settings.MYSQL_USER,
        passwd=common_settings.MYSQL_PASSWD, 
        db=common_settings.MYSQL_DOWNLOAD_DB,
        port=common_settings.MYSQL_PORT, 
        charset='utf8'
    )
    conn = mysql_pool.connection()
    cur = conn.cursor()
    city_number = cur.execute('select cityName from city_entrence where source="CH_HR" and valid=1 and resourceType="%s"' % common_settings.TASK_TYPE)
    cities = cur.fetchall()
    function_number = cur.execute('select thirdFunction from function_entrence where source="CH_HR" and valid=1 and resourceType="%s"' % common_settings.TASK_TYPE)
    functions = cur.fetchall()
    logger.info('the number of city and functions is:%s, %s' % (city_number, function_number))
    if not city_number or not function_number:
        return
    add_task_url = common_settings.TASK_URL +common_settings.CREATE_TASK_PATH
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',}
    today = datetime.datetime.today()
    next_datetime = datetime.datetime(today.year, today.month, today.day, 0, 0, 0) + datetime.timedelta(days=1)
    deadline = int(time.mktime(time.strptime(next_datetime.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))) * 1000

    city_result = []
    if cities:
        cities = [i[0] for i in cities]
        for i in city_order:
            if i in cities:
                city_result.append(i)
                cities.remove(i)
        city_result = city_result + cities
    for city in city_result:
        for function in functions:
            add_task_data = {
                "callSystemID": common_settings.CALLSYSTEMID, 
                "source": 'CH_HR', 
                "traceID": str(uuid.uuid1()), 
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps({"zone": city, "keyword": function[0], "degree": 0, "refreshTime": 1, "page_now": 1}, ensure_ascii=False), 
                "taskType": common_settings.TASK_TYPE,
                "deadline": deadline
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
    logger.info('done.')

def create_task_for_meituan():
    logger = utils.get_logger()
    logger.info('start create task for meituan.')
    add_task_url = common_settings.TASK_URL +common_settings.CREATE_TASK_PATH
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',}
    deadline = datetime.datetime.now() + datetime.timedelta(days=1)
    deadline = int(time.mktime(deadline.timetuple())) * 1000
    # for func in [u'客服/技术支持', u'售前/售后服务', u'网络/在线客服', u'客服经理/主管', u'客户关系/投诉协调人员', u'客服咨询热线/呼叫中心人员', u'vip专员', u'售前/售后技术支持', u'其他客服/技术支持职位']:
    #     add_task_data = {
    #         "callSystemID": common_settings.CALLSYSTEMID, 
    #         "source": 'CH_HR', 
    #         "traceID": str(uuid.uuid1()), 
    #         # "executeParam": json.loads(i.strip()), 
    #         "executeParam": json.dumps({"zone": u'石家庄', "keyword": func, "degree": 0, "refreshTime": 1, "page_now": 1}, ensure_ascii=False), 
    #         "taskType": common_settings.TASK_TYPE,
    #         "deadline": deadline
    #     }
    #     add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)

    for city in [u'石家庄', u'邢台', u'衡水', u'保定', u'沧州']:
        for function in [u'行政', u'行政经理/主管/办公室主任', u'行政专员/助理', u'文员/文秘/秘书/助理', u'内勤/后勤/总务', u'前台/总机/接待', u'商务/行政司机', u'其他行政职位', u'客服/技术支持', u'售前/售后服务', u'网络/在线客服', u'客服经理/主管', u'客户关系/投诉协调人员', u'客服咨询热线/呼叫中心人员', u'vip专员', u'售前/售后技术支持', u'其他客服/技术支持职位']:
            add_task_data = {
                "callSystemID": common_settings.CALLSYSTEMID, 
                "source": 'CH_HR', 
                "traceID": str(uuid.uuid1()), 
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps({"zone": city, "keyword": function, "degree": 0, "refreshTime": 1, "page_now": 1}, ensure_ascii=False), 
                "taskType": common_settings.TASK_TYPE,
                "deadline": deadline
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)

if __name__ == '__main__':
    project_settings = settings.project_settings
    project_settings['PROJECT_NAME'] = 'resume_chinahr_create_task'
    utils.set_setting(project_settings)
    # create_task_for_meituan()
    create_task_from_mysql()

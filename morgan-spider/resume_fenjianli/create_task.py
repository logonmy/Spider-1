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
import traceback
import MySQLdb
from DBUtils.PersistentDB import PersistentDB

city_order = [u'北京', u'上海', u'广州', u'深圳', u'天津', u'武汉', u'成都']

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
    city_number = cur.execute('select * from city_entrence where source="RESUME_FEN" and valid=1')
    cities = cur.fetchall()
    function_number = cur.execute('select * from function_entrence where source="RESUME_FEN" and valid=1')
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
        city_dict = {i[1]: i for i in cities}
        for i in city_order:
            if i in city_dict:
                city_result.append(city_dict[i])
                city_dict.pop(i)
        city_result = city_result + city_dict.values()

    for city in city_result:
        for function in functions:
            add_task_data = {
                "callSystemID": "morgan-fenjianli-resume-1", 
                "source": 'RESUME_FEN', 
                "traceID": str(uuid.uuid1()), 
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps({'model_name': 'zhilian', 'job_code': function[8], 'job_name': function[7], 'area_code': city[6], 'area_name': city[1]}, ensure_ascii=False), 
                "taskType": "RESUME_FETCH",
                "deadline": deadline
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
            add_task_data = {
                "callSystemID": "morgan-fenjianli-resume-1", 
                "source": 'RESUME_FEN', 
                "traceID": str(uuid.uuid1()), 
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps({'model_name': 'liepin', 'job_code': function[8], 'job_name': function[7], 'area_code': city[6], 'area_name': city[1]}, ensure_ascii=False), 
                "taskType": "RESUME_FETCH",
                "deadline": deadline
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
    logger.info('done.')

if __name__ == '__main__':
    utils.set_setting({"PROJECT_NAME": 'resume_fenjianli_create_task',})
    create_task_from_mysql()

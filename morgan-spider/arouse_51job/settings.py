#!coding:utf8

# version: python2.7
# author: wzs
# time: 2017.4.25

project_settings = {
    'MYSQL_HOST': 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com',
    'MYSQL_PORT': 3306,
    'MYSQL_USER': 'spider_admin',
    'MYSQL_PASSWD': 'n4UZknFH6F',
    'MYSQL_DB': 'spider',
    'KAFKA_HOSTS': 'kafka-data.mofanghr.service:9092',
    'KAFKA_TOPIC': 'morgan-data-raw',
    'REDIS_IP': '172.16.25.36',
    'REDIS_PORT': 6379,
    'PROJECT_NAME': 'morgan-51job-arouse',

    # GET_TASKS_QUEUE_MAX_SIZE = 100
    # RETURN_TASKS_QUEUE_MAX_SIZE = 100

    "TASK_URL": 'http://172.16.25.35:7001',
    "GET_TASK_PATH": '/task/search?',
    "CREATE_TASK_PATH": '/task/add?',
    "RETURN_TASK_PATH": '/task/result/add?',
    "CALLSYSTEMID": 'morgan-51job-arouse-1',
    "TASK_TYPE": 'RESUME_FETCH',
    "SOURCE": 'FIVE_ONE',
    'ACCOUNT_URL': 'http://172.16.25.35:9000/acc/getCookie.json?source=%s&useType=%s',

    "DOWNLOAD_THREAD_NUMBER": 1,
}


INVALID_ACCOUNT_URL = 'http://172.16.25.35:9000/acc/invalidCookie.json?'

AOURSE_DB_HOST = 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com'
AOURSE_DB_USER = 'spider_admin'
AOURSE_DB_PASS = 'n4UZknFH6F'
AOURSE_DB_NAME = 'spider_search'

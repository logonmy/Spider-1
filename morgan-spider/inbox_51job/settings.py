#!coding:utf8

# version: python2.7
# author: wzs
# time: 2017.4.25

project_settings = {
'MYSQL_HOST' : '172.16.25.1',
'MYSQL_PORT' : 3306,
'MYSQL_USER':'bi_admin',
'MYSQL_PASSWD ': "bi_admin#@1mofanghr",
'MYSQL_DB' : 'spider',

'KAFKA_HOSTS' : '172.16.25.35:19092',
'KAFKA_TOPIC' : 'morgan-data-raw',

'REDIS_IP' : '127.0.0.1',
'REDIS_PORT' : 6379,

'PROJECT_NAME' : 'morgan-51job-spider-inbox',

# GET_TASKS_QUEUE_MAX_SIZE = 100
# RETURN_TASKS_QUEUE_MAX_SIZE = 100

"TASK_URL": 'http://172.16.25.35:7001',
"GET_TASK_PATH": '/task/search?',
"CREATE_TASK_PATH": '/task/add?',
"RETURN_TASK_PATH": '/task/result/add?',
"CALLSYSTEMID": 'morgan-51job-inbox-1',
"TASK_TYPE": 'RESUME_INBOX',
"SOURCE": 'FIVE_ONE',


"DOWNLOAD_THREAD_NUMBER": 1,
}

account_list = ('shhy8127', 'shhy8127', 'shhy8127', 'shhy8127',)

INVALID_ACCOUNT_URL = 'http://172.16.25.35:9000/acc/invalidCookie.json?'
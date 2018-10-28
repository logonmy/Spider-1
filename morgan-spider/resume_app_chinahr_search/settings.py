#!coding:utf8
import random

project_settings = {
"PROJECT_NAME": 'resume_app_chinahr_search',
"CALLSYSTEMID": 'morgan-chinahr-resume-1',
"TASK_TYPE": 'RESUME_FETCH',
# 'RESOURCE_TYPE': 'RESUME_SEARCH',
"SOURCE": 'CH_HR',
'PROXY_PATH': 'test',
"DOWNLOAD_THREAD_NUMBER": 5,
"DOWNLOAD_RETRY_TIMES": 3,
'MNS_SAVE_RETRY_TIME': 20,
# 'MNS_QUEUE' : 'morgan-queue-test-resume-raw',
'MNS_QUEUE': 'morgan-queue-resume-raw',
# "MYSQL_HOST": "172.16.25.1",
"MYSQL_PORT": 3306,
# "MYSQL_USER": "bi_admin",
# "MYSQL_PASSWD": "bi_admin#@1mofanghr",
"MYSQL_SEARCH_DB": "spider_search",
"MYSQL_DB": "spider_search",
"MYSQL_DOWNLOAD_DB": "spider",
'MYSQL_MANAGER_DB': 'morgan_manager',
'NUMBERS_ERVERYDAY': 100000,
'RESUME_DELAY_DAYS': 1,
'SET_FORBIDDEN_URL': 'http://172.16.25.41:8002/acc/updateUser.json?userName=%s&password=%s&source=%s&valid=0',
}

AWAKE_URL = 'http://morgan-pick.mofanghr.com/awake/force.json'
STATIC_PROXIES=[
['H60TQG2T4800092D', '2A5A804B014B4579'],
# ['HKF9723461EF3DBD', '0074AD76A609C9E1'],
]
def get_proxy():
    p=random.choice(STATIC_PROXIES)
    return {'http': 'http://%s:%s@proxy.abuyun.com:9020' % (p[0], p[1]), 'https': 'http://%s:%s@proxy.abuyun.com:9020' % (p[0], p[1])}

# STATIC_PROXIES=[
# ['47.95.32.105', '3128'],
# ['47.94.46.238', '3128'],
# ['47.93.118.95', '3128'],
# ['47.94.42.170', '3128'],
# ['47.93.121.87', '3128'],
# ['47.93.125.9', '3128'],
# ['47.94.43.188', '3128'],
# ['47.93.123.77', '3128'],
# ['47.93.116.245', '3128'],
# ['47.93.115.141', '3128'],
# ]
# def get_proxy():
#     global STATIC_PROXIES
#     p=random.choice(STATIC_PROXIES)
#     return {'http': 'http://%s:%s' % (p[0], p[1]), 'https': 'http://%s:%s' % (p[0], p[1])}

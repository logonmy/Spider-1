#!coding:utf8
import random

project_settings = {
    "PROJECT_NAME": 'resume_rencaia',

    "CALLSYSTEMID": 'morgan-rencaia-resume-1',
    "TASK_TYPE": 'RESUME_FETCH',
    'RESOURCE_TYPE': 'RESUME_SEARCH',
    "SOURCE": 'REN_CAI',
    'PROXY_PATH': 'test',

    "SEARCH_THREAD_NUMBER": 2,
    "DOWNLOAD_RETRY_TIME": 3,
    'MNS_QUEUE': 'morgan-queue-resume-raw',
    # 'MNS_QUEUE' : 'morgan-queue-test-resume-raw',
    # "PROXY_URL" : 'http://172.16.25.35:8003/proxy/one.json?systemId=morgan-boss-jd-1',
    "MYSQL_SEARCH_DB": "spider_search",
    "MYSQL_DB": "spider_search",
    "MYSQL_DOWNLOAD_DB": "spider",

    'QUEUE_MAX_SIZE': 30,
    'MNS_SAVE_RETRY_TIME': 5,
    'NUMBERS_ERVERYDAY': 6000,
    'USE_PROXY': True,
    # 'ACCOUNT_URL': 'http://10.0.4.223:8002/acc/getCookie.json?source=%s&useType=%s',
    # 'SET_INVALID_URL': 'http://10.0.4.223:8002/acc/invalidCookie.json?userName=%s&password=%s',
    'UPDATE_DOWNLOAD_SCORE': 'http://172.16.25.41:8002/acc/uploadCookie.json',
    'SET_FORBIDDEN_URL': 'http://172.16.25.41:8002/acc/updateUser.json?userName=%s&password=%s&source=REN_CAI&valid=0',
}

STATIC_PROXIES = [
    ['47.95.32.105', '3128'],
    ['47.94.46.238', '3128'],
    ['47.93.118.95', '3128'],
    ['47.94.42.170', '3128'],
    ['47.93.121.87', '3128'],
    ['47.93.125.9', '3128'],
    ['47.94.43.188', '3128'],
    ['47.93.123.77', '3128'],
    ['47.93.116.245', '3128'],
    ['47.93.115.141', '3128'],
]


def get_proxy():
    # global STATIC_PROXIES
    # p=random.choice(STATIC_PROXIES)
    # return {'http': 'http://%s:%s' % (p[0], p[1]), 'https': 'http://%s:%s' % (p[0], p[1])}
    return {
        'http': 'http://H4U23WF0BK7PY0OD:B8CD32E44A22A8F9@http-dyn.abuyun.com:9020',
        'https': 'https://H4U23WF0BK7PY0OD:B8CD32E44A22A8F9@http-dyn.abuyun.com:9020', }

#!coding:utf8
import random

project_settings = {
    "PROJECT_NAME": 'resume_zhaopingou',

    "CALLSYSTEMID": 'morgan-zhaopingou-resume-1',
    "TASK_TYPE": 'RESUME_FETCH',
    'RESOURCE_TYPE': 'RESUME_SEARCH',
    "SOURCE": 'ZHAO_PIN_GOU',
    'PROXY_PATH': 'test',

    "SEARCH_THREAD_NUMBER": 14,
    "DOWNLOAD_THREAD_NUMBER": 5,
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
}

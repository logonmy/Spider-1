#!coding:utf8

# version: python2.7
# author: wzs
# time: 2017.4.25

project_settings = {

    'REDIS_IP': '172.16.25.36',
    'REDIS_PORT': 6379,

    'PROJECT_NAME': 'morgan-51job-spider-jd',

    "CALLSYSTEMID": 'morgan-51job-jd-1',
    "TASK_TYPE": 'JD_FETCH',
    "SOURCE": 'FIVE_ONE',

    "DOWNLOAD_THREAD_NUMBER": 4,
    "useAby": True,
    "aby": {
        'http': 'http://H4U23WF0BK7PY0OD:B8CD32E44A22A8F9@proxy.abuyun.com:9020',
        'https': 'https://H4U23WF0BK7PY0OD:B8CD32E44A22A8F9@proxy.abuyun.com:9020'
    }
}

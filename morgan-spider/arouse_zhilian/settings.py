#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25

# sys.path.append("..")

project_settings = {

    "KAFKA_HOSTS": '172.16.25.35:19092',
    "KAFKA_TOPIC": 'morgan-data-raw',
    "PROJECT_NAME": 'arouse-zhilian',
    "CALLSYSTEMID": 'morgan-zhilian-arouse-1',
    "TASK_TYPE": 'RESUME_FETCH',
    "SOURCE": 'ZHI_LIAN',
    'invalidUrl': 'http://172.16.25.35:8002/acc/invalidCookie.json?',
    'loadCookieUrl': 'http://172.16.25.35:8002/acc/getCookie.json?source=ZHI_LIAN&useType=RESUME_FETCH&all=true',
    "DOWNLOAD_THREAD_NUMBER": 1,

}

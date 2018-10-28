#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25

# sys.path.append("..")

project_settings = {
    # "KAFKA_HOSTS": '172.16.25.35:19092',
    # "KAFKA_TOPIC": 'morgan-jd-raw',
    "PROJECT_NAME": 'morgan-jd-ganji',
    "CALLSYSTEMID": 'morgan-jd-ganji-1',
    "TASK_TYPE": 'JD_FETCH',
    "SOURCE": 'GJ_HR',
    "DOWNLOAD_THREAD_NUMBER": 5,
    "PROXY_URL": 'http://172.16.25.41:8003/proxy/one.json?systemId=jd-ganji',
    # u 1表示搜索最近三天,2表示5天以内，3表示15天以内，4表示一个月内
    "U": 1,

}

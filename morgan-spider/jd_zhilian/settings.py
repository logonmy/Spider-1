#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25

# sys.path.append("..")

project_settings = {
    # "KAFKA_HOSTS": '172.16.25.35:19092',
    # "KAFKA_TOPIC": 'morgan-jd-raw',
    "PROJECT_NAME": 'morgan-jd-zhilian',
    "CALLSYSTEMID": 'morgan-jd-zhilian-1',
    "TASK_TYPE": 'JD_FETCH',
    "SOURCE": 'ZHI_LIAN',
    "DOWNLOAD_THREAD_NUMBER": 5,
    # pd=3,表示搜索最近三天，pd=1，表示搜索当天,pd=7 表示最近一周，pd=30 表示最近一个月
    "PD": 3,
    "useProxy": False,
    # 是否使用阿布云代理
    "useAby": True,
    "aby": {'http': 'http://HKF9723461EF3DBD:0074AD76A609C9E1@proxy.abuyun.com:9020',
            'https': 'https://HKF9723461EF3DBD:0074AD76A609C9E1@proxy.abuyun.com:9020'},
}

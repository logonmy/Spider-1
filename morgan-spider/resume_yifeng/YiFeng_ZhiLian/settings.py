#!coding:utf8
import random
CALLSYSTEMID = 'YI_FENG_ZHI_LIAN'
MYSQL_HOST = '172.16.25.1'
MYSQL_PORT = 3306
MYSQL_USER = 'bi_admin'
MYSQL_PASSWD = 'bi_admin#@1mofanghr'
MYSQL_DB = 'spider_search'

KAFKA_HOSTS = '172.16.25.35:19092'
KAFKA_TOPIC = 'morgan-resume-raw'

# MYSQL_HOST = 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com'
# MYSQL_PORT = 3306
# MYSQL_USER = 'spider_admin'
# MYSQL_PASSWD = 'n4UZknFH6F'
# MYSQL_DB = 'spider'

# KAFKA_HOSTS = 'kafka-data.mofanghr.service:9092'
# KAFKA_TOPIC = 'morgan-resume-raw'

# REDIS_HOST = '172.16.25.36'



STATIC_PROXIES=[
#['H463CA16CA05YUUD:952FCA274D3C9DB2@proxy.abuyun.com', '9020'],
['H1R88SO2032T1UZD:166C3BC57B0BD0CE@proxy.abuyun.com', '9020'],
#['HMCKW8ZGDYQXQZ1D:55A4BB91448F65DC@proxy.abuyun.com', '9020'],
]

MIN_COIN = -100000

def get_random_proxy():
    global STATIC_PROXIES
    random_proxy = random.choice(STATIC_PROXIES)
    return {'http': 'http://%s:%s' % (random_proxy[0], random_proxy[1]), 'https': 'http://%s:%s' % (random_proxy[0], random_proxy[1])}


# -*-coding: utf-8-*-

from gevent import monkey

monkey.patch_all()
import sys
import time
import MySQLdb

reload(sys)
sys.setdefaultencoding('utf-8')

sql = 'select * from spider.redis_awake_final_temp where id > %d and id <= %d'
count_sql = 'select COUNT(1) from spider.redis_awake_final_temp'
pagesize = 100000
connect = MySQLdb.connect(host='172.16.25.1', user='bi_admin', passwd='bi_admin#@1mofanghr', port=3306, charset='utf8')
file_object = open('redis_protocol_data_1.txt', 'w')


def worker(count=None):
    start = time.time()
    cur = connect.cursor()
    sql_ = sql % ((count - 1) * pagesize, count * pagesize)
    cur.execute(sql_)
    results = cur.fetchall()
    for (id, key1, key2, mobiles) in results:
        file_object.write('*4\r\n$4\r\nHSET\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n$%d\r\n%s\r\n' % (
            len(key1.encode('utf-8')), key1.encode('utf-8'), len(key2.encode('utf-8')), key2.encode('utf-8'),
            len(mobiles.encode('utf-8')), mobiles.encode('utf-8')))
    cur.close()
    print sql_, time.time() - start, 's'


if __name__ == '__main__':
    start = time.time()
    cur = connect.cursor()
    cur.execute(count_sql)
    (record_num,) = cur.fetchone()
    # record_num = 10000000
    print '记录数%s' % record_num
    i = 1
    try:
        # worker1(1)
        while pagesize * (i - 1) < record_num:
            worker(i)
            i = i + 1
    finally:
        file_object.close()
        connect.close()
        print 'all finish', time.time() - start, 's'

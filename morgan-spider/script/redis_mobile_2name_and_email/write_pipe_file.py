# -*-coding: utf-8-*-

from gevent import monkey

monkey.patch_all()
import sys
import time
import MySQLdb

reload(sys)
sys.setdefaultencoding('utf-8')

sql = 'SELECT * FROM spider.redis_mobile2name_and_email_final WHERE id > %d AND id <= %d and name_and_email is not null'
count_sql = 'SELECT COUNT(1) FROM spider.redis_mobile2name_and_email_final'
pagesize = 100000
connect = MySQLdb.connect(host='172.16.25.1', user='bi_admin', passwd='bi_admin#@1mofanghr', port=3306, charset='utf8')
file_object = open('redis_protocol_data_1.txt', 'w')


def worker(count=None):
    start = time.time()
    cur = connect.cursor()
    sql_ = sql % ((count - 1) * pagesize, count * pagesize)
    cur.execute(sql_)
    results = cur.fetchall()
    for (id, mobile, name_and_email) in results:
        file_object.write('*3\r\n'
                          '$3\r\n'
                          'SET\r\n'
                          '$%d\r\n'
                          '%s\r\n'
                          '$%d\r\n'
                          '%s\r\n' % (
                              len(mobile.encode('utf-8')), mobile.encode('utf-8'), len(name_and_email.encode('utf-8')),
                              name_and_email.encode('utf-8')))
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

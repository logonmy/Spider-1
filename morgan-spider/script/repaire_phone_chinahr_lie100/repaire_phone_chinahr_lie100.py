#!coding:utf8

import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import datetime
import logging
import traceback
from logging.handlers import RotatingFileHandler

logger = None
def get_logger():
    global logger
    if not logger:
        logger = logging.getLogger('')
        formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(threadName)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler()

        rotating_handler = logging.handlers.RotatingFileHandler(
            '%s/%s.log' % ('.', 'repaire_phone_chinahr_lie100'), 'a', 50 * 1024 * 1024, 100, None, 0)

        stream_handler.setFormatter(formatter)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(rotating_handler)
        logger.setLevel(logging.INFO)
    return logger

def main():

    logger = get_logger()
    logger.info('==========================================\nstart main!!!')

    start_datetime = datetime.date(2017, 5,9)
    today_datetime = datetime.date(2017, 6, 10)
    MYSQL_HOST = 'rm-2ze15h84ax219xf08.mysql.rds.aliyuncs.com'
    MYSQL_PORT = 3306
    MYSQL_USER = 'spider_admin'
    MYSQL_PASSWD = 'n4UZknFH6F'
    MYSQL_DB = 'spider'


    mysql_pool = PersistentDB(MySQLdb, 
        host=MYSQL_HOST, 
        user=MYSQL_USER,
        passwd=MYSQL_PASSWD, 
        db=MYSQL_DB,
        port=MYSQL_PORT, 
        charset='utf8'
    )
    mysql_conn = mysql_pool.connection()
    mysql_cursor = mysql_conn.cursor()
    while start_datetime<today_datetime:
        logger.info('-----------------------------------------------start deal with:'+str(start_datetime))
        sql = """select externalId,mobile,source from resume_parsed where
                     rdCreateTime>'%s'
                       and rdCreateTime<'%s'
                     and source in('LIE_100','CH_HR');""" % (str(start_datetime), str(start_datetime + datetime.timedelta(days=1)))
        mobile_number= mysql_cursor.execute(sql)
        logger.info('mobile_number is:'+str(mobile_number))
        if not mobile_number:
            logger.info('did get any mobile continue next day')
            start_datetime = start_datetime + datetime.timedelta(days=1)
            continue
        mobiles = mysql_cursor.fetchall()
        china_hr_sql_list = []
        youben_hr_sql_list = []
        for mobile in mobiles:
            if mobile[2] == 'CH_HR':
                resume_id = mobile[0]
                if len(mobile[0].split('_')[-1]) ==1:
                    resume_id = '_'.join(mobile[0].split('_')[:-1])
                china_hr_sql_list.append("update resume_download  set mobile='%s' where resume_id='%s';" % (mobile[1], resume_id))
                # mysql_cursor.execute("update resume_download  set mobile='%s' where resume_id='%s';" % (mobile[1], resume_id))
                # mysql_conn.commit()
            elif mobile[2] =='LIE_100':
            	youben_hr_sql_list.append("update youben_buy_record set mobile='%s' where resumeId='%s';" % (mobile[1], mobile[0]))
                # mysql_cursor.execute("update youben_buy_record set mobile='%s' where resumeId='%s';" % (mobile[1], mobile[0]))
                # mysql_conn.commit()
            else:
                logger.info('get error mobile 2:'+str(mobile))
                continue

        count= 0 
        for i in china_hr_sql_list:
        	mysql_cursor.execute(i)
        	count+=1
        	if not (count % 30):
        		mysql_conn.commit()
        mysql_conn.commit()

        count= 0 
        for i in youben_hr_sql_list:
        	mysql_cursor.execute(i)
        	count+=1
        	if not (count % 30):
        		mysql_conn.commit()
        mysql_conn.commit()
        
        start_datetime = start_datetime + datetime.timedelta(days=1)
        if start_datetime>datetime.date(2017, 5, 16):
            return




if __name__ == '__main__':
    main()
#!coding:utf8

import subprocess

import sys
from mf_utils.core import InitCore
from mf_utils.sql.mysql import MysqlHandle
from logger import Logger
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

reload(sys)
sys.setdefaultencoding('utf-8')

core = InitCore(project_name='jd_fetch_create_task')
sql = '''
select distinct source
from `morgan-manager`.schedule_task_define
where
createTime > date( now( ) - interval 7 day )
and valid = 1
and taskStatus = 'NEW'
and taskType = 'JD_FETCH'
'''
log = Logger.timed_rt_logger()


def main():
    log.info('running')
    script_name = {
        'ZHI_LIAN': '../jd_zhilian/create_task.py',
        'GJ_HR': '../jd_ganji/create_task.py',
        'FIVE_ONE': '../jd_51job/create_five_one_task.py',
        'FIVE_EIGHT': '../jd_58/create_task.py',
        'CH_HR': '../jd_chinahr/create_task.py'
    }
    db = MysqlHandle(host=core.common_settings.MYSQL_HOST,
                     user=core.common_settings.MYSQL_USER,
                     passwd=core.common_settings.MYSQL_PASSWD,
                     port=core.common_settings.MYSQL_PORT)
    for (source,) in db.query_by_sql(sql):
        script_name.pop(source)
    for (source, script) in script_name.items():
        popen = subprocess.Popen(['python', script])
        log.info('add task. source %s pid %s', source, popen.pid)


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(main, 'interval', minutes=5)
    scheduler.start()
    log.info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        while True:
            time.sleep(2)
        log.info('sleep!')
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info('Exit The Job!')

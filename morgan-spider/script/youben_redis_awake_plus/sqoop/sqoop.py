# -*-coding: utf-8-*-

from pyhive import hive
from TCLIService.ttypes import TOperationState

import sys
import os
import ConfigParser

reload(sys)
sys.setdefaultencoding('utf-8')

hive_config = {
    'host': '172.16.25.21',
    'port': 10000,
    'user_name': 'hive',
    'database': 'stg',
    'partition_name': 'rand_'
}

mysql_config = {}

config = {}

hive_sql = 'SELECT DISTINCT %s from %s.%s'

sqoop_script = 'sqoop export --connect jdbc:mysql://%s:%s/%s --username %s --password \'%s\' --table %s --export-dir oss://LTAI8IpG2WQ59zmQ:bXjPgYyNfZ6IBOPqU0wZxrCJQsV9bv@mf-hdfs.vpc100-oss-cn-beijing.aliyuncs.com/%s/%s/%s=%s --input-fields-terminated-by \'\\0001\' --input-null-string \'\\\\N\' --input-null-non-string \'\\\\N\';'

sqoop_script_hdfs = 'sqoop export --connect jdbc:mysql://%s:%s/%s --username %s --password \'%s\' --table %s --export-dir hdfs://emr-cluster/user/hive/warehouse/%s/%s=%s --input-fields-terminated-by \'\\0001\' --input-null-string \'\\\\N\' --input-null-non-string \'\\\\N\';'


def run():
    connection = hive.connect(host=hive_config['host'], port=hive_config['port'], username=hive_config['user_name'],
                              database=hive_config['database'])
    cursor = connection.cursor()
    do_run(cursor, hive_sql=hive_sql, sqoop_script=sqoop_script)
    connection.close()
    cursor.close()


def do_run(cursor, hive_sql=None, sqoop_script=None):
    hive_sql_ = hive_sql % (hive_config['partition_name'], hive_config['database'], hive_config['table_name'])
    print hive_sql_
    cursor.execute('''set hive.execution.engine=tez''')
    cursor.execute(hive_sql_, async=True)
    status = cursor.poll().operationState
    while status in (TOperationState.INITIALIZED_STATE, TOperationState.RUNNING_STATE):
        logs = cursor.fetch_logs()
        for message in logs:
            print message
        status = cursor.poll().operationState
    print 'final status : %s' % status
    result_list = cursor.fetchall()
    cursor.close()
    for (item,) in result_list:
        run_sqoop(sqoop_script=sqoop_script, item=item)


def run_sqoop(sqoop_script=None, item=None):
    if config['type'] == 'oss':
        sqoop_script_ = sqoop_script % (mysql_config['host'], mysql_config['port'], mysql_config['database'],
                                        mysql_config['user_name'], mysql_config['password'], hive_config['table_name'],
                                        hive_config['database'], hive_config['table_name'],
                                        hive_config['partition_name'], item)
    else:
        sqoop_script_ = sqoop_script_hdfs % (mysql_config['host'], mysql_config['port'], mysql_config['database'],
                                             mysql_config['user_name'], mysql_config['password'],
                                             hive_config['table_name'],
                                             hive_config['table_name'],
                                             hive_config['partition_name'], item)
    print sqoop_script_
    os.system(sqoop_script_)


def main():
    run()


if __name__ == '__main__':
    args = sys.argv
    cfg = ConfigParser.ConfigParser()
    cfg.read(args[1])
    mysql_config['host'] = cfg.get('mysql', 'host')
    mysql_config['port'] = cfg.get('mysql', 'port')
    mysql_config['database'] = cfg.get('mysql', 'database')
    mysql_config['user_name'] = cfg.get('mysql', 'user_name')
    mysql_config['password'] = cfg.get('mysql', 'password')
    hive_config['database'] = args[2]
    hive_config['table_name'] = args[3]
    config['type'] = args[4]
    main()

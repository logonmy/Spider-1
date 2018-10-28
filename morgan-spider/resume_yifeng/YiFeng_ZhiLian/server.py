#!coding:utf8

import requests
import json
import time
import settings
import util
import datetime
import re
import MySQLdb
import traceback
import uuid
from pykafka import KafkaClient
import random
# import redis
import threading
# from DBUtils.PooledDB import PooledDB
from DBUtils.PersistentDB import PersistentDB
import copy


def change_time_thread():
    logger = util.get_logger()
    logger.info('start check time!!!')
    global change_time_tag
    global stop_tag
    start_day = datetime.datetime.now().day
    while not stop_tag:
        if not change_time_tag and start_day != datetime.datetime.now().day:
            start_day = datetime.datetime.now().day
            change_time_tag = True
            logger.info('has change change_time_tag to True!!!, start_day is '+str(start_day))
        time.sleep(3600)

def main_zhilian(numbers_all):
    logger = util.get_logger()
    global change_time_tag
    kafka_client = KafkaClient(settings.KAFKA_HOSTS)
    kafka_producer = kafka_client.topics[settings.KAFKA_TOPIC].get_sync_producer()
    # redis_client = redis.Redis(host=settings.REDIS_HOST)
    user_now_key = ''

    mysql_pool = PersistentDB(
        MySQLdb, 
        host=settings.MYSQL_HOST, 
        user=settings.MYSQL_USER, 
        passwd=settings.MYSQL_PASSWD, 
        db=settings.MYSQL_DB, 
        port=settings.MYSQL_PORT, 
        charset='utf8'
    )
    mysql_conn = mysql_pool.connection()
    mysql_cursor = mysql_conn.cursor()

    cookie_dict = {}
    cookie = {}
    try:
        f=open('cookie_dict', 'r')
        cookie_str = f.readline()
        f.close()
        cookie_dict = json.loads(cookie_str)
        task_file = open('yifeng_zhilian.task', 'r')
        start_task = numbers_all['start_task']
        start_account = numbers_all['start_account']
        while start_task>0:
            task_str = task_file.readline()
            start_task -= 1
        accounts_file = open('accounts', 'r')
        while start_account>0:
            account = accounts_file.readline()
            start_account -= 1
    except Exception, e:
        logger.info('did not get task_file from file!!!'+ str(traceback.format_exc()))

    # # get one logined account
    try:
        user_now_str = accounts_file.readline()
        if not user_now_str:
            return 1
        user_now = json.loads(user_now_str)
        if not user_now:
            return 1
        numbers_all['start_account'] += 1
        if user_now['username'] not in cookie_dict:
            cookie_dict[user_now['username']] = {}
        cookie = copy.copy(cookie_dict[user_now['username']])
        login_result = util.login(user_now['username'], user_now['passwd'], user_now['proxy'], cookie_dict[user_now['username']])
        if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
            f=open('cookie_dict', 'w')
            f.write(json.dumps(cookie_dict))
            f.close()
            cookie = copy.copy(cookie_dict[user_now['username']])
        download_beans = 0
        # has_login = False
        if login_result['code'] not in [0, '0']:
            logger.info('login_result:'+str(login_result))
            raise Exception
        logger.info('login_result:'+str(login_result))
        download_beans = int(login_result['login_data']['todayNum'])
    except StopIteration, e:
        logger.info('there has no accout to use, quit!!!' + str(traceback.format_exc()))
        return 1
    except Exception, e:
        logger.info('error when login new account!!!' + str(traceback.format_exc()))
        #redis_client.delete(user_now_key)

    logger.info(numbers_all)
    for i in task_file:
        numbers_all['start_task'] += 1
        i_dict = json.loads(i.strip())
        logger.info('start to get data '+ str(i_dict))
        mysql_error_time=10
        list_page = i_dict.get('page_now', 1)

        while list_page>0 and numbers_all[i_dict['expcity']]>0:
            # list_page = 1
            while download_beans<settings.MIN_COIN:
                try:
                    if change_time_tag:
                        logger.info('get change_time_tag is True, stop the task and return loop!!!')
                        return 1
                    user_now_str = accounts_file.readline()
                    if not user_now_str:
                        return 1
                    user_now = json.loads(user_now_str)
                    if not user_now:
                        return 1
                    numbers_all['start_account'] += 1

                    if user_now['username'] not in cookie_dict:
                        cookie_dict[user_now['username']] = {}
                    cookie = copy.copy(cookie_dict[user_now['username']])
                    login_result = util.login(user_now['username'], user_now['passwd'], user_now['proxy'], cookie_dict[user_now['username']])
                    if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
                        f=open('cookie_dict', 'w')
                        f.write(json.dumps(cookie_dict))
                        f.close()
                        cookie = copy.copy(cookie_dict[user_now['username']])
                    download_beans = 0
                    if login_result['code'] == 2:
                        logger.info('login result:' + str(login_result))
                        time.sleep(10)
                        raise Exception
                    elif login_result['code']:
                        logger.info('login result:' + str(login_result))
                        raise Exception
                    download_beans = int(login_result['login_data']['todayNum'])
                except StopIteration, e:
                    logger.info('there has no accout to use, quit!!!' + str(traceback.format_exc()))
                    return 1
                except Exception, e:
                    logger.info('error when login new account!!!' + str(traceback.format_exc()))
                    time.sleep(3)

            logger.info('--------------download_beans:%d, list_page:%d, numbers_all:%s' % (download_beans, list_page, str(numbers_all)))
            time.sleep(3)
            # download list
            while download_beans>=settings.MIN_COIN and list_page>=0 and numbers_all[i_dict['expcity']]>0:
                
                list_result = util.get_zhilian_list(i_dict, user_now['proxy'], list_page, cookie_dict[user_now['username']])
                # logger.info(str(i_dict))
                # logger.info(str(list_result))
                # time.sleep(500000)
                if list_result['code'] not in [200, '200']:
                    logger.info('get error list ,continue!!!' + str(list_result))
                    download_beans = 0
                    continue
                # print 'has get the list of', list_page
                logger.info('has get the list of' + str(list_page))

                resume_list = list_result.get('resumeList', {}).get('resumeList', [])
                # logger.info('the resume_list is:'+str(resume_list))
                f=open('resume_list', 'w')
                f.write(json.dumps(resume_list, ensure_ascii=False))
                f.close()
                logger.info('sleeping')
                # time.sleep(3000000)

                for resume in resume_list:
                    # logger.info('start loop resume_list:'+str(resume))
                    resume_key_list = resume.get('url', '').split('?')
                    if not resume_key_list:
                        logger.info('did not find resume_key_list, continue...')
                        continue
                    resume_key = resume_key_list[0]
                    try:
                        has_find_in_mysql = mysql_cursor.execute('select * from resume_id where source=6 and resume_id="%s"' % resume_key)
                    except Exception, e:
                        logger.info('mysql error '+str(mysql_error_time)+' time:'+str(traceback.format_exc()))
                        mysql_error_time -= 1
                        if not mysql_error_time:
                            logger.info('there has no mysql_error_time')
                            # return
                        continue
                    if has_find_in_mysql:
                        logger.info('has find resume_key '+ resume_key + ' in mysql!!!')
                        continue
                    resume_result = util.get_zhilian_resume(resume.get('url', ''), user_now['proxy'], cookie_dict[user_now['username']])
                    # logger.info('the resume_result is:'+str(resume_result))
                
                    if resume_result['code'] in [200, '200']:

                        resume_uuid = uuid.uuid1()
                        try:
                            mysql_cursor.execute('insert into resume_raw (source, content, createBy, trackId, createtime, email) values ("YI_FENG_ZL", %s, "python", %s, now(), %s)' , (json.dumps(resume_result, ensure_ascii=False), resume_uuid, user_now['username']))
                            # save_mysql_id = int(mysql_conn.insert_id())
                            mysql_conn.commit()
                            mysql_cursor.execute('select last_insert_id()')
                            save_mysql_ids = mysql_cursor.fetchall()
                            if not save_mysql_ids or not save_mysql_ids[0]:
                                logger.info('insert into mysql error!!!:' + sql + '    ' + str(sql_value))
                                raise Exception
                            save_mysql_id = save_mysql_ids[0][0]
                        except Exception, e:
                            logger.info('mysql error '+str(mysql_error_time)+' time:'+str(traceback.format_exc()))
                            mysql_error_time -= 1
                            if not mysql_error_time:
                                # return
                                logger.info('there has no mysql_error_time')
                            continue

                        kafka_data = {
                            "channelType": "WEB",
                            "content": {
                                "content": json.dumps(resume_result, ensure_ascii=False),
                                "id": save_mysql_id,
                                "createBy": "python",
                                "createTime": int(time.time()*1000),
                                "ip": '',
                                "resumeSubmitTime": '',
                                "resumeUpdateTime": resume.get('updateTime', ''),
                                "source": "YI_FENG_ZL",
                                "trackId": str(resume_uuid),
                                "avatarUrl": '',
                            },
                            "interfaceType": "PARSE",
                            "resourceDataType": "RAW",
                            "resourceType": "RESUME_SEARCH",
                            "source": "YI_FENG_ZL",
                            "trackId": str(resume_uuid),
                            'traceID': str(resume_uuid),
                            'callSystemID': settings.CALLSYSTEMID,
                        }
                        logger.info('the raw id is:'+str(kafka_data['content']['id']))

                        kafka_producer.produce(json.dumps(kafka_data))
                        try:
                            mysql_cursor.execute('insert into resume_id (source, resume_id) values (6, "%s")' % resume_key)
                            mysql_conn.commit()
                        except Exception, e:
                            logger.info('mysql error '+str(mysql_error_time)+' time:'+str(traceback.format_exc()))
                            mysql_error_time -= 1
                            if not mysql_error_time:
                                # return
                                logger.info('there has no mysql_error_time')
                            continue
                        
                        # download_beans -= 1
                        numbers_all[i_dict['expcity']] -= 1

                        f = open('data', 'a')
                        f.write(json.dumps(kafka_data, ensure_ascii=False)+'\n')
                        f.close()
                        logger.info('has finish ' + resume_key)

                        if download_beans < settings.MIN_COIN:
                            break
                    elif resume_result['code'] == 6:
                        download_beans = 0
                        break
                    elif resume_result['code'] == 8:
                        download_beans = 0
                        break
                    elif resume_result['code'] == 9:
                        download_beans = 0
                        break
                    else:
                        pass
                    if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
                        f=open('cookie_dict', 'w')
                        f.write(json.dumps(cookie_dict))
                        f.close()
                        cookie = copy.copy(cookie_dict[user_now['username']])
                    time.sleep(4)
                    # logger.info('goto sleep...')
                    # time.sleep(3000000)
                if download_beans>=settings.MIN_COIN:
                    rowcount_list = list_result.get('resumeList', {}).get('rowcount', '').split('/')
                    # logger.info('rowcount_list:'+list_result.get('rowcount', ''))
                    # logger.info('list_result:'+str(list_result))
                    if len(rowcount_list)!=2 or rowcount_list[0]==rowcount_list[1]:
                        list_page = -1
                    else:
                        list_page += 1
                        i_dict['page_now'] += 1
                time.sleep(1)
                if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
                    f=open('cookie_dict', 'w')
                    f.write(json.dumps(cookie_dict))
                    f.close()
                    cookie = copy.copy(cookie_dict[user_now['username']])
            logger.info('download_beans:%d, i:%s, list_page:%d, numbers_all:%s' % (download_beans, i, list_page, str(numbers_all)))
            time.sleep(2)

    # accounts_file.close()
    task_file.close()
    accounts_file.close()

    mysql_cursor.close()
    mysql_conn.close()
    return 2

def main_yifeng(numbers_all):
    logger = util.get_logger()
    global change_time_tag
    kafka_client = KafkaClient(settings.KAFKA_HOSTS)
    kafka_producer = kafka_client.topics[settings.KAFKA_TOPIC].get_sync_producer()
    # redis_client = redis.Redis(host=settings.REDIS_HOST)
    user_now_key = ''

    mysql_pool = PersistentDB(
        MySQLdb, 
        host=settings.MYSQL_HOST, 
        user=settings.MYSQL_USER, 
        passwd=settings.MYSQL_PASSWD, 
        db=settings.MYSQL_DB, 
        port=settings.MYSQL_PORT, 
        charset='utf8'
    )
    mysql_conn = mysql_pool.connection()
    mysql_cursor = mysql_conn.cursor()

    cookie_dict = {}
    cookie = {}
    try:
        f=open('cookie_dict', 'r')
        cookie_str = f.readline()
        f.close()
        cookie_dict = json.loads(cookie_str)
        task_file = open('yifeng_yifeng.task', 'r')
        start_task = numbers_all['start_task']
        start_account = numbers_all['start_account']
        while start_task>0:
            task_str = task_file.readline()
            start_task -= 1
        accounts_file = open('accounts', 'r')
        while start_account>0:
            account = accounts_file.readline()
            start_account -= 1
    except Exception, e:
        logger.info('did not get task_file from file!!!'+ str(traceback.format_exc()))

    # # get one logined account
    try:
        user_now_str = accounts_file.readline()
        if not user_now_str:
            return 1
        user_now = json.loads(user_now_str)
        if not user_now:
            return 1
        numbers_all['start_account'] += 1
        if user_now['username'] not in cookie_dict:
            cookie_dict[user_now['username']] = {}
        cookie = copy.copy(cookie_dict[user_now['username']])
        login_result = util.login(user_now['username'], user_now['passwd'], user_now['proxy'], cookie_dict[user_now['username']])
        if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
            f=open('cookie_dict', 'w')
            f.write(json.dumps(cookie_dict))
            f.close()
            cookie = copy.copy(cookie_dict[user_now['username']])
        download_beans = 0
        # has_login = False
        if login_result['code'] not in [0, '0']:
            logger.info('login_result:'+str(login_result))
            raise Exception
        logger.info('login_result:'+str(login_result))
        download_beans = int(login_result['login_data']['todayNum'])
    except StopIteration, e:
        logger.info('there has no accout to use, quit!!!' + str(traceback.format_exc()))
        return 1
    except Exception, e:
        logger.info('error when login new account!!!' + str(traceback.format_exc()))
        #redis_client.delete(user_now_key)

    logger.info(numbers_all)
    for i in task_file:
        numbers_all['start_task'] += 1
        i_dict = json.loads(i.strip())
        logger.info('start to get data '+ str(i_dict))
        mysql_error_time=10
        list_page = i_dict.get('page_now', 1)

        while list_page>0 and numbers_all[i_dict['city']]>0:
            # list_page = 1
            while download_beans<settings.MIN_COIN:
                try:
                    if change_time_tag:
                        logger.info('get change_time_tag is True, stop the task and return loop!!!')
                        return 1
                    user_now_str = accounts_file.readline()
                    if not user_now_str:
                        return 1
                    user_now = json.loads(user_now_str)
                    if not user_now:
                        return 1
                    numbers_all['start_account'] += 1

                    if user_now['username'] not in cookie_dict:
                        cookie_dict[user_now['username']] = {}
                    cookie = copy.copy(cookie_dict[user_now['username']])
                    login_result = util.login(user_now['username'], user_now['passwd'], user_now['proxy'], cookie_dict[user_now['username']])
                    if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
                        f=open('cookie_dict', 'w')
                        f.write(json.dumps(cookie_dict))
                        f.close()
                        cookie = copy.copy(cookie_dict[user_now['username']])
                    download_beans = 0
                    if login_result['code'] == 2:
                        logger.info('login result:' + str(login_result))
                        time.sleep(10)
                        raise Exception
                    elif login_result['code']:
                        logger.info('login result:' + str(login_result))
                        raise Exception
                    download_beans = int(login_result['login_data']['todayNum'])
                except StopIteration, e:
                    logger.info('there has no accout to use, quit!!!' + str(traceback.format_exc()))
                    return 1
                except Exception, e:
                    logger.info('error when login new account!!!' + str(traceback.format_exc()))
                    time.sleep(3)

            logger.info('--------------download_beans:%d, list_page:%d, numbers_all:%s' % (download_beans, list_page, str(numbers_all)))
            time.sleep(3)
            # download list
            while download_beans>=settings.MIN_COIN and list_page>=0 and numbers_all[i_dict['city']]>0:
                
                list_result = util.get_yifeng_list(i_dict, user_now['proxy'], list_page, cookie_dict[user_now['username']])
                # logger.info(str(i_dict))
                # logger.info(str(list_result))
                # time.sleep(500000)
                if list_result['code'] not in [200, '200']:
                    logger.info('get error list ,continue!!!' + str(list_result))
                    download_beans = 0
                    continue
                # print 'has get the list of', list_page
                logger.info('has get the list of' + str(list_page))

                resume_list = list_result.get('bidPools', [])
                # logger.info('the resume_list is:'+str(resume_list))

                for resume in resume_list:
                    logger.info('start loop resume_list:'+str(resume))
                    try:
                        has_find_in_mysql = mysql_cursor.execute('select * from resume_id where source=6 and resume_id="%s"' % resume.get('userId', ''))
                    except Exception, e:
                        logger.info('mysql error '+str(mysql_error_time)+' time:'+str(traceback.format_exc()))
                        mysql_error_time -= 1
                        if not mysql_error_time:
                            logger.info('there has no mysql_error_time')
                            # return
                        continue
                    if has_find_in_mysql:
                        logger.info('has find userId '+ str(resume.get('userId', '')) + ' in mysql!!!')
                        continue
                    resume_result = util.get_yifeng_resume(str(resume.get('userId', '')), user_now['proxy'], cookie_dict[user_now['username']])
                    logger.info('the resume_result is:'+str(resume_result))
                
                    if resume_result['code'] in [200, '200']:

                        resume_uuid = uuid.uuid1()
                        try:
                            mysql_cursor.execute('insert into resume_raw (source, content, createBy, trackId, createtime, email) values ("YI_FENG", %s, "python", %s, now(), %s)' , (json.dumps(resume_result, ensure_ascii=False), resume_uuid, user_now['username']))
                            # save_mysql_id = int(mysql_conn.insert_id())
                            mysql_conn.commit()
                            mysql_cursor.execute('select last_insert_id()')
                            save_mysql_ids = mysql_cursor.fetchall()
                            if not save_mysql_ids or not save_mysql_ids[0]:
                                logger.info('insert into mysql error!!!:' + sql + '    ' + str(sql_value))
                                raise Exception
                            save_mysql_id = save_mysql_ids[0][0]
                        except Exception, e:
                            logger.info('mysql error '+str(mysql_error_time)+' time:'+str(traceback.format_exc()))
                            mysql_error_time -= 1
                            if not mysql_error_time:
                                # return
                                logger.info('there has no mysql_error_time')
                            continue

                        kafka_data = {
                            "channelType": "WEB",
                            "content": {
                                "content": json.dumps(resume_result, ensure_ascii=False),
                                "id": save_mysql_id,
                                "createBy": "python",
                                "createTime": int(time.time()*1000),
                                "ip": '',
                                "resumeSubmitTime": '',
                                "resumeUpdateTime": resume.get('updateTime', ''),
                                "source": "YI_FENG",
                                "trackId": str(resume_uuid),
                                "avatarUrl": '',
                            },
                            "interfaceType": "PARSE",
                            "resourceDataType": "RAW",
                            "resourceType": "RESUME_SEARCH",
                            "source": "YI_FENG",
                            "trackId": str(resume_uuid),
                            "callSystemID":settings.CALLSYSTEMID,
                            "traceID":str(resume_uuid)
                        }
                        logger.info('the raw id is:'+str(kafka_data['content']['id']))

                        kafka_producer.produce(json.dumps(kafka_data))
                        try:
                            mysql_cursor.execute('insert into resume_id (source, resume_id) values (6, "%s")' % resume.get('userId', ''))
                            mysql_conn.commit()
                        except Exception, e:
                            logger.info('mysql error '+str(mysql_error_time)+' time:'+str(traceback.format_exc()))
                            mysql_error_time -= 1
                            if not mysql_error_time:
                                # return
                                logger.info('there has no mysql_error_time')
                            continue
                        
                        # download_beans -= 1
                        numbers_all[i_dict['city']] -= 1

                        f = open('data', 'a')
                        f.write(json.dumps(kafka_data, ensure_ascii=False)+'\n')
                        f.close()
                        logger.info('has finish ' + resume.get('userId', ''))

                        if download_beans <  settings.MIN_COIN:
                            break
                    elif resume_result['code'] == 6:
                        download_beans = 0
                        break
                    elif resume_result['code'] == 8:
                        download_beans = 0
                        break
                    elif resume_result['code'] == 9:
                        download_beans = 0
                        break
                    else:
                        pass
                    if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
                        f=open('cookie_dict', 'w')
                        f.write(json.dumps(cookie_dict))
                        f.close()
                        cookie = copy.copy(cookie_dict[user_now['username']])
                    time.sleep(2)
                if download_beans>=settings.MIN_COIN:
                    if list_result.get('page', '') != list_result.get('totalPage', ''):
                        list_page += 1
                        i_dict['page_now'] += 1
                    else:
                        list_page = -1
                time.sleep(1)
                if cookie.get('JSESSIONID', '') != cookie_dict[user_now['username']].get('JSESSIONID', ''):
                    f=open('cookie_dict', 'w')
                    f.write(json.dumps(cookie_dict))
                    f.close()
                    cookie = copy.copy(cookie_dict[user_now['username']])
            logger.info('download_beans:%d, i:%s, list_page:%d, numbers_all:%s' % (download_beans, i, list_page, str(numbers_all)))
            time.sleep(2)

    # accounts_file.close()
    task_file.close()
    accounts_file.close()

    mysql_cursor.close()
    mysql_conn.close()
    return 2

if __name__ == '__main__':
    logger = util.get_logger()
    loop_count=0
    change_time_tag = False
    stop_tag = False

    # time_check_thread = threading.Thread(target=change_time_thread)
    # time_check_thread.start()

    numbers_all_yifeng = {'530': 999999, 'start_task': 0, 'start_account': 0}
    numbers_all_zhilian = {'530': 999999, 'start_task': 0, 'start_account': 0}
    #numbers_all = {'36,400': 1056, 'start_task': 701, '34,398': 2789, 'start_account': 163}
    while True:
        logger.info('============================================================================\nstart loop the main again '+ str(loop_count))
        if loop_count % 2:
            main_result = main_zhilian(numbers_all_zhilian)
            # main_result = main_yifeng(numbers_all_yifeng)
        else:
            # main_result = main_yifeng(numbers_all_yifeng)
            main_result = main_zhilian(numbers_all_zhilian)
        # 1: no account; 2: no task
        logger.info('goto sleep...')
        time.sleep(3000000)
        if main_result == 1:
            logger.info('there has no account.')
            numbers_all.update({'530': 999999, 'start_task': 0, 'start_account': 0, '34,398': 999999, '25,291': 999999, '25,292': 999999, '23,264': 999999, '27,312': 999999, '35,399': 999999})
            while not change_time_tag:
                logger.info('not change time, sleeping!!!')
                time.sleep(3600)
            change_time_tag = False
        elif main_result == 2:
            logger.info('there has no task.')
            numbers_all.update({'36,400': 999999, 'start_task': 0, '34,398': 999999, '25,291': 999999, '25,292': 999999, '23,264': 999999, '27,312': 999999, '35,399': 999999})
        else:
            logger.info('get error when process main:'+str(main_result))
            exit(0)

    # stop_tag = True
    # time_check_thread.join()
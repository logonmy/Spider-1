#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25
# 本模块为jd使用，用于jd采集，主要流程：导入utils模块，初始化utils，开启多个线程运行process_thread方法，逐个获取、处理任务
# 若调度流程不变，增删渠道时此模块无需更改


import os
import sys
import Queue
import traceback

import common_settings
import utils
import threading
import time
import process
import urllib
import uuid
import signal

stop_tag = False


def recive_stop_signal(signal_num, other):
    '''
    停止程序，可用kill pid停止本程序，程序收到停止信号后会执行本方法，设置stop_tag为True，之后每个线程执行完自己当前任务之后会直接退出，不会再次获取任务，如果需要急停，可以kill -9 pid，这样会强制停止，不会运行该方法
    '''
    global stop_tag
    stop_tag = True


def process_thread():
    '''
    每个线程的入口
    '''
    logger = utils.get_logger()
    logger.info('process_thread start!!!')
    global stop_tag
    while not stop_tag:
        # 获取一个任务，若没有获取到任务，则sleep，sleep时间为common_settings.SERVER_SLEEP_TIME
        task_traceid = str(uuid.uuid1())
        params = {'traceID': task_traceid, 'callSystemID': common_settings.CALLSYSTEMID,
                  'taskType': common_settings.TASK_TYPE, 'source': common_settings.SOURCE, 'limit': 1}
        param_str = '&'.join([str(i) + '=' + str(params[i]) for i in params])
        task_url = common_settings.TASK_URL + common_settings.GET_TASK_PATH + param_str
        task_result = utils.download(url=task_url, is_json=True)
        if task_result['code'] or task_result['json']['code'] not in [200, '200']:
            logger.info('get error task, sleep... url is:' + task_url + ' return is:' + str(task_result))
            time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        logger.info('get task!!!' + str(task_result))
        if not task_result['json']['data']:
            logger.info('did not get task_result data:' + str(task_result))
            time.sleep(common_settings.SERVER_SLEEP_TIME)
            continue
        process_result = {'code': -1, 'executeParam':task_result['json']['data'][0]['executeParam']}

        # 调用每个渠道自己的process.process模块处理各自的任务
        try:
            # logger.info('has get a task:' + str(task_result))
            # time.sleep(6)
            process_result = process.process(task_result['json'])
            # process_result = {'code': 1, 'executeResult': 'executeResultblablablabla', 'executeParam': 'executeParamblablablabla'}
        except Exception, e:
            logger.info('error when process:' + str(traceback.format_exc()))
        return_task_url = common_settings.TASK_URL + common_settings.RETURN_TASK_PATH
        return_task_traceid = str(uuid.uuid1())
        return_data = {}
        return_data['traceID'] = return_task_traceid
        return_data['callSystemID'] = common_settings.CALLSYSTEMID
        return_data['uuid'] = task_result['json']['data'][0]['uuid']
        return_data['executeResult'] = process_result.get('executeResult', '')
        # 返回调度任务处理的结果
        if not process_result.get('code', True):
            return_data['executeStatus'] = 'SUCCESS'
        else:
            return_data['executeStatus'] = 'FAILURE'
            logger.info('get a failed return of task!!!')
        for x in xrange(3):
            try:
                logger.info('send return task time ' + str(x))
                return_task_result = utils.download(url=return_task_url, is_json=True, method='post', data=return_data)
                if not return_task_result['code'] and return_task_result['json']['code'] in [200, '200']:
                    break
            except Exception, e:
                logger.info('error when send return task:' + str(traceback.format_exc()))

        # 如果处理失败，则向调度重新写入一条任务
        if process_result.get('code', True) and process_result.get('executeParam', ''):
            logger.info('start create task!!!')
            for insert_count in xrange(3):
                try:
                    logger.info('create task time ' + str(insert_count))
                    insert_url = common_settings.TASK_URL + common_settings.CREATE_TASK_PATH
                    insert_task_traceid = str(uuid.uuid1())
                    insert_data = {
                        'traceID': insert_task_traceid, 
                        'callSystemID': common_settings.CALLSYSTEMID,
                        'taskType': common_settings.TASK_TYPE, 
                        'source': common_settings.SOURCE,
                        'executeParam': process_result.get('executeParam', ''),
                        'parentUuid': task_result['json']['data'][0]['uuid'], 
                        # 'deadline': task_result['json']['data'][0]['deadline'],
                    }
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    }
                    insert_result = utils.download(url=insert_url, is_json=True, headers=headers, method='post', data=insert_data)
                    logger.info('insert result:'+str(insert_result))
                    if not insert_result['code'] and insert_result['json']['code'] in [200, '200']:
                        break
                except Exception, e:
                    logger.info('error when create task:' + str(traceback.format_exc()))

        time.sleep(5)


def main(project_settings):
    '''
    jd下载公共程序的入口程序，各个渠道在各自的脚本（如jd_chinahr_run.py、jd_liepin_run.py等）中加载完参数后，调用此方法开启各自的程序
    '''
    signal.signal(signal.SIGTERM, recive_stop_signal)
    
    # 初始化utils模块，设置各个渠道单独的参数和公共参数
    for i in project_settings:
        common_settings.__setattr__(i, project_settings[i])

    utils.set_setting(project_settings)
    logger = utils.get_logger()
    logger.info('=====================================================\nmain program start!!!')

    # 开启多线程，从调度获取任务、处理任务、返回任务
    process_thread_list = []
    for i in xrange(common_settings.DOWNLOAD_THREAD_NUMBER):
        new_thread = threading.Thread(target=process_thread, name='Thread-' + str(i))
        new_thread.start()
        process_thread_list.append(new_thread)

    # 等待任务结束
    for i in process_thread_list:
        i.join()

    logger.info('all thread has done, quit!!!')


def test():
    pass


if __name__ == '__main__':
    main({})
    # test()

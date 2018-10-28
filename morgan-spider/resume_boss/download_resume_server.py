#!coding:utf8

import requests
import logging
from logging.handlers import RotatingFileHandler
import traceback
import settings
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import time
import json
import uuid
from pykafka import KafkaClient

logger = None


def get_logger():
    global logger
    if not logger:
        logger = logging.getLogger('')
        formatter = logging.Formatter(
            fmt="%(asctime)s %(filename)s %(threadName)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        stream_handler = logging.StreamHandler()

        rotating_handler = logging.handlers.TimedRotatingFileHandler('./logs/download_resume.log', 'midnight', 1)

        stream_handler.setFormatter(formatter)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(rotating_handler)
        logger.setLevel(logging.INFO)
    return logger


def set_avaliable1(cooklie, uid, proxy):
    set_url = 'http://www.zhipin.com/setting/notify/set.json'
    set_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.zhipin.com',
        'Origin': 'http://www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    set_data = {
        'type': '2',
        'noMoreShow': '0',
        'sendMsg': '1',
        'msgContent': u'你好3',
        'geekId': str(uid),
    }
    set_response = requests.post(set_url, headers=set_headers, data=set_data, proxies=proxy, allow_redirects=False)
    print set_response.text


def set_avaliable(cooklie, uid, proxy):
    set_url = 'http://www.zhipin.com/chat/relation/groupset.json'
    set_headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.zhipin.com',
        'Origin': 'http://www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    set_data = {
        'geekId': 'abdf0c9ccc80b2441XJ839y1EVU~',
        'relationType': '6',
    }
    set_response = requests.post(set_url, headers=set_headers, data=set_data, proxies=proxy, allow_redirects=False)
    print set_response.text


def say_hello_info(cookie, params, proxy=None):
    logger = get_logger()
    logger.info('start say hello:' + str(params))
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy:' + str(proxy))
        result['code'] = 1
        return result
    say_hello_url = 'http://www.zhipin.com/chat/batchAddRelation.json'
    say_hello_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.zhipin.com',
        'Origin': 'http://www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im?mu=recommend&status=2',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie
    }
    say_hello_data = {
        'gids': params['gid'],
        'jids': params['jid'],
        'expectIds': params['expectid'],
        'lids': params['lid'],
    }

    say_hello_response = requests.post(say_hello_url, headers=say_hello_header, data=say_hello_data, proxies=proxy,
                                       allow_redirects=False, timeout=20)
    if say_hello_response.status_code not in [200, '200']:
        logger.info('say hello error:' + str(say_hello_response.status_code))
        result['code'] = 1
        return result
    result['code'] = 0
    return result


def get_communicate_list(cookie, page, proxy):
    logger = get_logger()
    logger.info('get communicate list')
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy')
        result['code'] = 1
        return result

    get_list_url = 'https://www.zhipin.com/chat/userList.json?page=%s&_=%s' % (page, str(int(time.time() * 1000)))

    get_list_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'https://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    get_list_response = requests.get(get_list_url, headers=get_list_header, proxies=proxy, allow_redirects=False,
                                     timeout=20)
    if get_list_response.status_code not in [200, '200']:
        logger.info('not get 200 when download communicate list:' + str(get_list_response.status_code))
        result['code'] = 2
        return result
    result['data'] = get_list_response.json().get('data', [])
    result['code'] = 0
    return result


def request_phone(cookie, uid, account_username, proxy=None):
    logger = get_logger()
    logger.info('start to requests phone:' + str(uid))
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy!!!')
        result['code'] = 1
        return result
    request_contact_url = 'https://www.zhipin.com/chat/requestContact.json?to=%s&_=%s' % (
        uid, str(int(time.time() * 1000)))
    request_contact_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'https://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    request_contact_response = requests.get(request_contact_url, headers=request_contact_header, proxies=proxy,
                                            allow_redirects=False, timeout=20)
    if request_contact_response.status_code not in [200, '200']:
        logger.info('did not get 200 when request contact:' + str(request_contact_response.status_code))
        result['code'] = 2
        return result
    request_json = request_contact_response.json()
    if request_json.get('result', 0) in [1, '1']:
        result['code'] = 0
        add_status_url = settings.ADD_URL % (uid, account_username, 'MOBILE')
        add_status_response = requests.get(add_status_url)
        if add_status_response.status_code in [200, '200'] and add_status_response.json()['code'] in [200, '200']:
            logger.info('add phone status success.')
        else:
            logger.info('add phone status failed.')
    else:
        result['code'] = 3
    return result


def get_phone(cookie, uid, proxy):
    logger = get_logger()
    logger.info('start to get phone of:' + uid)
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy!!!')
        result['code'] = 1
        return result
    get_phone_url = 'https://www.zhipin.com/chat/query/exchangephone.json?uid=' + uid
    get_phone_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'https://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    get_phone_response = requests.get(get_phone_url, headers=get_phone_header, proxies=proxy, allow_redirects=False,
                                      timeout=20)
    if get_phone_response.status_code not in [200, '200']:
        logger.info('did not get 200 when get phone number:' + str(get_phone_response.status_code))
        result['code'] = 2
        return result
    get_phone_json = get_phone_response.json()
    if get_phone_json.get('phone', ''):
        result['code'] = 0
        result['phone'] = get_phone_json['phone']
    else:
        result['code'] = 3
    return result


def get_resume(cookie, uid, en_uid, proxy=None):
    logger = get_logger()
    logger.info('start to get resume')
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy')
        result['code'] = 1
        return result
    get_resume_url = 'https://www.zhipin.com/chat/geek/chatinfo?uid=' + en_uid
    get_resume_header = {
        'Accept': 'text/plain, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'https://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    get_resume_response = requests.get(get_resume_url, headers=get_resume_header, proxies=proxy, allow_redirects=False,
                                       timeout=20)
    if get_resume_response.status_code not in [200, '200']:
        logger.info('not get 200 when get resume:' + str(get_resume_response.status_code))
        result['code'] = 2
        return result
    result['data'] = get_resume_response.text
    # print get_resume_response.text

    geek_url = 'http://www.zhipin.com/chat/geek.json?uid=' + str(uid)
    geek_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    geek_response = requests.get(geek_url, headers=geek_header, proxies=proxy, allow_redirects=False)

    position_url = 'http://www.zhipin.com/bossweb/job/%s.html' % str(geek_response.json()['data']['toPositionId'])
    position_headers = {
        'Accept': 'text/html, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    position_response = requests.get(position_url, headers=position_headers, proxies=proxy, allow_redirects=False)
    if position_response.status_code not in [200, '200']:
        logger.info('not get 200 when get position:' + str(position_response.code))
        result['code'] = 3
        return result
    result['position'] = position_response.text
    result['position_name'] = geek_response.json()['data']['positionName']
    result['code'] = 0
    return result


def update_weixin(cookie, weixin, proxy):
    logger = get_logger()
    logger.info('start to update weixin.')
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy')
        result['code'] = 1
        return result
    update_weixin_url = 'http://www.zhipin.com/user/updateWeixin.json'
    update_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.zhipin.com',
        'Origin': 'http://www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    update_data = {
        'weixin': weixin,
    }
    update_response = requests.post(update_weixin_url, data=update_data, headers=update_header, proxies=proxy,
                                    allow_redirects=False)
    if update_response.json().get('recode', 0) in [1, '1']:
        result['code'] = 0
        return result
    result['code'] = 2
    return result


def request_weixin(cookie, uid, account_username, proxy):
    logger = get_logger()
    logger.info('start to request weixin:' + str(uid))

    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy.')
        result['code'] = 1
        return result

    request_weixin_url = 'http://www.zhipin.com/chat/requestWeixin.json?to=%s&_=%s' % (
        str(uid), str(int(time.time() * 1000)))
    request_weixin_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'http://www.zhipin.com/chat/im',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    request_weixin_response = requests.get(request_weixin_url, headers=request_weixin_header, proxies=proxy,
                                           allow_redirects=False)
    print request_weixin_response.text
    if request_weixin_response.json().get('result', 0) in [1, '1']:
        result['code'] = 0
        # add_status_url = settings.ADD_URL % (uid, account_username, 'WECHAT')
        # add_status_response = requests.get(add_status_url)
        # # print add_status_response.text
        # if add_status_response.status_code in [200, '200'] and add_status_response.json()['code'] in [200, '200']:
        #     logger.info('add weixin status success.')
        # else:
        #     logger.info('add weixin status failed.')
    else:
        result['code'] = 2
    return result


def get_weixin(cookie, uid, proxy):
    logger = get_logger()
    logger.info('start to get weixin of:' + uid)
    result = {'code': 0}
    if not proxy:
        logger.info('there has no proxy!!!')
        result['code'] = 1
        return result
    get_phone_url = 'https://www.zhipin.com/chat/query/exchangeweixin.json?uid=' + uid
    get_phone_header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Host': 'www.zhipin.com',
        'Referer': 'https://www.zhipin.com/chat/im?mu=chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie,
    }
    get_phone_response = requests.get(get_phone_url, headers=get_phone_header, proxies=proxy, allow_redirects=False,
                                      timeout=20)
    if get_phone_response.status_code not in [200, '200']:
        logger.info('did not get 200 when get weixin number:' + str(get_phone_response.status_code))
        result['code'] = 2
        return result
    get_phone_json = get_phone_response.json()
    if get_phone_json.get('weixin', ''):
        result['code'] = 0
        result['weixin'] = get_phone_json['weixin']
    else:
        result['code'] = 3
    return result


def set_chinahr_cookie_invalid(account):
    logger = get_logger()
    logger.info('set chinahr cookie invalid!')
    try:
        if not account:
            logger.info('null account')
            return
        set_invalid_url = settings.SET_INVALID_URL % (account.get('userName', ''), account.get('password', ''))
        set_invalid_response = requests.get(set_invalid_url)
        # print set_invalid_response.text
    except Exception, e:
        logger.info('get error when set invalid cookie:' + str(traceback.format_exc()))


def get_account():
    logger = get_logger()
    logger.info('start to get account.')
    result = {'code': 0}
    try:
        get_account_response = requests.get(settings.GET_ACCOUNT_URL)
        if get_account_response.status_code not in [200, '200']:
            result['code'] = 2
            return result
        accounts = get_account_response.json()
        result['account'] = accounts['data'] or []
    except Exception, e:
        logger.info(str(traceback.format_exc()))
        result['code'] = 1
    return result


def check_download(account_username, uid):
    logger = get_logger()
    logger.info('start to check if the uid should download now:' + str(uid))

    result = 1
    check_url = settings.CHECK_URL % (str(uid), str(account_username))
    check_response = requests.get(check_url)
    # print check_response.text
    if check_response.status_code not in [200, '200']:
        result = 2
    # elif check_response.json().get('code', 1) == 0:
    #     result = 0
    # else:
    #     result = 1
    return check_response.json().get('code', 1)


def upload_resume(uid, account_username, phone, weixin, resume, position, username, jobname):
    logger = get_logger()
    logger.info('start to update resume:' + str(uid))
    upload_resume_url = settings.UPLOAD_RESUME_URL
    upload_resume_data = {
        'uid': uid,
        'loginAccount': account_username,
        'mobile': phone,
        'wechat': weixin,
        'jdContent': position.encode('utf8'),
        'resumeContent': resume.encode('utf8'),
        'name': username,
        'jobName': jobname,
        'callSystemID': settings.PROJECT_NAME,
        'traceID': str(uuid.uuid4())
    }
    header = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    # logger.info(str(upload_resume_data))
    upload_response = requests.post(upload_resume_url, data=upload_resume_data, headers=header)
    # print upload_response.text
    if upload_response.status_code not in [200, '200']:
        logger.info('update failed:' + str(upload_response.status_code))
    else:
        logger.info('update success')


def main():
    logger = get_logger()
    logger.info('start main.')
    proxy = {'http': 'http://H2CI114ZXVK7355D:C889D07037AA2C14@proxy.abuyun.com:9020',
             'https': 'http://H2CI114ZXVK7355D:C889D07037AA2C14@proxy.abuyun.com:9020'}

    accounts = get_account()
    if accounts['code']:
        logger.info('get error when get account:' + str(accounts))

    for account in accounts['account']:
        if not account.get('cookie', ''):
            logger.info('there has no cookie in account:' + str(account))
            set_chinahr_cookie_invalid(account)
            continue
        page_now = 1
        while page_now:
            list_result = get_communicate_list(account['cookie'], page_now, proxy)
            if list_result['code']:
                logger.info('get error when download list:' + str(list_result))
                page_now = 0
                continue
            if list_result['data']:
                page_now += 1
            else:
                page_now = 0
            for user in list_result['data']:
                if user['name'] == u'直聘助手':
                    logger.info('get 直聘助手, pass.')
                    continue
                weixin = get_weixin(account['cookie'], user['encryptUid'], proxy).get('weixin', '')
                phone = get_phone(account['cookie'], user['encryptUid'], proxy).get('phone')

                check_result = check_download(account['userName'], user['uid'])
                if check_result == 99:
                    logger.info('has say hello today.')
                    if weixin or phone:
                        resume_result = get_resume(account['cookie'], user['uid'], user['encryptUid'], proxy)
                        upload_resume(user['uid'], account['userName'], phone, weixin, resume_result['data'],
                                      resume_result['position'], user['name'], resume_result['position_name'])
                        # continue
                elif check_result == 100:
                    logger.info('need to change phone and weixin')
                    if not weixin:
                        request_weixin(account['cookie'], user['uid'], account['userName'], proxy)
                    if not phone:
                        request_phone(account['cookie'], user['uid'], account['userName'], proxy)
                    if weixin or phone:
                        resume_result = get_resume(account['cookie'], user['uid'], user['encryptUid'], proxy)
                        upload_resume(user['uid'], account['userName'], phone, weixin, resume_result['data'],
                                      resume_result['position'], user['name'], resume_result['position_name'])

                elif check_result == 101:
                    logger.info('need to change phone')
                    if not phone:
                        request_phone(account['cookie'], user['uid'], account['userName'], proxy)
                    else:
                        upload_resume(user['uid'], account['userName'], phone, weixin, '', '', '', '')
                        # resume_result = get_resume(account['cookie'], user['uid'], user['encryptUid'], proxy)
                        # upload_resume(user['uid'], account['userName'], phone, weixin, resume_result['data'], resume_result['position'], user['name'], resume_result['position_name'])

                elif check_result == 102:
                    logger.info('need to change weixin')
                    if not weixin:
                        request_weixin(account['cookie'], user['uid'], account['userName'], proxy)
                    else:
                        upload_resume(user['uid'], account['userName'], phone, weixin, '', '', '', '')
                        # resume_result = get_resume(account['cookie'], user['uid'], user['encryptUid'], proxy)
                        # upload_resume(user['uid'], account['userName'], phone, weixin, resume_result['data'], resume_result['position'], user['name'], resume_result['position_name'])
                elif check_result == 103:
                    logger.info('has find the user in mysql.')
                    # continue
                elif check_result == 106:
                    logger.info('i have the phone and weixin.')
                    # continue

                elif check_result == 104:
                    logger.info('phone and weixin both get 3times up, skip.')
                    if weixin or phone:
                        resume_result = get_resume(account['cookie'], user['uid'], user['encryptUid'], proxy)
                        upload_resume(user['uid'], account['userName'], phone, weixin, resume_result['data'],
                                      resume_result['position'], user['name'], resume_result['position_name'])
                        # continue

                elif check_result == 105:
                    logger.info('get 105, error use!!!')
                    # continue

                else:
                    logger.info('did not support check result')
                    # continue
                    # return
            time.sleep(20)


if __name__ == '__main__':
    main()
    # print get_account()
    # print check_download('15910286297', '999472')
    # cookie = 'wt=1GE1DZOS5hfLmYTs;t=1GE1DZOS5hfLmYTs'
    # p={'http': 'http://H2CI114ZXVK7355D:C889D07037AA2C14@proxy.abuyun.com:9020', 'https': 'http://H2CI114ZXVK7355D:C889D07037AA2C14@proxy.abuyun.com:9020'}
    # a= get_resume(cookie, '26641817', 'd43627e1aeb9c7c41XJz2t68Elc~', p)
    # print a
    # f=open('data', 'w')
    # f.write(json.dumps(a, ensure_ascii=False).encode('utf8'))
    # f.close()
    # b = get_weixin(cookie, '4dd2e8d675c47ee33n1z39q_', p)
    # c = get_phone(cookie, '4dd2e8d675c47ee33n1z39q_', p)
    # print upload_resume('999472', '15910286297', c['phone'], b['weixin'], a['data'], a['position'])
    # print set_avaliable(cookie, '26641817', p)
    # print request_weixin(cookie, '26641817', '15910286297', p)
    # print get_communicate_list(cookie, 1, p)

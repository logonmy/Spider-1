#!coding:utf8

import redis
import requests
import random
import time
import json
import re
import sys
sys.path.append("../common")
import common_settings
import utils
import datetime
import settings

uid_re = re.compile('buid=([^&]+)&')

def vote(user_id, proxies, device_id, cookie, limited=5, errors=3):
    logger = utils.get_logger()
    flag = 0
    error = 0
    get_user_headers = {
        'versionCode': 'Android_30',
        'versionName': 'Android_5.9.0',
        'UMengChannel': '2',
        'uid': user_id,
        'appSign': '-1012826753',
        'deviceID': device_id,
        'deviceName': 'MI5S',
        'role': 'boss',
        'deviceModel': 'MI5S',
        'deviceVersion': '6.0',
        'pushVersion': '52',
        'platform': 'Android-23',
        'User-Agent': 'ChinaHrAndroid5.9.0',
        'extion': '',
        'pbi': '{"itemIndex":0,"action":"click","block":"03","time":%s,"targetPage":"class com.chinahr.android.b.resumepoint.ResumePointMainActivity\/","page":"2302","sourcePage":""}' % str(int(time.time()*1000)),
        'Brand': 'Xiaomi',
        'device_id': device_id,
        'device_name': 'MI5S',
        'device_os': 'Android',
        'device_os_version': '6.0',
        'app_version': '5.9.0',
        'uidrole': 'boss',
        'utm_source': '2',
        'tinkerLoadedSuccess': 'false',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'app.chinahr.com',
        'Accept-Encoding': 'gzip',
    }
    while flag < limited:
        session = str(int(time.time() * 1000)) + str(
            random.random()).split('.')[1]
        url = "https://app.chinahr.com/buser/support?" \
              "buid=%s&session=%s" % (user_id, session)
        job_url = "https://app.chinahr.com/buser/showMicrojobs" \
                  "?buid=%s&session=%s" % (user_id, session)

        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Mobile Safari/537.36',
            'referer': 'https://app.chinahr.com/buser/cIndex.html?buid=%s'
                       % user_id
        }
        try:
            res_job = requests.get(job_url, headers=headers,
                                   proxies=proxies, timeout=30)
            res = requests.get(url, headers=headers, data='', proxies=proxies,
                               timeout=30)
        except requests.RequestException:
            continue
        code = json.loads(res.content).get("code")
        print res.content
        if code == 0:
            flag += 1
            logger.info("%s vote success %d" % (user_id, flag))
        else:
            error += 1
            logger.warning("%s vote fail %d" % (user_id, error))
            logger.info(res.content)

            if error >= errors:
                logger.error("%s vote error." % user_id)
                return False
        get_user_headers['Cookie'] = '; '.join(i[0]+'='+i[1] for i in cookie.items())
        for x in xrange(3):
            try:
                obtaincoin_response = requests.post(
                    'https://app.chinahr.com/buser/chrCoin/obtainCoin',
                    headers=get_user_headers, data={"taskId": 3},
                    proxies=proxies, timeout=30)
                break
            except Exception, e:
                continue
        else:
            return False

    return True

def delete_before_account_inredis(redis_client):
    date_today = datetime.datetime.today().strftime("%Y-%m-%d")
    redis_value_all = redis_client.keys('*-*-*_*_chinahr_*')
    for i in redis_value_all:
        if not i.startswith('date_today'):
            redis_client.delete(i)

def get_chinahr_cookie_all(proxy=None):
    logger = utils.get_logger()
    logger.info('get url fo get_account!')
    get_account_url = common_settings.ACCOUNT_URL % ('CH_HR', 'RESUME_INBOX') + '&all=true'
    cookie_result = {'code': 0, 'cookie': []}
    proxy = {}
    if not cookie_result['cookie']:
        try:
            logger.info('start to get cookie:'+get_account_url)
            cookie_json = utils.download(url=get_account_url)
            cookie_json['json'] = json.loads(cookie_json['data'])
            # print cookie_json['json']
            # exit(0)
            if cookie_json.get('code', 1) or not cookie_json['json'].get('data', []):
                logger.info('get error cookie!!!'+str(cookie_json))
                # set_chinahr_cookie_invalid(cookie_json['json']['data'])
                time.sleep(3)
            cookie_result['cookie'] = cookie_json['json']['data']

        except Exception, e:
            logger.info('get error when download cookie_result:'+str(traceback.format_exc()))
    return cookie_result

def main():
    logger = utils.get_logger()
    redis_client = redis.Redis(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
    delete_before_account_inredis(redis_client)
    cookie_result = get_chinahr_cookie_all()
    proxy = settings.get_proxy()
    start_count = 0
    if cookie_result['code']:
        logger.info('there has no cookie get.')
        return
    for cookie in cookie_result['cookie']:
        if start_count:
            start_count -= 1
            continue
        username = cookie.get('userName', '')
        password = cookie.get('password', '')
        if not cookie.get('cookie', ''):
            logger.info('not get uid in cookie:'+str(cookie))
            url = 'http://172.16.25.41:8002/acc/invalidCookie.json?userName=%s&password=%s' % (username, password)
            requests.get(url)
            continue
        #continue
        logger.info('start to deal with :'+username)
        try:
            cookie_dict = json.loads(cookie.get('cookie', '{}'))
        except Exception, e:
            logger.info('error when json cookie:'+username+' '+ password)
            continue
        uid_list = uid_re.findall(cookie_dict.get('bps', ''))
        device_id = json.loads(cookie.get('extraContent', '{}')).get('device_id', '')
        if not uid_list:
            logger.info('not get uid in cookie:'+str(cookie))
            url = 'http://172.16.25.41:8002/acc/invalidCookie.json?userName=%s&password=%s' % (username, password)
            requests.get(url)
            #break
            continue
        uid = uid_list[0]
        vote_result = vote(uid, proxy, device_id, cookie_dict)
        if not vote_result:
            logger.info('vote failed:'+str(cookie))
        redis_client.set(time.strftime("%Y-%m-%d")+'_'+username+'_chinahr_0', 1000)


if __name__ == '__main__':
    utils.set_setting({'PROJECT_NAME': 'chinahr_create_account_to_redis'})
    main()

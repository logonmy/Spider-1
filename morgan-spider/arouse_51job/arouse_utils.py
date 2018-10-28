#! /usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import sys

from DBUtils.PersistentDB import PersistentDB

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
import MySQLdb
import redis
import settings

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append("../common")
import utils




def find(pattern, context):
    if not context:
        return None

    findall = re.findall(pattern=pattern, string=context)

    if findall:
        return findall[0]
    else:
        return None


redis_pool = redis.ConnectionPool(host='172.16.25.36', port=6379)


def redis_get(key):
    redis_ = redis.Redis(connection_pool=redis_pool)
    return redis_.get(key)


def redis_delete(key):
    """
    :param key:
    :return: 1: 删除成功 , 0: key不存在 or删除失败
    """
    redis_ = redis.Redis(connection_pool=redis_pool)
    return redis_.delete(key)


def redis_incr(key):
    redis_ = redis.Redis(connection_pool=redis_pool)
    # return redis_.set(key, value, 3600 * 24)
    return redis_.incr(key)


def save_account_task_count(username):
    """
    保存帐号的任务执行次数
    :param username: 帐号
    :return: 此帐号当天的执行进入搜索列表次数
    """


def get_account_task_count(username):
    """
    保存帐号的任务执行次数
    :param username: 帐号
    :return: 此帐号当天的执行进入搜索列表次数
    """
    pass


usernames = open('account_list').readlines()


def invalid_account(account):
    logger = utils.get_logger()
    account_url = settings.INVALID_ACCOUNT_URL + 'userName=%s&password=%s' % (
        account.get('userName'), account.get('password'))
    account_result = utils.download(url=account_url, is_json=True)
    logger.info('cookies失效,帐号重新登录请求发送成功 %s', account_result.get('data', ''))


def get_one_cookies(username):
    if not username:
        return None
    # username = 'fptz'
    account_dict = utils.get_account(username.replace('\n', ''))
    dict_get = account_dict.get('cookie', '')
    if not dict_get:
        return None
    cookie_list = json.loads(dict_get)
    cookie_str = ''
    for cookie in cookie_list:
        mid = cookie.get('name') + '=' + cookie.get('value') + '; '
        cookie_str += mid
        cookie_str += '51job=cenglish%3D0; '
    cookie_str += 'adv=adsnew%3D0%26%7C%26adsresume%3D1%26%7C%26adsfrom%3Dhttp%253A%252F%252Fbzclk.baidu.com%252Fadrc.php%253Ft%253D06KL00c00fAjOKR07edR00uiAs0IoyPm00000rRPIH300000I1hgBF.THLZ_Q5n1VeHksK85yF9pywdpAqVuNqsusK15Hbzmhm1P1mknj0snjF-mH00IHY3nRDvfWnLPjnYn1fvnY7Dnjb1wj7anYR3wjIKnH64n0K95gTqFhdWpyfqnW6YnjnvPjbvriusThqbpyfqnHm0uHdCIZwsrBtEIZF9mvR8PH7JUvc8mvqVQLwzmyP-QMKCTjq9uZP8IyYqP164nWn1Fh7JTjd9i7csmYwEIbs1ujPbXHfkHNIsI--GPyGBnWKvRjFpXycznj-uURusyb9yIvNM5HYhp1YsuHDdnWfYnhf3mhn4PHK-PHbvmhnYPWD4mvm4nAuhm6KWThnqn1fsPWc%2526tpl%253Dtpl_10085_14394_1%2526l%253D1047858661%2526wd%253D%2525E5%252589%25258D%2525E7%2525A8%25258B%2525E6%252597%2525A0%2525E5%2525BF%2525A7%2526issp%253D1%2526f%253D8%2526ie%253Dutf-8%2526rqlang%253Dcn%2526tn%253Dbaiduhome_pg%2526inputT%253D2097%26%7C%26adsnum%3D789233; adv=adsnew%3D0%26%7C%26adsresume%3D1%26%7C%26adsfrom%3Dhttp%253A%252F%252Fbzclk.baidu.com%252Fadrc.php%253Ft%253D06KL00c00fAjOKR07edR00uiAs0mNG-m00000rRPIH300000I1hgBc.THYdnyGEm6K85yF9pywd0Znquj9BmyNBPHmsnj01PhcYnfKd5H6kfHuan1TYn1f1Pjm1fRfsrHPDnRc1wH9DPYDkrjbs0ADqI1YhUyPGujYzrjfsn1mYrHm4FMKzUvwGujYkP6K-5y9YIZ0lQzqYTh7Wui3dnyGEmB4WUvYEIZF9mvR8TA9s5v7bTv4dUHYLrjbzn1nhmyGs5y7cRWKWwAqvHjPbnvw4Pj7PNLKvyybdphcznZufn-G4mWcsrN-VwMKpi7uLuyTq5iuo5HK-nHRzPjfzuj9Bm1bdnARdrHuBm1fvnH-WuWbsuhuB0APzm1Ydrjc4n0%2526tpl%253Dtpl_10085_14394_1%2526l%253D1047858661%2526ie%253Dutf-8%2526f%253D3%2526tn%253Dbaidu%2526wd%253D51job%2526rqlang%253Dcn%2526prefixsug%253D51%2526rsp%253D3%2526inputT%253D3067%26%7C%26adsnum%3D789233;'
    account_dict['cookie'] = cookie_str.encode()

    return account_dict


def get_frist_post_headers(__VIEWSTATE, param):
    headers = {
        # '__VIEWSTATE': '/wEPDwUKLTIxNTcwNzQxNWQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgEFG3NlYXJjaF9zZWFyY2hlbmdpbmVfc3ViamVjdA==',
        '__VIEWSTATE': __VIEWSTATE,
        'search_area_hid': '',
        'sex_ch': '99|不限',
        'sex_en': '99|Unlimited',
        'hidSearchEngineid': '',
        'send_cycle': '1',
        'send_time': '7',
        'send_sum': '10',
        'hidWhere': '',
        'searchValueHid': "##0#" + param['function_code'] + "####5#99#20#30##99##########1##1#0##" + param[
            'region_code'] + "#0#0#0",
        'showGuide': '',
    }
    return headers


def get_get_headers(refer=None, cookie=None):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
    }
    if refer:
        headers['Referer'] = refer
    if cookie:
        headers['Cookie'] = cookie
    return headers


def get_by_externalids(ids):
    sql = 'select id,externalId,mobile from resume_picked WHERE externalId IN ('
    for id in ids:
        sql += id
        sql += ','
    sql = sql[:-1]
    sql += ')  AND source=2'
    conn, cur = utils.get_mysql_client()

    cur.execute(sql)
    results = cur.fetchall()
    if results:
        return results
    else:
        return None

mysql_pool = None
def get_mysql_client():
    global mysql_pool
    if not mysql_pool:
        mysql_pool = PersistentDB(MySQLdb, host=settings.AOURSE_DB_HOST, user=settings.AOURSE_DB_USER,
                                  passwd=settings.AOURSE_DB_PASS, db=settings.AOURSE_DB_NAME,
                                  port=3306, charset='utf8')
    conn = mysql_pool.connection()
    cur = conn.cursor()
    return conn, cur


def save_history(type, mobile=None, pick_id=None):
    logger = utils.get_logger()
    if type == 'AWAKE':
        sql = 'insert into resume_picked_history (pickType,mobile,searchPickId,valid,createTime,updateTime) VALUES ' \
              '("AWAKE", %s, %s, 1, now(), now())' % (mobile, pick_id)
    if type == 'CREATE':
        sql = 'insert into resume_picked_history (pickType,mobile,searchPickId,valid,createTime,updateTime) VALUES ' \
              '("CREATE", null, null, 1, now(), now())'
    conn, cur = get_mysql_client()
    try:
        cur.execute(sql)
        conn.commit()
    except:
        logger.error('save_history error %s', sql)
        pass


def update_arouse(info_id):
    logger = utils.get_logger()
    sql = 'update resume_picked set updateTime=now(),status=1,updateBy="AWAKE-BY-SEARCH" WHERE id=%s' % info_id
    conn, cur = utils.get_mysql_client()

    try:
        cur.execute(sql)
        conn.commit()
    except:
        logger.error('update_arouse error %s', sql)
        pass


def resumeArouse(enternal_ids):
    """
    从集合中拿取所有id 进行唤醒
    :param enternal_ids:
    :return:
    """
    logger = utils.get_logger()
    if not enternal_ids:
        return
    logger.info("进入唤醒流程,一共%s个" % len(enternal_ids))
    arouse_dict = {}  # 唤醒id-手机号
    arouse_dict_ectenal = {}  # 唤醒extenalid-id
    if enternal_ids:
        pick_from_db = get_by_externalids(enternal_ids)
        if pick_from_db:
            logger.info("数据库查询到可以唤醒的简历数量为:%s" % len(pick_from_db))
            for pick in pick_from_db:
                externalId = pick[1]
                id = pick[0]
                if externalId in enternal_ids:
                    arouse_dict[id] = pick[2]
                    arouse_dict_ectenal[externalId] = id
        else:
            logger.info("数据库查询到可以唤醒的简历数量为:0" )

        count_arouse = 0
        for enternal_id in enternal_ids:
            if arouse_dict_ectenal.has_key(enternal_id):
                info_id = arouse_dict_ectenal[enternal_id]
                save_history('AWAKE', mobile=arouse_dict.get(info_id), pick_id=info_id)
                update_arouse(info_id)
                count_arouse += 1
            else:
                save_history('CREATE')

        logger.info('唤醒完毕,一共%s个, 共唤醒 %s个' % (len(enternal_ids), count_arouse))

    return '唤醒完毕,一共%s个, 共唤醒 %s个,唤醒列表:%s' % (len(enternal_ids), count_arouse, json.dumps(arouse_dict_ectenal, ensure_ascii=False))


def test():
    # get_one_cookies()
    logger = utils.get_logger()
    account = {
        'password': 'sjzx2017',
        'userName': 'shhy8127',
    }
    invalid_account(account)
    # print redis_incr('test_redis_key')
    # print redis_incr('test_redis_key')
    # print redis_delete('test_redis_key')
    # print redis_incr('test_redis_key')


# test()

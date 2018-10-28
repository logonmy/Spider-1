#!coding:utf8

import utils
import json
import traceback
from lxml import etree
import settings
import time
import uuid
import re
import redis
import common_settings

# 获取redis客户端
redis_client = None
def get_redis_client():
    global redis_client
    if not redis_client:
        redis_client = redis.Redis(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
    return redis_client

# 设置账号ciikie失效
def set_chinahr_cookie_invalid(cookie_result):
    logger = utils.get_logger()
    logger.info('set chinahr cookie invalid!')
    try:
        if not cookie_result:
            logger.info('null cookie_result')
            return
        set_invalid_url = settings.project_settings['SET_INVALID_URL'] % (cookie_result.get('userName', ''), cookie_result.get('password', ''), settings.project_settings['SOURCE'])
        set_invalid_result = utils.download(url=set_invalid_url)
    except Exception, e:
        logger.info('get error when set invalid cookie:'+str(traceback.format_exc()))

# 从account模块获取账号
def get_chinahr_cookie(proxy=None):
    '''
    从account模块获取账号，并检查账号是否处于登录状态，若账号未处于登录状态或为获取到账号或账号cookie为空，则sleep后重新获取，直到获取到账号之后即返回
    '''
    logger = utils.get_logger()
    logger.info('get url fo get_account!')
    get_account_url = settings.project_settings['GET_ACCOUNT_URL'] % (settings.project_settings['SOURCE'], settings.project_settings['TASK_TYPE'])
    cookie_result = {'code': 0, 'cookie': {}}
    while not cookie_result['cookie']:
        try:
            logger.info('start to get cookie:'+get_account_url)
            cookie_json = utils.download(url=get_account_url)
            cookie_json['json'] = json.loads(cookie_json['data'])

            # 检查是否已经获取到账号或者哦账号pcookie是否为空
            if cookie_json.get('code', 1) or not cookie_json['json'].get('data', {}) or not cookie_json['json']['data'].get('cookie', ''):
                logger.info('get error cookie!!!'+str(cookie_json))
                set_chinahr_cookie_invalid(cookie_json['json']['data'])
                time.sleep(3)
                continue
            cookie_json = cookie_json['json']['data']
            cookie_json['cookie'] = json.loads(cookie_json['cookie'])
            cookie_str = '; '.join([i.get('name', '')+'='+i.get('value', '') for i in cookie_json.get('cookie', {})])

            check_is_login_url = 'http://passport.chinahr.com/ajax/pc/vaildateIsLogin?callback=jQuery110102000928863316167_%s&_=%s' % (str(int(time.time())*1000), str(int(time.time())*1000))
            check_is_login_headers = {
                'Accept':'*/*',
                'Accept-Encoding':'gzip, deflate, sdch',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Host':'passport.chinahr.com',
                'Referer':'http://www.chinahr.com',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            }

            check_is_login_json = {}

            # 检查账号是否处于登录状态
            for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                logger.info('start download:'+check_is_login_url)
                check_is_login_result = utils.download(url=check_is_login_url, proxy=proxy, headers=check_is_login_headers, cookie=cookie_str)
                if not check_is_login_result['code']:
                    check_is_login_json_list = re.findall('[^\(]*\((.*)\)[^\)]*', check_is_login_result['data'])
                    if not check_is_login_json_list:
                        logger.info('get error when check is_login:'+str(check_is_login_result))
                    else:
                        try:
                            check_is_login_json = json.loads(check_is_login_json_list[0])
                            break
                        except Exception as e:
                            logger.info('get error when parse check_is_login_json_list to json:'+str(check_is_login_json_list))
                            time.sleep(3)
                            # continue
                proxy.update(utils.get_proxy())
                # time.sleep(2)
            else:
                logger.info('error when check login, change account!!!')
                continue
            
            if check_is_login_json and check_is_login_json.get('isSuccess', False):
                cookie_result['cookie'] = cookie_str
                cookie_result['username'] = cookie_json.get('userName', '')
                cookie_result['password'] = cookie_json.get('password', '')
                logger.info('the account is login:'+str(check_is_login_result))
            else:
                logger.info('get a invalid cookie!!!'+str(check_is_login_json))
                set_chinahr_cookie_invalid(cookie_json)
                time.sleep(3)
        except Exception, e:
            logger.info('get error when download cookie_result:'+str(traceback.format_exc()))
        
    return cookie_result

# 处理单个任务
def process(task):
    logger = utils.get_logger()
    logger.info('process chinahr start!!!')
    redis_client = get_redis_client()
    result = {'code': 0}
    task_data_list = task.get('data', [])
    if not task_data_list or not task_data_list[0]['executeParam']:
        logger.info('did not get task_data_list!!!')
        result['code'] = 1
        return result
    task_data = json.loads(task_data_list[0]['executeParam'])
    if set(['cityCode', 'cityName']) - set(task_data.keys()):
        logger.info('not get full keys:'+ str(task_data.keys()))
        result['code'] = 2
        return result
    logger.info('deal with '+task_data['cityName'])
    task_data['pagenum'] = int(task_data.get('pagenum', 0)) or 1
    get_next_page_tag = True
    proxy = utils.get_proxy()
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Host':'www.chinahr.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }
    while get_next_page_tag:
        list_url = 'http://www.chinahr.com/sou/?orderField=relate&city=%s&keyword=%s&refreshTime=1&page=%s&salary=%s' % (task_data['cityCode'], task_data.get('keyword', ''), str(task_data['pagenum']), task_data.get('salary', ''))
        try:
            # 下载列表页
            for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                logger.info('start download list:'+list_url)
                list_result = utils.download(url=list_url, proxy=proxy, headers=headers)
                if not list_result['code']:
                    if len(list_result['data'])<1024:
                        logger.info('get '+list_result['data'])
                    else:
                        break
                proxy = utils.get_proxy()
                # time.sleep(2)
            else:
                logger.info('error when download:'+list_url)
                continue

            if list_result['code']:
                logger.info('get error when download list:' + str(list_result))
                raise Exception
            else:
                logger.info('success when download:'+list_url)
            tree_root = etree.HTML(list_result['data'])
            job_list = tree_root.xpath('.//div[@id="searchList"]/div[@class="resultList"]/div[@class="jobList"]')
            next_page = tree_root.xpath('''.//a[@onclick="clickLog('from=chr_list_lowpage_next');"]''')
            if u'对不起，没有找到满足条件的职位信息' in list_result['data'] and task_data['pagenum'] ==1:
                logger.info(u'没有符合条件的职位 %s' % task_data_list[0]['executeParam'])

            download_day = str(time.localtime().tm_mon)+'-'+str(time.localtime().tm_mday)
            
            for job_index, job in enumerate(job_list):
                try:
                    job_url = job.attrib.get('data-url', '')

                    # 检查该职位今题啊是否已经下载过，若下载过，则跳过
                    job_key = 'chinahr_jd_'+job_url.split('/')[-1].split('.')[0]
                    has_find_in_redis = False
                    try:
                        job_download_time=redis_client.get(job_key)
                        if job_download_time == download_day:
                            has_find_in_redis=True
                        else:
                            redis_client.set(job_key, download_day)
                    except Exception, e:
                        logger.info('get error when use redis.')

                    if has_find_in_redis:
                        logger.info('has find %s in redis' % job_key)
                        continue
                    else:
                        logger.info('not find %s in redis' % job_key)

                    urgent_flag = bool(job.xpath('.//li[@class="l1"]//span[@class="e1"]/a/i')) + 1 - 1
                    job_content = {
                        'content': '',
                        'urgentFlag': urgent_flag
                    }


                    # 下载详情页
                    for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                        logger.info('start download job:'+job_url)
                        cookie_result = get_chinahr_cookie(proxy)
                        if not cookie_result.get('cookie', {}):
                            logger.info('not get cookie!!!')
                            continue
                        job_result = utils.download(url=job_url, proxy=proxy, headers=headers, cookie=cookie_result['cookie'])
                        if not job_result['code']:
                            # 检查下载的页面是否有效
                            if 'SEO' not in job_result['data'].encode('utf8'):
                                logger.info('not find SEO in info!!!'+job_url)
                            elif len(job_result['data'])<1024:
                                logger.info('get '+job_result['data'])
                            else:
                                break
                        proxy = utils.get_proxy()
                        # time.sleep(2)
                    else:
                        logger.info('error when download:'+job_url)
                        continue

                    if job_result['code']:
                        logger.info('get error when download job_url:'+job_url+str(job_result))
                        continue
                    else:
                        logger.info('success when download:'+job_url)

                    # 获取job的公司信息
                    job_root = etree.HTML(job_result['data'])
                    company_urls = job_root.xpath('.//div[@class="job-company jrpadding"]//a')
                    company_info = ''
                    if not company_urls or not company_urls[0].attrib.get('href', ''):
                        logger.info('not get company_urls')
                    else:
                        company_url = company_urls[0].attrib['href']

                        for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                            logger.info('start download company:'+company_url)
                            company_result = utils.download(url=company_url, proxy=proxy, headers=headers)
                            if not company_result['code']:
                                if len(company_result['data'])<1024:
                                    logger.info('get '+company_result['data'])
                                else:
                                    break
                            proxy = utils.get_proxy()
                            # time.sleep(2)
                        else:
                            logger.info('error when download:'+company_url)
                            continue
                        if company_result['code']:
                            logger.info('get error when download company_url:'+company_url+str(company_result))
                        else:
                            logger.info('success when download:'+company_url)
                            company_info = company_result['data']

                    job_content['content'] = job_result['data'].encode('utf8')
                    job_str = json.dumps(job_content, ensure_ascii=False)


                    # 构建保存的sql语句，保存到mns的json数据，并保存数据
                    trace_uuid = str(uuid.uuid1())
                    sql = 'insert into jd_raw (source, content, createBy, trackId, createtime, pageUrl, searchConditions, pageNum, pageIndex, contactInfo) values ("' + settings.project_settings['SOURCE'] + '", %s, "python", %s, now(), %s, %s, %s, %s, %s)'
                    sql_value = (job_str, trace_uuid, job_url, json.dumps(task_data, ensure_ascii=False), task_data['pagenum'], job_index, company_info.encode('utf8'))
                    kafka_data = {
                        "channelType": "WEB",
                        "content": {
                            "content": job_str,
                            "id": '',
                            "createBy": "python",
                            "createTime": int(time.time()*1000),
                            "ip": proxy,
                            "jdUpdateTime": '',
                            "source": settings.project_settings['SOURCE'],
                            "trackId": '',
                            'contactInfo': company_info.encode('utf8'),
                            'searchConditions': json.dumps(task_data, ensure_ascii=False),
                            'pageUrl': job_url,
                        },
                        "interfaceType": "PARSE",
                        "resourceDataType": "RAW",
                        "resourceType": settings.project_settings['RESOURCE_TYPE'],
                        'protocolType': 'HTTP',
                        "source": settings.project_settings['SOURCE'],
                        "trackId": '',
                    }

                    utils.save_data(sql, sql_value, kafka_data)

                except Exception, e:
                    logger.info('get error when download:' + job_url + str(traceback.format_exc()))
                    continue
            if not next_page or not next_page[0].attrib.get('href', ''):
                logger.info('there has not job found!!!')
                get_next_page_tag = False
            else:
                task_data['pagenum'] += 1
                
        except Exception, e:
            logger.info('get error when deal task!!!' + str(traceback.format_exc()))
            result['code'] = result['code'] or 3
            result['executeParam'] = json.dumps(task_data)
            break

    return result

#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25
import utils
import json
import traceback
from lxml import etree
import settings
import time
import uuid
import re
import datetime
import redis
import common_settings
date_re = re.compile(r'发布于(\d+)月(\d+)日')

redis_client = None
def get_redis_client():
    global redis_client
    if not redis_client:
        # redis_pool = redis.ConnectionPool(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
        # redis_client = redis.Redis(redis_pool)
        redis_client = redis.Redis(host=common_settings.REDIS_IP, port=common_settings.REDIS_PORT, db=1)
    return redis_client

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
    # print task_data_list
    # time.sleep(50)
    task_data = json.loads(task_data_list[0]['executeParam'])
    # task_data = task_data_list[0]['executeParam']
    # if set(['cityCode', 'cityName', 'funcCode', 'funcName']) - set(task_data.keys()):
    if set(['city']) - set(task_data.keys()):
        logger.info('not get full keys:'+ str(task_data.keys()))
        result['code'] = 2
        return result
    logger.info('deal with '+str(task_data))
    task_data['pagenum'] = int(task_data.get('pagenum', 0)) or 1
    get_next_page_tag = True
    # proxy = utils.get_proxy()['proxy']
    proxy = utils.get_proxy()
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Host':'www.zhipin.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }
    while get_next_page_tag:
        get_next_page_tag = False

        city = task_data['city']
        zone = task_data.get('zone', '')
        # industry = task_data.get('industry', '')
        jobtitle = task_data.get('jobtitle', '')
        money = task_data.get('money', '')
        education = task_data.get('education', '')
        experience = task_data.get('experience', '')
        size = task_data.get('size', '')


        city_param = 'c' + str(city)
        zone_param =  'b_' + str(zone) if zone else ''
        # industry_param = 'i'+str(industry)+'-' if industry else ''
        jobtitle_param = '-p'+str(jobtitle) if jobtitle else ''
        money_param = 'y_'+str(money)+'-' if money else ''
        education_param = 'd_'+str(education)+'-' if education else ''
        experience_param = 'e_'+str(experience)+'-' if experience else ''
        size_param = 's_'+str(size)+'-' if size else ''


        if experience_param or education_param or size_param or money_param or zone_param:
            # list_url = 'http://www.zhipin.com/'+city_param+jobtitle_param+'/'+experience_param+education_param+size_param+money_param+zone_param+'/?page='+str(task_data['pagenum'])+'&ka=page-next'
            list_url = 'http://www.zhipin.com/'+city_param+jobtitle_param+'/'+experience_param+education_param+size_param+money_param+zone_param+'/?page='+str(task_data['pagenum'])
        else:
            # list_url = 'http://www.zhipin.com/'+city_param+jobtitle_param+'/?page='+str(task_data['pagenum'])+'&ka=page-next'
            list_url = 'http://www.zhipin.com/'+city_param+jobtitle_param+'/?page='+str(task_data['pagenum'])

        # if experience or education or size or money or zone:
        #     list_url = 'http://www.zhipin.com/'+industry_param+city_param+'/'+experience_param+education_param+size_param+money_param+zone_param+'/?page='+str(task_data['pagenum'])+'&ka=page-next'
        # else:
        #     list_url = 'http://www.zhipin.com/'+industry_param+city_param+'/?page='+str(task_data['pagenum'])+'&ka=page-next'

        try:
            for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                logger.info('start download list:'+list_url)
                list_result = utils.download(url=list_url, proxy=proxy, headers=headers, retry_time=3)
                time.sleep(5)
                if not list_result['code']:
                    if len(list_result['data']) < 1024:
                        logger.info('get '+list_result['data'])
                    elif u'<title>BOSS直聘验证码</title>' in list_result['data']:
                        logger.info('need verify code!')
                    elif u'<p>由于您当前网络访问页面过于频繁，可能存在安全风险，我们暂时阻止了您的本次访问，24小时将自动解除限制。</p>' in list_result['data']:
                        logger.info('get anti crawl page!')
                    else:
                        break
                proxy = utils.get_proxy()
                time.sleep(2)
            else:
                logger.info('error when download:'+list_url)
                result['executeParam'] = json.dumps(task_data)
                return result
            # time.sleep(300)
            if list_result['code']:
                logger.info('get error when download list:' + str(list_result))
                raise Exception
            else:
                logger.info('success when download:'+list_url)
            tree_root = etree.HTML(list_result['data'])
            job_list = tree_root.xpath('//div[@class="job-box"]/div[@class="job-list"]/ul/li')
            next_page = tree_root.xpath('''.//a[@class="next"]''')
            if u'没有找到相关职位，修改筛选条件试一下' in list_result['data'] and task_data['pagenum'] == 1:
                logger.info(u'没有符合条件的职位 %s' % task_data_list[0]['executeParam'])
            
            download_day = str(time.localtime().tm_mon)+'-'+str(time.localtime().tm_mday)
            for job_index, job in enumerate(job_list):
                try:
                    url_list = job.xpath('.//a')
                    if not url_list:
                        continue
                    elif len(url_list) == 1:
                        if 'job_detail' in url_list[0].attrib['href']:
                            job_url = 'http://www.zhipin.com'+url_list[0].attrib['href']
                            company_url = ''
                        else:
                            continue
                    else:
                        job_url = 'http://www.zhipin.com'+url_list[0].attrib['href']
                        company_url = 'http://www.zhipin.com'+url_list[1].attrib['href']


                    has_find_in_redis = False
                    job_key = 'boss_jd_'+job_url
                    try:
                        job_download_time=redis_client.get(job_key)
                        if job_download_time == download_day:
                            has_find_in_redis=True
                        else:
                            redis_client.set(job_key, download_day)
                    except Exception, e:
                        # redis_client.set(job_key, download_day)
                        logger.info('get error when use redis.')
                        pass
                    if has_find_in_redis:
                        logger.info('has find %s in redis' % job_key)
                        continue
                    else:
                        logger.info('not find %s in redis' % job_key)


                    if job.xpath('.//div[@class="job-time"]/span'):
                        # result['jobs'].append({'href': 'http://www.zhipin.com'+job.xpath('./a')[0].attrib['href'], 'job_time': job.xpath('.//div[@class="job-time"]/span')[0].text})
                        # job_url = 'http://www.zhipin.com'+job.xpath('./a')[0].attrib['href']
                        job_time = job.xpath('.//div[@class="job-time"]/span')[0].text.encode('utf8')
                    else:
                        continue
                    
                    if ':' in job_time or u'昨天' in job_time:
                        pass
                    # elif u'发布于' in job_time and u'月' in job_time and u'日' in job_time:
                    else:
                        continue
                        # date_split = date_re.findall(job_time)
                        # if date_split and len(date_split[0]) == 2 and date_split[0][0] and date_split[0][1]:
                        #     date_today = datetime.date.today()
                        #     date_before_three_day = datetime.date.today() - datetime.timedelta(days=3)
                        #     # job_time_split = job_time.split(u'发布于')
                        #     # if len(job_time_split)<2:
                        #     #     logger.info('can not recognize job_time:'+job_time)
                        #     #     continue
                        #     # job_real_time_split = job_time_split[1].split('-')
                        #     # if len(job_real_time_split)<2:
                        #     #     logger.info('can not recognize job_time:'+job_time)
                        #     #     continue
                        #     try:
                        #         date_real = datetime.date(date_today.year, int(date_split[0][0]), int(date_split[0][1]))
                        #         if date_today - date_real>datetime.timedelta(3):
                        #             continue
                        #     except Exception, e:
                        #         logger.info('can not recognize job_time:'+job_time)
                        #         continue
                        # else:
                        #     logger.info('can not recognize job_time:'+job_time)
                        #     continue





                    # elif date_re.findall(job_time) and date_re.findall(job_time)[0] and date_re.findall(job_time)[1]:
                    #     date_today = datetime.date.today()
                    #     date_before_three_day = datetime.date.today() - datetime.timedelta(days=3)
                    #     job_time_split = job_time.split(u'发布于')
                    #     if len(job_time_split)<2:
                    #         logger.info('can not recognize job_time:'+job_time)
                    #         continue
                    #     job_real_time_split = job_time_split[1].split('-')
                    #     if len(job_real_time_split)<2:
                    #         logger.info('can not recognize job_time:'+job_time)
                    #         continue
                    #     try:
                    #         date_real = datetime.date(date_today.year, int(job_real_time_split[0]), int(job_real_time_split[1]))
                    #         if date_today - date_real>datetime.timedelta(3):
                    #             continue
                    #     except Exception, e:
                    #         logger.info('can not recognize job_time:'+job_time)
                    #         continue
                    # else:
                    #     logger.info('can not recognize job_time:'+job_time)
                    #     continue

                    for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                        logger.info('start download job:'+job_url)
                        job_result = utils.download(url=job_url, proxy=proxy, headers=headers, retry_time=3)
                        time.sleep(5)
                        if not job_result['code']:
                            if len(job_result['data']) < 1024:
                                logger.info('get '+job_result['data'])
                            elif u'<title>BOSS直聘验证码</title>' in job_result['data']:
                                logger.info('need verify code!')
                            elif u'<p>由于您当前网络访问页面过于频繁，可能存在安全风险，我们暂时阻止了您的本次访问，24小时将自动解除限制。</p>' in job_result['data']:
                                logger.info('get anti crawl page!')
                            else:
                                break
                        proxy = utils.get_proxy()
                        time.sleep(2)
                    else:
                        logger.info('error when download:'+job_url)
                        continue
                        # result['executeParam'] = json.dumps(task_data)
                        # return result
                    if job_result['code']:
                        logger.info('get error when download job_url:'+job_url+str(job_result))
                        continue
                    else:
                        logger.info('success when download:'+job_url)
                    job_root = etree.HTML(job_result['data'])
                    # company_urls = job_root.xpath('//a[@ka="job-detail-company"]')
                    company_info = ''
                    if not company_url:
                        logger.info('not get company_url')
                    else:
                        # company_url = 'http://www.zhipin.com/gongsi/%s.html?ka=company-intro' % company_urls[0].attrib['href'].split('/')[2].split('.')[0][1:]
                        # while True:
                        #     logger.info('start download company:'+company_url)
                        #     company_result = utils.download(url=company_url, proxy=utils.get_proxy(), headers=headers)
                        #     if not company_result['code']:
                        #         break
                        #     proxy = utils.get_proxy()
                        #     time.sleep(2)
                        for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                            logger.info('start download company:'+company_url)
                            company_result = utils.download(url=company_url, proxy=proxy, headers=headers, retry_time=3)
                            time.sleep(5)
                            if not company_result['code']:
                                if len(company_result['data']) < 1024:
                                    logger.info('get '+company_result['data'])
                                elif u'<title>BOSS直聘验证码</title>' in company_result['data']:
                                    logger.info('need verify code!')
                                elif u'<p>由于您当前网络访问页面过于频繁，可能存在安全风险，我们暂时阻止了您的本次访问，24小时将自动解除限制。</p>' in company_result['data']:
                                    logger.info('get anti crawl page!')
                                else:
                                    break
                            proxy = utils.get_proxy()
                            time.sleep(2)
                        else:
                            logger.info('error when download:'+company_url)
                            continue
                            # result['executeParam'] = json.dumps(task_data)
                            # return result
                        if company_result['code']:
                            logger.info('get error when download company_url:'+company_url+str(company_result))
                        else:
                            logger.info('success when download:'+company_url)
                            company_info = company_result['data']

                    trace_uuid = str(uuid.uuid1())
                    sql = 'insert into jd_raw (source, content, createBy, trackId, createtime, pageUrl, searchConditions, pageNum, pageIndex, contactInfo) values ("' + settings.project_settings['SOURCE'] + '", %s, "python", %s, now(), %s, %s, %s, %s, %s)'
                    # task_data['cityName'] =  task_data['cityName'].decode('utf8')
                    # task_data['funcName'] =  task_data['funcName'].decode('utf8')
                    sql_value = (job_result['data'].encode('utf8'), trace_uuid, job_url, json.dumps(task_data, ensure_ascii=False), task_data['pagenum'], job_index, company_info.encode('utf8'))
                    kafka_data = {
                        "channelType": "WEB",
                        "content": {
                            "content": job_result['data'],
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

                    # f=open('kafka_data', 'a')
                    # f.write(json.dumps(kafka_data)+'\n')
                    # f.close()
                    # time.sleep(10)
                    utils.save_data(sql, sql_value, kafka_data)

                except Exception, e:
                    logger.info('get error when download:' + job_url + str(traceback.format_exc()))
                    continue
            if not next_page or not next_page[0].attrib.get('href', ''):
                logger.info('there has not job found!!!')
                get_next_page_tag = False
            else:
                task_data['pagenum'] += 1
                get_next_page_tag = True
                
        except Exception, e:
            logger.info('get error when deal task!!!' + str(traceback.format_exc()))
            result['code'] = result['code'] or 3
            result['executeParam'] = json.dumps(task_data)
            break

    return result

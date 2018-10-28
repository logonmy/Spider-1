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
import redis
import common_settings

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
    logger.info('process jd_liepin start!!!')
    result = {'code': 0}
    redis_client = get_redis_client()
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
    if set(['zone']) - set(task_data.keys()):
        logger.info('not get full keys:'+ str(task_data.keys()))
        result['code'] = 2
        return result
    logger.info('deal with '+str(task_data))
    task_data['pagenum'] = int(task_data.get('pagenum', 0))
    get_next_page_tag = True
    # proxy = utils.get_proxy()['proxy']
    proxy = utils.get_proxy()
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch, br',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Host':'www.liepin.com',
        #'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }
    headers={}
    while get_next_page_tag:

        zone = task_data.get('zone', '')
        # industry = task_data.get('industry', '')
        # industry2 = task_data.get('industry2', '')
        money = task_data.get('money', '')
        compkind = task_data.get('compkind', '')
        jobkind = task_data.get('jobkind', '')
        size = task_data.get('size', '')
        jobtitle = task_data.get('jobTitles', '')
        key_word = task_data.get('key', '')

        dqs_param =  str(zone) if zone else ''
        # industry_param = str(industry) if industry else ''
        # industry_2_param = str(industry2) if industry else ''
        jobTitles_param = str(jobtitle) if jobtitle else ''
        money_param = str(money) if money else ''
        compkind_param = str(compkind) if compkind else ''
        jobkind_param = str(jobkind) if jobkind else ''
        size_param = str(size) if size else ''
        key_word_param = str(key_word) if key_word else ''

        # list_url = 'https://www.liepin.com/zhaopin/?pubTime=3&fromSearchBtn=2&init=-1&industryType='+industry_param+'&industries='+industry_2_param+'&salary='+money_param+'&jobKind='+jobkind_param+'&compscale='+size_param+'&compkind='+compkind_param+'&dqs='+dqs_param+'&curPage='+str(task_data['pagenum'])


        # list_url = 'https://www.liepin.com/zhaopin/?pubTime=1&fromSearchBtn=2&init=-1&jobTitles='+jobTitles_param+'&salary='+money_param+'&jobKind=4&compscale='+size_param+'&compkind='+compkind_param+'&dqs='+dqs_param+'&curPage='+str(task_data['pagenum'])+'&key='+key_word_param
        #list_url = 'https://www.liepin.com/zhaopin/?pubTime=1&init=-1&jobTitles='+jobTitles_param+'&salary=&jobKind=&compscale=&compkind=&dqs='+dqs_param+'&searchType=1&d_pageSize=40&d_curPage='+str(task_data['pagenum'])+'&key='
        list_url = 'https://www.liepin.com/zhaopin/?pubTime=1&jobTitles='+jobTitles_param+'&searchType=1&dqs='+dqs_param+'&industryType=&industries=&salary=&key=&d_pageSize=40&d_curPage='+str(task_data['pagenum'])+'&&init=-1'
        try:
            for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                logger.info('start download list:'+list_url)
                list_result = utils.download(url=list_url, proxy=proxy, headers=headers)
                if not list_result['code']:
                    if len(list_result['data'])<1024:
                        logger.info('get '+list_result['data'])
                    else:
                        break
                proxy = utils.get_proxy()
                time.sleep(2)
            else:
                logger.info('error when download:'+list_url)
                result['executeParam'] = json.dumps(task_data)
                return result
            # while True:
            #     logger.info('start download list:'+list_url)
            #     list_result = utils.download(url=list_url, proxy=proxy, headers=headers)
            #     if not list_result['code']:
            #         break
            #     proxy = utils.get_proxy()
            #     time.sleep(2)
            # time.sleep(300)
            if list_result['code']:
                logger.info('get error when download list:' + str(list_result))
                raise Exception
            else:
                logger.info('success when download:'+list_url)
            tree_root = etree.HTML(list_result['data'])
            # sojob_result = tree_root.xpath('//div[@class="sojob-result "]') or tree_root.xpath('//div[@class="sojob-result"]') or tree_root.xpath('//div[@class="sojob-result sojob-no-result"]')
            job_list = tree_root.xpath('//ul[@class="sojob-list"]/li')
            if not job_list:
                logger.info('did not get job_list, return!!!')
                logger.info(u'没有符合条件的职位 %s' % task_data_list[0]['executeParam'])
                get_next_page_tag = False
                break
            # job_list = tree_root.xpath('//div[@class="job-box"]/div[@class="job-list"]/ul/li')
            # next_page = tree_root.xpath('''.//a[@onclick="clickLog('from=chr_list_lowpage_next');"]''')
            job_count_number = 0

            download_day = str(time.localtime().tm_mon)+'-'+str(time.localtime().tm_mday)
            
            for job_index, job in enumerate(job_list):
                if job.atrrib['class'] == 'downgrade-search':
                    if not job_count_number:
                        logger.info(u'没有符合条件的职位 %s' % task_data_list[0]['executeParam'])
                        get_next_page_tag = False
                    break
                try:
                    job_info=job.xpath('./div[@class="sojob-item-main clearfix"]/div[@class="job-info"]')[0]
                    if job_info:
                        job_url = 'https://www.liepin.com' + job_info.xpath('./h3/a')[0].attrib['href']
                    else:
                        continue
                    job_count_number += 1

                    # check if need download or not
                    job_key = 'liepin_jd_'+job_url.split('/')[-1].split('.')[0]
                    has_find_in_redis = False
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

                    urgent_flag = 0
                    type_flag = 2
                    if job.xpath('.//i[@class="icon icon-red-triangle"]'):
                        urgent_flag = 1
                    if job.xpath('.//i[@class="icon icon-blue-triangle"]'):
                        type_flag = 1
                    if job.xpath('.//i[@class="icon icon-orange-triangle"]'):
                        type_flag = 3
                    time.sleep(5)

                    job_content = {
                        'content': '',
                        'type': type_flag,
                        'urgentFlag': urgent_flag,
                    }


                    for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                        logger.info('start download job:'+job_url)
                        job_result = utils.download(url=job_url, proxy=proxy, headers=headers)
                        if not job_result['code']:
                            if len(list_result['data'])<1024:
                                logger.info('get '+list_result['data'])
                            else:
                                break
                        proxy = utils.get_proxy()
                        time.sleep(2)
                    else:
                        logger.info('error when download:'+job_url)
                        continue
                        # result['executeParam'] = json.dumps(task_data)
                        # return result
                    # while True:
                    #     logger.info('start download job:'+job_url)
                    #     job_result = utils.download(url=job_url, proxy=proxy, headers=headers)
                    #     if not job_result['code']:
                    #         break
                    #     proxy = utils.get_proxy()
                    #     time.sleep(2)
                    if job_result['code']:
                        logger.info('get error when download job_url:'+job_url+str(job_result))
                        continue
                    else:
                        logger.info('success when download:'+job_url)
                    job_root = etree.HTML(job_result['data'])
                    company_urls = job_root.xpath('//div[@class="title-info"]/h3/a')
                    company_info = ''
                    if not company_urls or not company_urls[0].attrib.get('href', ''):
                        logger.info('not get company_urls')
                    else:
                        company_url = company_urls[0].attrib['href']
                        for x in xrange(settings.project_settings['DOWNLOAD_RETRY_TIMES']):
                            logger.info('start download company:'+company_url)
                            company_result = utils.download(url=company_url, proxy=proxy, headers=headers)
                            if not company_result['code']:
                                if len(list_result['data'])<1024:
                                    logger.info('get '+list_result['data'])
                                else:
                                    break
                            proxy = utils.get_proxy()
                            time.sleep(2)
                        else:
                            logger.info('error when download:'+company_url)
                            continue
                            # result['executeParam'] = json.dumps(task_data)
                            # return result
                        # while True:
                        #     logger.info('start download company:'+company_url)
                        #     company_result = utils.download(url=company_url, proxy=utils.get_proxy(), headers=headers)
                        #     if not company_result['code']:
                        #         break
                        #     proxy = utils.get_proxy()
                        #     time.sleep(2)
                        if company_result['code']:
                            logger.info('get error when download company_url:'+company_url+str(company_result))
                        else:
                            logger.info('success when download:'+company_url)
                            company_info = company_result['data']

                    job_content['content'] = job_result['data'].encode('utf8')
                    job_str = json.dumps(job_content, ensure_ascii=False)
                    trace_uuid = str(uuid.uuid1())
                    sql = 'insert into jd_raw (source, content, createBy, trackId, createtime, pageUrl, searchConditions, pageNum, pageIndex, contactInfo) values ("' + settings.project_settings['SOURCE'] + '", %s, "python", %s, now(), %s, %s, %s, %s, %s)'
                    # task_data['cityName'] =  task_data['cityName'].decode('utf8')
                    # task_data['funcName'] =  task_data['funcName'].decode('utf8')
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

                    # f=open('kafka_data', 'a')
                    # f.write(json.dumps(kafka_data)+'\n')
                    # f.close()
                    # time.sleep(10)
                    utils.save_data(sql, sql_value, kafka_data)

                except Exception, e:
                    logger.info('get error when download:' + job_url + str(traceback.format_exc()))
                    continue
            get_next_page_tag = False
            #for i in tree_root.xpath('.//div[@class="pagerbar"]/a'):
            #    if i.text == u'下一页' and i.attrib['href'].startswith('http'):
            #        get_next_page_tag = True
            #        task_data['pagenum'] += 1
            #        break
            if u'下一页' in list_result['data']:
                get_next_page_tag = True
                task_data['pagenum'] += 1
                continue
                
        except Exception, e:
            logger.info('get error when deal task!!!' + str(traceback.format_exc()))
            result['code'] = result['code'] or 3
            result['executeParam'] = json.dumps(task_data)
            break

    return result

#!coding:utf8
import sys

sys.path.append('../common')
import utils
from lxml import etree
import common_settings
import uuid
import json
import time
import requests
import settings
import traceback
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import datetime

# ZONE_LIST = []
# INDUSTRY_LIST = [
#     {'industry_01': ['040', '420', '010', '030']}, 
#     {'industry_02': ['050', '060', '020']}, 
#     {'industry_03': ['080', '100', '090']}, 
#     {'industry_04': ['130', '140', '150', '430', '500']}, 
#     {'industry_05': ['190', '240', '200', '210', '220', '460', '470']},
#     {'industry_06': ['350', '360', '180', '370', '340']},
#     {'industry_10': ['270', '280', '290']},
#     {'industry_11': ['330', '310', '320', '300', '490']},
#     {'industry_07': ['120', '110', '440', '450', '230', '260', '510']},
#     {'industry_08': ['070', '170', '380']},
#     {'industry_09': ['250', '160', '480']},
#     {'industry_12': ['390', '410', '400']}
# ]

INDUSTRY_LIST = {
    'industry_01': ['040', '420', '010', '030'], 
    'industry_02': ['050', '060', '020'], 
    'industry_03': ['080', '100', '090'], 
    'industry_04': ['130', '140', '150', '430', '500'], 
    'industry_05': ['190', '240', '200', '210', '220', '460', '470'],
    'industry_06': ['350', '360', '180', '370', '340'],
    'industry_10': ['270', '280', '290'],
    'industry_11': ['330', '310', '320', '300', '490'],
    'industry_07': ['120', '110', '440', '450', '230', '260', '510'],
    'industry_08': ['070', '170', '380'],
    'industry_09': ['250', '160', '480'],
    'industry_12': ['390', '410', '400'], 
}

# SIZE_LIST = ['010 1-49', '020 50-99', '030 100-499', '040 500-999', '050 1000-2000', '060 2000-5000', '070 5000-10000', '080 10000-']
# SIZE_LIST = ['010', '020', '030', '040', '050', '060', '070', '080']
# COMPJIND = ['010外企外商独资', '020中外合营合资', '030私营民营企业', '040国有企业', '050上市公司', '060政府非营利机构', '070事业单位', '999其他']
# COMPKIND = ['010', '020', '030', '040', '050', '060', '070', '999']
# JOBKIND = ['1猎头职位', '2企业职位']
JOBKIND = ['1', '2']
MONEY_LIST = ['10$15', '15$20', '20$30', '30$50', '50$100', '100$999']

def get_list(city=None, zone=None, jobTitles=None, money=None, compkind=None, jobkind=None, size=None, page_now=None, proxy=None, **kwargs):
    logger = utils.get_logger()
    proxy = proxy if proxy else utils.get_proxy()
    # logger.info('the proxy is'+str(proxy))
    # logger.info('split_list_thread start!!!')
    result = {'code': 0, 'jobs': []}
    # list_url = 'http://www.zhipin.com/%s/e_105-d_203-s_302-y_4-b_%E6%9C%9D%E9%98%B3%E5%8C%BA/?page=%s&ka=page-next'
    dqs_param =  str(zone) if zone else ''
    jobTitles_param = str(jobTitles) if jobTitles else ''
    money_param = str(money) if money else ''
    compkind_param = str(compkind) if compkind else ''
    jobkind_param = str(jobkind) if jobkind else ''
    size_param = str(size) if size else ''
    # list_url = 'http://www.zhipin.com/%s/?page=%s' % (city, page_now)
    list_url = 'https://www.liepin.com/zhaopin/?pubTime=1&fromSearchBtn=2&init=-1&jobTitles='+jobTitles_param+'&salary='+money_param+'&jobKind='+jobkind_param+'&compscale='+size_param+'&compkind='+compkind_param+'&dqs='+dqs_param+'&curPage='+str(int(page_now-1))
    logger.info('the url, proxy is'+list_url+'    '+str(proxy))
    time.sleep(2)
    list_header = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch, br',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Host':'www.liepin.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }
    while True:
        logger.info('download url:'+list_url)
        try:
            response = requests.get(list_url, headers=list_header, allow_redirects=False, proxies=proxy, timeout=10)
            if response.status_code in [200, '200']:
                break
            else:
                logger.info('not get 200 when download list!!!'+ str(response.status_code))
        except Exception, e:
            logger.info(str(traceback.format_exc()))
        proxy.update(utils.get_proxy())
        
    
    tree = etree.HTML(response.text.encode('utf8'))
    sojob_result = tree.xpath('//div[@class="sojob-result "]')
    # result['jobs']=[]
    if sojob_result:
        jobs_list = sojob_result[0].xpath('./ul[@class="sojob-list"]/li')
        for job in jobs_list:
            if job.xpath('./div[@class="sojob-item-main clearfix"]/div[@class="job-info"]'):
                job_info=job.xpath('./div[@class="sojob-item-main clearfix"]/div[@class="job-info"]')[0]
                new_job = {}
                if job_info.xpath('./h3/a'):
                    new_job['href'] = job_info.xpath('./h3/a')[0].attrib['href']
                    new_job['job_time'] = job_info.xpath('.//p[@class="time-info clearfix"]/time')[0].text
                    # result['jobs'].append({'href': job_info.xpath('./h3/a')[0].attrib['href'], 'job_time': job_info.xpath('.//p[@class="time-info clearfix"]/time')[0].text})
                    result['jobs'].append(new_job)
                else:
                    logger.info("did not get job_info.xpath('./h3/a')!!!")
                    f=open('errorfile', 'w')
                    f.write(response.text.encode('utf8'))
                    f.close()
                    exit(0)
                # result['jobs'].append({'href': job_info.xpath('./h3/a')[0].attrib['href'], 'job_time': job_info.xpath('.//p[@class="time-info clearfix"]/time')[0].text})
            else:
                logger.info('get error when parse job!!!')
                #logger.info('get error when parse job!!!'+str(response.text.encode('utf8')))
                # error_file_lock.acquire()
                # f=open('error_file', 'a')
                # f.write(base64.b64encode(response.text.encode('utf8')))
                # f.close()
                # error_file_lock.release()
    else:
        logger.info('did not get sojob-result div')

    result['has_next_page'] = False
    if tree.xpath('.//div[@class="pagerbar"]/a'):
        for i in tree.xpath('.//div[@class="pagerbar"]/a'):
            if i.text == u'下一页' and i.attrib['href'].startswith('http'):
                result['has_next_page'] = True

    return result

def main():
    logger = utils.get_logger()
    global zones
    global industrys
    proxy = utils.get_proxy()
    # task_file = open('task_file', 'a')
    if not proxy:
        logger.info('did not get proxy, quit!!!')
        return 
    # proxy = None
    apply_origin_task = False
    origin_task = {"city": "250020",  "zone": "250020060"}
    cities_file = open('cities', 'r')
    CITY_LIST = json.loads(cities_file.readline())
    cities_file.close()
    city_dict_file = open('cities_dict', 'r')
    city_dict = json.loads(city_dict_file.readline())
    city_dict_file.close()
    jobTitles_file =open('keys_number', 'r')
    jobTitles = jobTitles_file.readlines()
    jobTitles_file.close()
    for city in CITY_LIST:
        if apply_origin_task and 'city' in origin_task:
            if city['c'] != origin_task['city']:
                continue
            else:
                origin_task.pop('city')
            if not origin_task:
                apply_origin_task = False
                continue
        logger.info('split task:'+str(city['c']))
        logger.info('---------------------------------------------------------')
        # time.sleep(10)
        for zone in city['relations']:
            if apply_origin_task and 'zone' in origin_task:
                if zone != origin_task['zone']:
                    continue
                else:
                    origin_task.pop('zone')
                if not origin_task:
                    apply_origin_task = False
                    continue
            else:
                process_dict = {'city': city['c'], 'zone': zone}
                list_result = get_list(page_now=100, proxy=proxy, **process_dict)
                logger.info('2================'+str(list_result))
                # time.sleep(5)
                if len(list_result['jobs']) < 39:
                    task_file = open('task_file', 'a')
                    for jobtitle in jobTitles:
                        if len(city['relations'])==1:
                            process_dict = {'city': city['c'], 'zone': zone, 'funName': jobtitle.split()[1], 'cityName': city_dict[zone][0], 'jobTitles': jobtitle.split()[0]}
                        else:
                            process_dict = {'city': city['c'], 'zone': zone, 'funName': jobtitle.split()[1], 'cityName': city_dict[city['c']][0]+'-'+city_dict[zone][0], 'jobTitles': jobtitle.split()[0]}
                        task_file.write(json.dumps(process_dict)+'\n')
                    task_file.close()
                    continue

            for jt in jobTitles:
                if apply_origin_task and 'jobTitles' in origin_task:
                    if jobTitles != origin_task['jobTitles']:
                        continue
                    else:
                        origin_task.pop('jobTitles')
                    if not origin_task:
                        apply_origin_task = False
                        continue
                else:
                    # process_dict = {'city': city['c'], 'zone': zone, 'jobTitles': jt.split()[0], 'funName': jt.split()[1], 'cityName': city_dict[zone][0]}
                    if len(city['relations'])==1:
                        process_dict = {'city': city['c'], 'zone': zone, 'funName': jt.split()[1], 'cityName': city_dict[zone][0], 'jobTitles': jt.split()[0]}
                    else:
                        process_dict = {'city': city['c'], 'zone': zone, 'funName': jt.split()[1], 'cityName': city_dict[city['c']][0]+'-'+city_dict[zone][0], 'jobTitles': jt.split()[0]}
                    list_result = get_list(page_now=100, proxy=proxy, **process_dict)
                    logger.info('3================'+str(list_result))
                    # time.sleep(5)
                    if len(list_result['jobs']) < 39:
                        task_file = open('task_file', 'a')
                        task_file.write(json.dumps(process_dict)+'\n')
                        task_file.close()
                        continue
                for money in MONEY_LIST:
                    if apply_origin_task and 'money' in origin_task:
                        if money != origin_task['money']:
                            continue
                        else:
                            origin_task.pop('money')
                        if not origin_task:
                            apply_origin_task = False
                            continue
                    else:
                        if len(city['relations'])==1:
                            process_dict = {'city': city['c'], 'zone': zone, 'funName': jt.split()[1], 'cityName': city_dict[zone][0], 'jobTitles': jt.split()[0], 'money': money,}
                        else:
                            process_dict = {'city': city['c'], 'zone': zone, 'funName': jt.split()[1], 'cityName': city_dict[city['c']][0]+'-'+city_dict[zone][0], 'jobTitles': jt.split()[0], 'money': money,}
                        # process_dict = {'city': city['c'], 'zone': zone, 'jobTitles': jt.split()[0], 'money': money, 'funName': jt.split()[1], 'cityName': city_dict[zone][0]}
                        list_result = get_list(page_now=100, proxy=proxy, **process_dict)
                        logger.info('4================'+str(list_result))
                        # time.sleep(5)
                        if len(list_result['jobs']) < 39:
                            task_file = open('task_file', 'a')
                            task_file.write(json.dumps(process_dict)+'\n')
                            task_file.close()
                            continue
                    # for compkind in COMPKIND:
                    #     if apply_origin_task and 'compkind' in origin_task:
                    #         if compkind != origin_task['compkind']:
                    #             continue
                    #         else:
                    #             origin_task.pop('compkind')
                    #         if not origin_task:
                    #             apply_origin_task = False
                    #             continue
                    #     else:
                    #         process_dict = {'city': city['c'], 'zone': zone, 'industry': industry, 'industry_2': industry_2, 'money': money, 'compkind': compkind}
                    #         list_result = get_list(page_now=100, proxy=proxy, **process_dict)
                    #         logger.info('5================'+str(list_result))
                    #         # time.sleep(5)
                    #         if len(list_result['jobs']) < 39:
                    #             task_file = open('task_file', 'a')
                    #             task_file.write(json.dumps(process_dict)+'\n')
                    #             task_file.close()
                    #             continue
                    for jobkind in JOBKIND:
                        if apply_origin_task and 'jobkind' in origin_task:
                            if jobkind != origin_task['jobkind']:
                                continue
                            else:
                                origin_task.pop('jobkind')
                            if not origin_task:
                                apply_origin_task = False
                                continue
                        else:
                            if len(city['relations'])==1:
                                process_dict = {'city': city['c'], 'zone': zone, 'funName': jt.split()[1], 'cityName': city_dict[zone][0], 'jobTitles': jt.split()[0], 'money': money, 'compkind': compkind,}
                            else:
                                process_dict = {'city': city['c'], 'zone': zone, 'funName': jt.split()[1], 'cityName': city_dict[city['c']][0]+'-'+city_dict[zone][0], 'jobTitles': jt.split()[0], 'money': money, 'compkind': compkind,}
                            # process_dict = {'city': city['c'], 'zone': zone, 'jobTitles
                            # process_dict = {'city': city['c'], 'zone': zone, 'jobTitles': jt.split()[0], 'money': money, 'compkind': compkind, 'jobkind': jobkind, 'funName': jt.split()[1], 'cityName': city_dict[zone][0]}
                            list_result = get_list(page_now=100, proxy=proxy, **process_dict)
                            logger.info('6================'+str(list_result))
                            # time.sleep(5)
                            if len(list_result['jobs']) < 39:
                                task_file = open('task_file', 'a')
                                task_file.write(json.dumps(process_dict)+'\n')
                                task_file.close()
                                continue
                            # for size in SIZE_LIST:
                            #     if apply_origin_task and 'size' in origin_task:
                            #         if size != origin_task['size']:
                            #             continue
                            #         else:
                            #             origin_task.pop('size')
                            #         if not origin_task:
                            #             apply_origin_task = False
                            #             continue
                            #     else:
                            #         process_dict = {'city': city['c'], 'zone': zone, 'industry': industry, 'industry_2': industry_2, 'money': money, 'compkind': compkind, 'jobkind': jobkind, 'size': size}
                            #         task_file = open('task_file', 'a')
                            #         task_file.write(json.dumps(process_dict)+'\n')
                            #         task_file.close()
                            #         # time.sleep(10000)


    # task_file.close()

def main2():
    logger = utils.get_logger()
    f=open('task_file', 'w')
    cities_file = open('cities_all', 'r')
    CITY_LIST = json.loads(cities_file.readline())
    cities_file.close()
    city_dict_file = open('cities_dict', 'r')
    city_dict = json.loads(city_dict_file.readline())
    city_dict_file.close()
    jobTitles_file =open('keys_number', 'r')
    jobTitles = jobTitles_file.readlines()
    jobTitles_file.close()
    for i in CITY_LIST:
        for j in i['relations']:
            if j not in city_dict:
                logger.info(j)
                continue
            for k in jobTitles:
                if len(i['relations'])==1:
                    process_dict = {'city': i['c'], 'zone': j, 'funName': k.split()[1], 'cityName': city_dict[j][0], 'jobTitles': k.split()[0]}
                else:
                    process_dict = {'city': i['c'], 'zone': j, 'funName': k.split()[1], 'cityName': city_dict[i['c']][0]+'-'+city_dict[j][0], 'jobTitles': k.split()[0]}
                f.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
    f.close()
    logger.info('done!!!')

def add_old_task():
    logger = utils.get_logger()
    f=open('task_file', 'r')
    count=214479
    start = 0
    for i in f:
        if start:
            start -= 1
            continue
        add_task_url = common_settings.TASK_URL +common_settings.CREATE_TASK_PATH
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',}
        add_task_data = {
            "callSystemID": settings.project_settings['CALLSYSTEMID'], 
            "source": settings.project_settings['SOURCE'], 
            "traceID": str(uuid.uuid1()),
            "executeParam": i, 
            "taskType": settings.project_settings['TASK_TYPE'], 
        }
        add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
        #count -= 1
        #if not count:
        #    break
    f.close()
    logger.info('finish add task!!!')

def create_task_from_mysql():
    logger = utils.get_logger()
    logger.info('start create task from mysql.')
    mysql_pool = PersistentDB(
        MySQLdb, 
        host=common_settings.MYSQL_HOST, 
        user=common_settings.MYSQL_USER,
        passwd=common_settings.MYSQL_PASSWD, 
        db=common_settings.MYSQL_DB,
        port=common_settings.MYSQL_PORT, 
        charset='utf8'
    )
    conn = mysql_pool.connection()
    cur = conn.cursor()
    city_number = cur.execute('select cityName, code from city_entrence where source="LIE_PIN" and valid=1')
    cities = cur.fetchall()
    function_number = cur.execute('select thirdFunction, thirdFunctionCode from function_entrence where source="LIE_PIN" and valid=1')
    functions = cur.fetchall()
    logger.info('the number of city and functions is:%s, %s' % (city_number, function_number))
    if not city_number or not function_number:
        return
    add_task_url = common_settings.TASK_URL +common_settings.CREATE_TASK_PATH
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',}
    deadline = datetime.datetime.now() + datetime.timedelta(days=2)
    deadline = int(time.mktime(deadline.timetuple())) * 1000
    task_deleted_file = open('task_deleted', 'r')
    task_deleted = json.load(task_deleted_file.readline())
    task_deleted_file.close()
    for city in cities:
        funcs_deleted = task_deleted.get(city[0], [])
        for function in functions:
            if function[1] in funcs_deleted:
                continue
            add_task_data = {
                "callSystemID": "morgan-chinahr-jd-1", 
                "source": settings.project_settings['SOURCE'], 
                "traceID": str(uuid.uuid1()), 
                # "executeParam": json.loads(i.strip()), 
                "executeParam": json.dumps({"jobTitles": function[1], "cityName": city[0], "zone": city[1], "funName": function[0]}, ensure_ascii=False), 
                "taskType": "JD_FETCH",
                'deadline': deadline,
            }
            add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
    logger.info('done.')

if __name__ == '__main__':
    utils.set_setting({"PROJECT_NAME": 'jd_liepin_create_task',})
    # add_old_task()
    # main()
    # main2()
    create_task_from_mysql()

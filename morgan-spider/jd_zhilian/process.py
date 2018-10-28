#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25


import json
import uuid
import datetime
import time
import traceback
from lxml import etree
import re
import sys
from settings import project_settings

reload(sys)
sys.setdefaultencoding("utf8")

sys.path.append("../common")
import utils


def process(task):
    logger = utils.get_logger()
    data = json.loads(task['data'][0]['executeParam'], encoding="utf-8")
    result = parse_list(data=data)
    if result and '200' in str(result['code']):
        logger.info('任务执行成功 %s ' % data)
        return {'code': 0, 'executeResult': 'SUCCESS'}
    else:
        logger.info('任务执行失败- %s ' % data)
        return {'code': 500, 'executeResult': 'FAILURE',
                'executeParam': json.dumps(result, encoding='utf8')}


def parse_list(data):
    logger = utils.get_logger()
    # url = data['url']
    city_url = data['cityUrl']
    page_num = data['pageNum']
    flg = True
    while flg:
        url = build_page_url(data=data, page_num=page_num)
        logger.info('请求列表页 url : %s' % (url,))
        if project_settings.get('useAby'):
            proxy = project_settings.get('aby')
        else:
            proxy = utils.get_proxy()
        results = download_page(url=url, method='get', proxy=proxy)
        proxy = results['proxy']
        content = results['data']
        if '暂时无符合您条件的职位' in content or '没有符合您要求的职位' in content:
            logger.info('没有符合条件的职位 %s' % json.dumps(data, ensure_ascii=False))
            data['code'] = 200
            flg = True
            break
        if '您要访问的页面暂时没有找到' in content:
            logger.info('页面没有找到，返回404 %s ' % url)
            data['code'] = 200
            flg = True
            break
        if 'jobs.zhaopin.com' in city_url:
            flg = parse_list_v1(page=content, page_num=page_num, data=data,
                                refer=url, proxy=proxy)
        else:
            flg = parse_list_v2(page=content, page_num=page_num, data=data,
                                refer=url, proxy=proxy)

        # 有解析到正常数据
        logger.info('解析列表页详情数据 返回结果 %s' % (json.dumps(flg, ensure_ascii=False)))
        if flg.has_key('status') and flg.get('status'):
            data['code'] = 200
            if flg.has_key('detail_count') and flg.get('detail_count') > 0:
                page_num += 1
            else:
                data['code'] = 200
                flg = False
                break
        else:
            logger.info('列表页面访问失败 %s ' % url)
            data['code'] = 500
            flg = False
            break
        # 对于职位很不错的列表页 直接跳出
        if '以下职位也很不错' in content:
            flg = False
            logger.info('含有 以下职位也很不错 跳出循环')
            data['code'] = 200
            break
    data['pageNum'] = page_num
    return data


def build_page_url(data=None, page_num=None):
    logger = utils.get_logger()
    if not page_num:
        page_num = 1
    city_url = data['cityUrl']
    func_code = data['funcCode']
    # pd=3 表示最近三天，pd=1 表示搜索当天,默认搜素最近三天
    pd = 3
    if project_settings.get('PD'):
        pd = project_settings.get('PD')
    if 'https://jobs.zhaopin.com/' in city_url:
        return city_url + 'sj' + str(func_code) + '/pd' + str(pd) + '/p' + str(
            page_num)
    else:
        return city_url + '&isfilter=1&pd=' + str(pd) + '&p=' + str(
            page_num) + '&sj=' + str(func_code)


def parse_list_v1(page=None, page_num=None, data=None, refer=None, proxy=None):
    logger = utils.get_logger()
    logger.info('parse_list_v1 当前解析第 %s 页 %s ' % (page_num, data))
    result = {}
    flg = True
    detail_count = 0
    document = etree.HTML(page.decode('utf-8'))
    try:
        containers = document.xpath(
            '//div[@class="main-left main_current_items"]//div[@class="details_container  " or  @class="details_container bg_container "]')
        if containers:
            page_index = 0
            for container in containers:
                time_ = datetime.datetime.now() - datetime.timedelta(days=2)
                time_str_ = time_.strftime('%y') + '-' + time_.strftime(
                    '%m') + '-' + time_.strftime('%d')
                if time_str_ in etree.tostring(container, encoding='utf-8'):
                    logger.info(
                        '当前行的发布时间为 %s ，超过时间限制，不再进行抓取 %s ' % (time_str_, refer))
                    flg = True
                    break
                vacancyid = container.xpath('input[@name="vacancyid"]/@value')
                if vacancyid:
                    key = 'zhilian_' + vacancyid[0]
                    if utils.redis_get(key):
                        logger.info('parse_list_v1已经抓取，跳过 %s-%s' % (key, refer))
                        continue
                    else:
                        logger.info('parse_list_v1当前id不重复，进行抓取 %s ' % key)
                        utils.redis_set(key, '1')
                page_index += 1
                detail_count += 1
                parse_list_columnV1(
                    content=etree.tostring(container, encoding='utf-8'),
                    page_num=page_num,
                    page_index=page_index, data=data, refer=refer, proxy=proxy)
        else:
            logger.error('parse_list_v1 没有找到details_container 元素  %s' % data)
            # flg = True
            result['info_length'] = 0

    except Exception as e:
        logger.error('parse_list_v1 出错了 %s %s' % (data, traceback.format_exc()))
        flg = False
    result['status'] = flg
    result['detail_count'] = detail_count
    logger.info('parse_list_v1 %s 第 %s 页执行完毕 %s ' % (refer, page_num, result))
    return result


def parse_list_v2(page=None, page_num=None, data=None, refer=None, proxy=None):
    logger = utils.get_logger()
    logger.info('parse_list_v2 当前解析第 %s 页 %s ' % (page_num, data))
    document = etree.HTML(page.decode('utf-8'))
    flg = True
    result = {}
    detail_count = 0
    try:
        div = document.xpath('//div[@id="newlist_list_content_table"]')
        if not div:
            logger.info(
                'newlist_list_content_table 没有符合条件的职位 %s' % json.dumps(data))
            result['info_length'] = 0
            result['status'] = True
            return result
        tables = div[0].xpath('//table')
        if tables:
            page_index = 0
            for table in tables:
                table_str_ = etree.tostring(table, encoding='utf-8')
                if '以下职位也很不错' in table_str_ or '前天' in table_str_:
                    logger.info('当前好行搜索到 推荐位置，或者是发布时间为前天，程序结束 %s ' % refer)
                    result['info_length'] = 0
                    result['status'] = True
                    break

                if '职位名称' not in table_str_ and '公司名称' not in table_str_:
                    logger.info('parse_list_v2 解析第 %s 条 ' % page_index)
                    page_index += 1
                    tr = table.xpath('tr')
                    if tr:
                        vacancyid = tr[0].xpath(
                            'td/input[@name="vacancyid"]/@value')
                        if vacancyid:
                            key = 'zhilian_' + vacancyid[0]
                            if utils.redis_get(key):
                                logger.info(
                                    'parse_list_v2已经抓取，跳过 %s-%s' % (key, refer))
                                continue
                            else:
                                logger.info(
                                    'parse_list_v2当前id不重复，进行抓取 %s ' % key)
                                utils.redis_set(key, '1')
                        detail_count += 1
                        pay_data = {}
                        # 置顶
                        on_top = table.xpath('.//tr[1]/td[1]/div/a[2]/img[1]')
                        if on_top:
                            pay_data['onTopFlag'] = 1
                        # 加急
                        urgent_flag = table.xpath(
                            './/tr[1]/td[1]/div/a[2]/img[2]')
                        if urgent_flag:
                            pay_data['urgentFlag'] = 1
                        # 会员服务
                        member = table.xpath('.//tr[1]/td[3]/a[2]/img')
                        if member:
                            pay_data['memberFlag'] = 1
                        logger.info('付费选项 %s' % pay_data)
                        parse_list_columnV2(
                            content=etree.tostring(tr[0], encoding='utf-8'),
                            page_index=page_index,
                            page_num=page_num, data=data, refer=refer,
                            proxy=proxy, pay_data=pay_data)
                    else:
                        logger.error('parse_list_v2 页面不包含 tr 标签 %s ' % data)
        else:
            logger.error('parse_list_v2 没有找到table元素 %s ' % data)
            result['info_length'] = 0
    except Exception as e:
        logger.error('parse_list_v2 出错了 %s ' % data)
        logger.error(traceback.format_exc())
        flg = False
    result['status'] = flg
    result['detail_count'] = detail_count
    logger.info('parse_list_v2 %s 第 %s 页执行完毕 %s ' % (refer, page_num, result))
    return result


def getToday():
    time_ = datetime.datetime.now()
    time_str_ = time_.strftime('%Y') + '-' + time_.strftime(
        '%m') + '-' + time_.strftime('%d')
    return time_str_


def parse_list_columnV1(content=None, page_num=None, page_index=None, data=None,
                        refer=None, proxy=None):
    logger = utils.get_logger()
    logger.info('parse_list_columnV1当前抓取 %s 第 %s 页 第 %s 行 ' % (
    refer, page_num, page_index))
    flg = False
    detail_page_url = re.search('<span class="post">\\s*<a href="([\\s\\S]*?)"',
                                content);
    if detail_page_url:
        jd_layout_time = re.search('<span class="release_time">(.*?)</span>',
                                   content)
        if jd_layout_time:
            jd_layout_time = jd_layout_time.group(1)
        logger.info('parse_list_columnV1 解析到的 职位发布时间 %s ' % jd_layout_time)
        flg = parse_detail_page(detail_page_url=detail_page_url.group(1),
                                page_num=page_num, page_index=page_index,
                                jd_layout_time=jd_layout_time, data=data,
                                refer=refer, proxy=proxy)
    else:
        logger.error('parse_list_columnV1 没有解析到详情页面url %s' % data)
    return flg


def parse_list_columnV2(content=None, page_num=None, page_index=None, data=None,
                        refer=None, proxy=None, pay_data=None):
    logger = utils.get_logger()
    logger.info('parse_list_columnV2当前抓取 %s 第 %s 页 第 %s 行 ' % (
    refer, page_num, page_index))
    detail_page = re.search(
        '<td class="zwmc"[\\s\\S]*?<a[\\s\\S]*?href="([\\s\\S]*?)" target',
        content)
    flg = False
    if detail_page:
        detail_page_url = detail_page.group(1)
        if detail_page_url:
            jd_layout_time = re.search('<td class="gxsj"><span>(.*?)</span>',
                                       content)
            if jd_layout_time:
                jd_layout_time = jd_layout_time.group(1)
            logger.info('parse_list_columnV2 解析到的 职位发布时间 %s %s' % (
            jd_layout_time, detail_page_url))
            flg = parse_detail_page(detail_page_url=detail_page_url,
                                    page_num=page_num,
                                    page_index=page_index,
                                    jd_layout_time=jd_layout_time, data=data,
                                    refer=refer, proxy=proxy, pay_data=pay_data)

    else:
        logger.error('parse_list_columnV2 没有解析到详情页面url %s ' % data)
    return flg


def parse_detail_page(detail_page_url=None, page_num=None, page_index=None,
                      jd_layout_time=None, data=None, refer=None,
                      proxy=None, pay_data=None):
    logger = utils.get_logger()
    flg = False
    city_name = data['cityName']

    logger.info('详情页面url：%s' % detail_page_url)
    results = download_page(url=detail_page_url, header=None, proxy=proxy,
                            method='get')

    if results['code'] == 0 and results['data'] and '您当前所在位置' in results[
        'data']:
        content = results['data']
        company_page = parse_company_page(content, proxy=proxy)
        flg = save_db(page_index=page_index, page_num=page_num,
                      page_content=content, page_url=detail_page_url,
                      city_name=city_name, jd_layout_time=jd_layout_time,
                      data=data, proxy=proxy,
                      company_page=company_page, pay_data=pay_data)
    else:
        logger.error('parse_detail_page 详情页面访问失败 %s' % detail_page_url)
    return flg


def parse_company_page(content=None, proxy=None):
    logger = utils.get_logger()
    document = etree.HTML(content.decode('utf-8'))
    company_page_url = document.xpath('//p[@class="company-name-t"]/a/@href')
    if company_page_url:
        company_page_url = company_page_url[0]
        company_page = download_page(url=company_page_url, method='get',
                                     proxy=proxy)
        logger.info('parse_company_page 获取公司信息成功 %s ' % company_page_url)
        if company_page['code'] == 0:
            try:
                company_page_ = utils.remove_emoji(company_page['data']).decode(
                    'utf-8', 'ignore')
                return company_page_
            except Exception as e:
                logger.error('公司页面编码失败 %s ' % company_page_url)
    else:
        logger.error('parse_company_page 没有解析到公司详情页面url')
    return ''


def download_page(url=None, method=None, header=None, refer=None, proxy=None):
    logger = utils.get_logger()
    result = {}
    # if not header:
    header = {
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0(Windows NT 10.0; WOW64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Accept': 'text/html, application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cookie': 'ZP_OLD_FLAG=true;'
    }
    if refer:
        header['Referer'] = refer
    for x in xrange(0, 3):
        # proxy = utils.get_proxy()
        if project_settings.get('useAby'):
            proxy = project_settings.get('aby')
        else:
            proxy = utils.get_proxy()
        logger.info('download_page : %s ' % url)

        result = utils.download(url=url, headers=header, method=method,
                                allow_redirects=True, retry_time=1,
                                proxy=proxy)
        print result
        if result['code'] == 0:
            logger.info('success when download %s-%s ' % (proxy, url))
            break
        time.sleep(1)

    result['proxy'] = ''
    return result


def save_db(page_index=None, page_num=None, page_content=None, page_url=None,
            city_name=None, jd_layout_time=None,
            data=None, company_page=None, proxy=None, pay_data=None):
    logger = utils.get_logger()
    flg = False
    '''
    保存原文到数据库
    '''
    try:
        # url = data['url']
        city_url = data['cityUrl']
        # data['url'] = ''
        data['cityUrl'] = ''
        track_id = str(uuid.uuid4())
        if proxy:
            proxy = proxy['http'].replace('http://', '')
        page_content = utils.remove_emoji(page_content).decode('utf8', 'ignore')
        if not pay_data:
            pay_data = {}
        pay_data['content'] = page_content
        sql = 'INSERT INTO jd_raw(trackId,source,content,createTime,createBy,ip,pageNum,pageIndex,pageUrl,jobCity,searchConditions,jdLayoutTime)VALUES(%s,"ZHI_LIAN",%s,now(),"python",%s,%s,%s,%s,%s,%s,%s)'
        sql_val = [uuid.uuid1(), json.dumps(pay_data, ensure_ascii=False),
                   proxy, page_num,
                   page_index, page_url,
                   city_name.decode('utf-8', 'ignore'),
                   json.dumps(data, ensure_ascii=False), jd_layout_time]
        # data['url'] = url
        data['cityUrl'] = city_url
        kafka_data = {
            "channelType": "WEB",
            "content": {
                "trackId": track_id,
                "content": json.dumps(pay_data, ensure_ascii=False),
                "id": '',
                "createTime": int(time.time() * 1000),
                "createBy": "python",
                "ip": proxy,
                "phoneUrl": '',
                "ocrImg": '',
                "jdLayoutTime": jd_layout_time,
                "pageUrl": page_url,
                "pageNum": page_num,
                "pageIndex": page_index,
                "jobCity": city_name.decode('utf-8', 'ignore'),
                "companyImgs": '',
                "source": "ZHI_LIAN",
                "searchConditions": json.dumps(data, ensure_ascii=False),
                "contactInfo": company_page.decode('utf-8', 'ignore'),
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "JD_SEARCH",
            'protocolType': 'HTTP',
            "source": "ZHI_LIAN",
            "trackId": track_id,
        }
        utils.save_data(sql, sql_val, kafka_data)
        logger.info('保存数据库成功')
        flg = True
    except Exception:
        logger.error('保存数据库异常 %s %s' % (page_url, traceback.format_exc()))
        flg = False
    return flg


if __name__ == '__main__':
    utils.set_setting(project_settings)
    # data = {"cityCode": "639", "pageNum": 1, "cityName": "苏州", "funcName": "无线电工程师", "funcCode": "318",
    #         "cityUrl": "https://sou.zhaopin.com/Jobs/searchresult.ashx?jl=639"}

    # https://sou.zhaopin.com/jobs/searchresult.ashx?bj=4010200&sj=006&jl=%E8%A5%BF%E5%AE%89&sm=0&p=1
    data = {
        'cityCode': '530',
        'cityName': '北京',
        'funcName': '销售代表',
        'funcCode': '006',
        'pageNum': 1,
        'cityUrl': 'https://sou.zhaopin.com/jobs/searchresult.ashx?jl=530',
    }
    #
    data = parse_list(data)
    # print utils.get_proxy()

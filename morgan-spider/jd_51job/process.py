#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25
import json
import re
import traceback
import uuid
import sys
import datetime

sys.path.append("../common")
sys.path.append("..")
from lxml import html as xmlh
import utils
from jd_51job.five_one_module import JdRaw
from jd_51job.spider_utils import find, trim, get_info_headers

logger = None
from settings import project_settings


# getproxies_ = None


def process(task):
    """
        根据一个搜索条件开始一项搜索
        :return:
        """
    global logger
    if project_settings.get('useAby'):
        getproxies_ = project_settings.get('aby')
    else:
        getproxies_ = utils.get_proxy()
    logger = utils.get_logger()
    param_dict = json.loads(task['data'][0]['executeParam'], encoding="utf-8")

    result = {'code': 0}
    track_id = str(uuid.uuid1())

    page_num = 1
    if param_dict['page_num']:
        page_num = param_dict['page_num']
    while True:
        url = get_list_url(param_dict, page_num)

        list_html_list = get_html(url, 5, track_id, getproxies_)
        if list_html_list:
            logger.info("list_html success when download: " + url)
            info_list = parse_list_html(list_html_list[0], track_id, page_num)
        else:
            # 页面不正常
            logger.error(u"列表页面获取失败: url=%s" % url)
            param_dict['page_num'] = page_num
            result['executeResult'] = 'list_html_error'
            result['executeParam'] = json.dumps(param_dict, ensure_ascii=False).encode()
            result['code'] = 1
            return result

        if 'none_jd' == info_list:
            # 抓取完了
            logger.info("此搜索条件无新职位可用: url=%s" % url)
            logger.info('没有符合条件的职位 %s' % json.dumps(param_dict))
            result['executeResult'] = u'正常完毕'
            return result
        else:
            for info in info_list:
                try:
                    info_mian(param_dict, info, track_id, getproxies_)
                except Exception, e:
                    logger.error(traceback.extract_stack())

        page_num += 1

        # return result


def get_list_url(param, page_num):
    if param.get('func_code'):
        url = "https://search.51job.com/jobsearch/search_result.php?jobarea" \
              "=%s&funtype=%s&curr_page=%s" % (
            param['region_code'], param['func_code'], page_num)
    else:
        url = "https://search.51job.com/jobsearch/search_result.php?jobarea" \
              "=%s&curr_page=%s" % (
            param['region_code'], page_num)
        # url = "https://search.51job.com/jobsearch/search_result.php
        # ?jobarea=%s&keyword=%s&curr_page=%s" % (
        #     param['region_code'], param['func_name'], page_num)
    return url


def get_html(url, retry, track_id, getproxies_):
    if not url.startswith('https'):
        url = "https:" + url
    """
    获取列表页面
    :return: 异常返回null
    """
    if retry <= 0:
        return None
    logger.info('开始连接: %s , retry= %s' % (url, retry))
    if project_settings.get('useAby'):
        getproxies_ = project_settings.get('aby')
    proxy_ip = None
    if getproxies_:
        proxy_ip = find('.*?(\d+\.\d+\.\d+\.\d+:\d+)', getproxies_.get("http"))

    result = utils.download(url=url, headers=get_info_headers(), proxy=getproxies_, encoding='gbk')
    if result['code'] != 0:
        logger.error("连接页面异常,track_id= %s ,重试: retry= %s" % (track_id, retry))
        # getproxies_.update(utils.get_proxy())
        return get_html(url, retry - 1, track_id, getproxies_)
    elif '用户数不够' in result['data'] \
            or '在线用户数超过' in result['data'] \
            or len(result['data']) < 1000:
        logger.error("代理异常,track_id= %s ,重试: retry= %s" % (track_id, retry))
        # getproxies_.update(utils.get_proxy())
        return get_html(url, retry - 1, track_id, getproxies_)
    return [result['data'], proxy_ip]


def parse_list_html(list_html, track_id, page_num):
    """
    解析列表页面
    :return: list: dict :job_url,job_name,layout
    """

    if '对不起，没有找到符合你条件的职位' in list_html:
        return 'none_jd'
    findall = re.findall('<div class="el">[\\s\\S]*?</div>', list_html)

    # lines = tree.xpath('//div[@id="resultList"]')
    if findall:
        info_list = []
        now_time = (datetime.datetime.now()).strftime("%m-%d")
        yestday_time = (datetime.datetime.now() + datetime.timedelta(-1)).strftime("%m-%d")
        for index, line in enumerate(findall):
            line = trim(line)
            tree = xmlh.document_fromstring(line)
            a_ = tree.xpath('//p/span/a')
            layout_txt = tree.xpath('//span[@class="t5"]/text()')[0]
            hot_flag = 0
            urgent_flag = 0
            if tree.xpath('.//p/span/img'):
                img_name = tree.xpath('.//p/span/img')[0].attrib['src'].split('/')[-1]
                if img_name == 'tag_hot.jpg':
                    hot_flag = 1
                elif img_name == 'tag_qk.jpg':
                    urgent_flag = 1
            if now_time == layout_txt or yestday_time == layout_txt:
                if a_:
                    job_url = a_[0].attrib.get('href')
                    if utils.redis_get(job_url):
                        continue
                    one_info = {
                        'job_url': job_url,
                        'job_name': a_[0].text.encode(),
                        'layout': layout_txt,
                        'page_num': page_num,
                        'page_index': index + 1,
                        'urgentFlag': urgent_flag,
                        'hotFlag': hot_flag,
                    }
                    info_list.append(one_info)
                    utils.redis_set(job_url, '1')
        if info_list:
            return info_list
    return 'none_jd'


def parse_info_html(param_dict, info_html, page_url, layout, track_id, getproxies_):
    """
    解析详情页,组织出raw对象
    :return: raw 对象
    """
    jdraw = JdRaw()
    jdraw.source = 'FIVE_ONE'
    jdraw.trackId = track_id
    jdraw.jdLayoutTime = str(layout)
    jdraw.content = info_html.encode()
    jdraw.pageUrl = page_url
    jdraw.jobCity = param_dict['region_name'].encode()
    jdraw.searchConditions = json.dumps(param_dict, ensure_ascii=False).encode()
    jdraw.createBy = 'python'
    if page_url.endswith('t=1'):
        jdraw.adTag = 1
    elif page_url.endswith('t=5'):
        jdraw.adTag = 2

    tree = xmlh.document_fromstring(info_html)
    xpath = tree.xpath('//p[@class="cname"]/a[@target="_blank"]')
    if xpath:
        a_ = xpath[0]
        company_url = a_.attrib.get('href')
        company_html_list = get_html(company_url, 3, track_id, getproxies_)
        if company_html_list:
            logger.info("company_html success when download: " + company_url)
            jdraw.contactInfo = company_html_list[0].encode()
    return jdraw


def info_mian(param_dict, info, track_id, getproxies_):
    """
    一条jd详情主方法
    :param info: dict :job_url,job_name,layout
    :return:
    """
    url = info.get('job_url')
    layout = info.get('layout')
    page_num = info.get('page_num')
    page_index = info.get('page_index')
    urgent_flag = info.get('urgentFlag')
    hot_flag = info.get('hotFlag')

    info_html_list = get_html(url, 4, track_id, getproxies_)

    if info_html_list:
        logger.info("detail_html success when download: " + url)
        try:
            jdraw = parse_info_html(param_dict, info_html_list[0], url, layout, track_id, getproxies_)
            jdraw.ip = info_html_list[1]
            jdraw.pageNum = page_num
            jdraw.pageIndex = page_index
        except Exception as e:
            logger.error(e.message)
        if jdraw:
            jd_raw_dict = {
                'content': jdraw.content,
                'hotFlag': hot_flag,
                'urgentFlag': urgent_flag,
            }
            jdraw.content = json.dumps(jd_raw_dict, ensure_ascii=False)
            sql = 'INSERT INTO jd_raw (' \
                  'trackId,source,content,createTime,createBy,jdLayoutTime,ip,pageUrl,jobCity,adTag,searchConditions,pageNum,pageIndex,contactInfo' \
                  ') values(%s, "FIVE_ONE", %s, now(), "python", %s, %s , %s, %s,%s, %s,%s, %s, %s)'
            value = (
                jdraw.trackId, jdraw.content, jdraw.jdLayoutTime, jdraw.ip, jdraw.pageUrl, jdraw.jobCity, jdraw.adTag,
                jdraw.searchConditions,
                jdraw.pageNum, jdraw.pageIndex, jdraw.contactInfo)
            kafka_data = {
                'trackId': jdraw.trackId,
                'source': jdraw.source,
                "channelType": 'WEB',
                'resourceType': 'JD_SEARCH',
                'resourceDataType': 'RAW',
                'content': jdraw.to_dics(),
                'protocolType': 'HTTP'
            }

            try:
                utils.save_data(sql, value, kafka_data)
            except Exception:
                logger.error(traceback.format_exc())


if __name__ == '__main__':
    # {u'func_name': u'\u77ff\u4ea7\u52d8\u63a2/\u5730\u8d28\u52d8\u6d4b\u5de5\u7a0b\u5e08', u'region_code': u'080306',
    # u'page_num': None, u'region_name': u'\u911e\u5dde\u533a', u'func_code': u'0579'}
    pass

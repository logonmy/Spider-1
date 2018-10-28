#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25
import traceback
import uuid
import lxml.html as xmlh
import datetime
import sys
sys.path.append("../common")

import oss2
from five_eight_module import JdRaw
import spider_utils
from spider_utils import *
import utils
import urllib
import time
logger = None


# proxies_ = None

# utils.get_proxy

def local_proxy():
    proxy = {
        'http':
            'http://H8HO3L3H1G6705SD:D56EA801A63B16CF@proxy.abuyun.com:9020',
        'https':
            'https://H8HO3L3H1G6705SD:D56EA801A63B16CF@proxy.abuyun.com:9020'
    }
    return proxy


def process(task):
    """
        根据一个搜索条件开始一项搜索
        :return:
        """
    global logger
    logger = utils.get_logger()
    param_dict = json.loads(task['data'][0]['executeParam'], encoding="utf-8")
    logger.info("开始一个搜索条件的搜索:" + param_dict.__str__())
    result = {'code': 0, }
    result['executeParam'] = json.dumps(param_dict, ensure_ascii=False)
    track_id = str(uuid.uuid1())
    proxy_ip = local_proxy()

    url = get_search_url(param_dict)
    if param_dict.get('err_url'):
        url = param_dict.get('err_url')
    logger.info('初始Url : %s' % url)
    while True:
        logger.info("开始连接列表页面 %s" % url)
        list_html_list = get_html(url, 5, track_id, proxy_ip=proxy_ip)
        if list_html_list:
            logger.info("list_html success when download: " + url)
            logger.info("开始解析列表页面 %s" % url)
            parse_list_html_result = parse_list_html(list_html_list[0], url, track_id, proxy_ip)
            if not parse_list_html_result:
                # 页面不正常  redis 存入异常点, 下次继续
                logger.error("列表页面获取失败: url=%s" % url)
                param_dict['err_url'] = url
                result['executeResult'] = 'list_html_error'
                result['executeParam'] = json.dumps(param_dict, ensure_ascii=False)
                result['code'] = 1
                return result
            elif 'none_jd' == parse_list_html_result:
                # 抓取完了
                logger.info("此搜索条件无新职位可用: url=%s" % url)
                logger.info('没有符合条件的职位 %s' % json.dumps(param_dict))
                result['executeResult'] = 'success '
                return result
            else:
                info_list = parse_list_html_result.get('info_list')
                next_url = parse_list_html_result.get('next_url')
                info_main(url, info_list, track_id, param_dict, proxy_ip)
                if next_url:
                    url = next_url
                else:
                    logger.info("此搜索条件无新职位可用: url=%s" % url)

                    result['executeResult'] = 'success'
                    return result
        else:
            # 页面不正常
            logger.error("列表页面获取结果不正常: url=%s" % url)
            param_dict['err_url'] = url
            result['executeResult'] = 'list_html_error'
            result['executeParam'] = json.dumps(param_dict, ensure_ascii=False)
            result['code'] = 0
            return result


def get_search_url(param_dict):
    """
    拼接获取访问所需url
    :return:
    """
    page_num = 1
    if param_dict.get('page_num'):
        page_num = param_dict['page_num']
    oneDayAgo = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime("%Y%m%d")
    oneDayAfter = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y%m%d")
    now_day = datetime.datetime.now().strftime("%Y%m%d")

    if param_dict.get('third_url'):
        url = param_dict['city_url'] + param_dict['third_url'] + '/pn' + str(
            page_num) + '/?postdate=' + oneDayAgo + "_" + oneDayAfter
    else:
        url = param_dict['city_url'] + 'job/pn' + str(page_num) + '/?postdate=' + oneDayAgo + "_" + oneDayAfter
        # url = param_dict['city_url'] + 'job/pn' + str(page_num) + '/?key=' + param_dict[
        #     'third_name'] + '&final=1&jump=1'
    return url


def get_ajax_result(ajaxurl, headers, retry, proxy_ip):
    if retry <= 0:
        return None
    logger.info("开始连接ajax %s" % ajaxurl)
    try:
        r = requests.get(ajaxurl, headers=headers, proxies=proxy_ip, timeout=8)
    except:
        logger.error("连接ajax异常,重试: retry= %s" % retry)
        proxy_ip.update(local_proxy())
        return get_ajax_result(ajaxurl, headers, retry - 1, proxy_ip)
    if 'deliveryCount' not in r.content:
        logger.error("连接ajax结果异常,重试: retry= %s" % retry)
        proxy_ip.update(local_proxy())
        return get_ajax_result(ajaxurl, headers, retry - 1, proxy_ip)
    return r.content


def parse_imgs_new(info_url, jd_html, raw, trackId, proxy_ip):
    """
    解析新版电话图片连接和公司详情页
    :param info_url: jd详情页连接
    :param html: jd详情页面
    :param raw: raw对象
    :param uuid_: uuid
    :return:
    """
    logger.info(" 进入新版本途径-解析图片:%s " % trackId)
    tree = xmlh.document_fromstring(jd_html)

    scripts = tree.xpath('/html/head/script/text()')
    if scripts:
        html = scripts[0]
        infoid = spider_utils.find(".*?infoid:'(\\d+)',.*?", html)
        userid = spider_utils.find(".*?userid:'(\\d+)',.*?", html)
        local = spider_utils.find(".*?local : \"(\\d+).*?", html)
        cateid = spider_utils.find(".*?cateid : \"(\\d+).*?", html)
        ajaxurl = "http://statistics.zp.58.com/position/totalcount/?infoId=" + infoid + \
                  "&userId=" + userid + "&local=" + local + "&cateID=" + cateid + "&referUrl="
        headers = spider_utils.get_info_headers(info_url)
        result = get_ajax_result(ajaxurl, headers, 4, proxy_ip=proxy_ip)
        logger.info("ajax - 返回结果: %s" % result)
        if result:
            logger.info("ajax success when download: " + ajaxurl)
            raw.ajax = result

        img_param = spider_utils.find('.*?pagenum :"(.*?)",', html)
        if "-" in img_param:
            img_param = img_param.split("-")[0]
        img_url = "http://image.58.com/showphone.aspx?t=v55&v=" + img_param
        oss_addr = save_mobile_imgs_to_oss(img_url, 4, trackId, proxy_ip)
        if oss_addr:
            logger.info("oss_img success when download: " + img_url)
            raw.ocrImg = oss_addr

        companys = tree.xpath("//div[@class='baseInfo_link']/a")
        if companys:
            company_link = companys[0].attrib.get("href")
        company_html_list = None
        headers = spider_utils.get_info_headers()
        if company_link:
            company_html_list = get_html(company_link, 4, trackId, headers=headers, proxy_ip=proxy_ip)
        if company_html_list:
            logger.info("company_html success when download: " + company_link)
            raw.contactInfo = company_html_list[0].encode()
        else:
            logger.error("没有获取到公司详情页面 %s" % trackId)


def parse_imgs(info_url, html, raw, trackId, proxy_ip):
    """
    解析出电话号码 见ring新版页面
    :param info_url:
    :param html:
    :param raw:
    :param uuid_:
    :return:
    """
    logger.info("开始图片.公司.ajax模块 %s" % info_url)
    tree = xmlh.document_fromstring(html)
    titles = tree.xpath('/html/head/title/text()')
    if not titles:
        logger.error("获取到的详情页面异常:%s" % html)
        return
    title = titles[0]
    if re.match('.*?请输入验证码.*?|.*?Denied Access Policy.*?|.*?ERROR.*?/Z', title):
        logger.error("获取到的详情页面异常:%s" % html)
        return
    size_ = len(tree.xpath('//div[@class="fabuBtn_Arr"]/a[@rel="nofollow"]'))  # 判断新旧版本
    if size_ == 2:  # 新版
        parse_imgs_new(info_url, html, raw, trackId, proxy_ip)
        return
    else:  # 旧版  暂时找不到旧版页面,暂停中
        logger.error('搜索到旧版页面---------------%s' % info_url)
        return


def parse_info_html(html_list, info, trackId, param_dict, proxy_ip):
    """
    解析组织详情页-组织出raw对象
    :return: raw对象
    """
    html = html_list[0].encode()
    info_url = info.get('info_url')
    raw = JdRaw()
    raw.source = 'FIVE_EIGHT'
    raw.adTag = info.get('adTag')
    raw.jdLayoutTime = str(info.get('jdLayoutTime'))
    raw.trackId = trackId
    raw.content = html.encode()
    raw.pageUrl = info_url
    raw.ip = html_list[1]
    raw.pageNum = str(info.get('pageNum'))
    raw.pageIndex = info.get('pageIndex')
    raw.jobCity = param_dict['city_name'].encode()
    raw.searchConditions = json.dumps(param_dict, ensure_ascii=False).encode()
    parse_imgs(info_url, html, raw, trackId, proxy_ip)
    if raw.content:
        jd_content_dict = {
            'content': raw.content,
            'onTopFlag': info.get('onTopFlag', 0),
            'authentication': info.get('authentication', {})
        }
        if info.get('memberFlag', 0):
            jd_content_dict['memberFlag'] = info['memberFlag']
        raw.content = json.dumps(jd_content_dict, ensure_ascii=False)
        sql = 'INSERT INTO jd_raw (' \
              'trackId,source,content,createTime,createBy,jdLayoutTime,ip,pageUrl,jobCity,ocrImg,adTag,searchConditions,pageNum,pageIndex,contactInfo' \
              ') values(%s, "FIVE_EIGHT", %s, now(), "python", %s, %s ,%s, %s, %s,%s, %s,%s, %s, %s)'
        value = (
            raw.trackId, raw.content, raw.jdLayoutTime, raw.ip, raw.pageUrl, raw.jobCity, raw.ocrImg, raw.adTag,
            raw.searchConditions,
            raw.pageNum, raw.pageIndex, raw.contactInfo)

        kafka_data = {
            'trackId': raw.trackId,
            'source': raw.source,
            "channelType": 'WEB',
            'resourceType': 'JD_SEARCH',
            'resourceDataType': 'RAW',
            'content': raw.to_dics(),
            'protocolType': 'HTTP'
        }
        try:
            utils.save_data(sql, value, kafka_data)
        except Exception, e:
            logger.error(traceback.format_exc())


def save_mobile_imgs_to_oss(img_url, retry, trackId, proxy_ip):
    """
    连接获取电话图片保存oss
    :return:
    """
    logger.info("准备连接并保存电话图片: %s" % trackId)
    if retry <= 0:
        return None
    try:
        r = requests.get(img_url, proxies=local_proxy(), timeout=8)
    except Exception as e:
        logger.error(e)
        logger.error("连接电话图片异常: %s 重试 %s" % (trackId, retry))
        return save_mobile_imgs_to_oss(img_url, retry - 1, trackId)

    # 存储oss
    logger.info("准备存储oss: %s " % trackId)
    try:
        auth = oss2.Auth('LTAIa3y58SBV0Kyn', 'yBZcBKhQTgtf4cV55ljpnNCSk1XWaI')
        bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'ocr-img')
        oss_addr = 'spider/FIVE_EIGHT/JD_SEARCH/NEW/' + str(uuid.uuid1()) + '.jpg'
        put_object = bucket.put_object(oss_addr, r)
        logger.info("%s" % put_object.resp.status)
    except Exception as e:
        logger.error(traceback.format_stack())
        return save_mobile_imgs_to_oss(img_url, retry - 1, trackId)

    return oss_addr


def parse_list_html(list_html, url, trackId, proxy_ip):
    """
    解析获取列表页面中字段
    :return: dict 下页列表页连接 ,list( dict:详情页连接-发布日期 )
                异常页面返回None , 没有职位了返回'none_jd'
    """
    if not list_html:
        logger.error("没有获取到页面%s" % trackId)
        return None

    tree = xmlh.document_fromstring(list_html)

    none_jd = tree.xpath('//*[@id="infolist"]/dl[1]/dt/text()')
    if none_jd and "没有符合条件的信息" in none_jd:
        return 'none_jd'
    title_txt = tree.xpath('/html/head/title/text()')
    if not title_txt:
        logger.error("搜索到的页面异常:%s" % trackId)
        return None
    if spider_utils.find('.*?请输入验证码.*?|.*?Denied Access Policy.*?|.*?ERROR.*?', str(title_txt[0])):
        logger.error("搜索到的页面异常:%s" % trackId)
        return None
    lis = tree.xpath('//*[@id="list_con"]/li[@class="job_item clearfix"]')

    if not lis:
        logger.info('没有jd了-- %s' % trackId)
        return 'none_jd'
    list_dis = {}
    info_list = []
    # page_num_text = tree.xpath('//div[@class="pagerout"]/div/strong/span/text()')

    now_page_num = find('.*?pn(\\d+).*?', url)
    key_set = set()
    user_ids = set([])
    for index, item in enumerate(lis):
        # print item  # 一个职位
        div = item.xpath('./div/div[@__addition="0"]')
        if not div:
            continue
        result_dist = {
            'onTopFlag': 0,
            'authentication': {},
        }
        result_dist['pageNum'] = now_page_num
        result_dist['pageIndex'] = index + 1
        link = item.xpath('./div/div/a')[0].attrib.get('href')
        redis_key = utils.find('.*?entinfo=(\d+)_.*?', link)
        if not redis_key or redis_key in key_set: #  对连接进行去重
            continue
        else:
            redis_key = 'five_eight:'+redis_key
            redis_get_link = utils.redis_get(redis_key)
            if redis_get_link:
                key_set.add(redis_key)
                continue
            else:
                utils.redis_set(redis_key, '1')
                key_set.add(redis_key)
        # print link # 拿到详情链接
        layout_list = item.xpath('./a[@class="sign"]/text()')
        layout =None
        if layout_list:
            layout = layout_list[0]
            result_dist['info_url'] = link  # 拿到详情链接
        if layout:
            if '精准' in layout:
                result_dist['jdLayoutTime'] = None
                result_dist['adTag'] = '1'
                result_dist['onTopFlag'] = 1
            elif '置顶' in layout:
                result_dist['jdLayoutTime'] = None
                result_dist['adTag'] = '2'
                result_dist['onTopFlag'] = 1
            else:
                result_dist['jdLayoutTime'] = layout
                result_dist['adTag'] = None
        else:
            result_dist['jdLayoutTime'] = None
            result_dist['adTag'] = None
        if item.xpath('.//i[@class="comp_icons mingqi"]'):
            result_dist['authentication']['58_mingqi'] = 1
        uids = item.xpath('.//input[@name="uid"]')
        if uids and uids[0].attrib.get('uid', ''):
            user_ids.add(uids[0].attrib['uid'])
            result_dist['uid'] = uids[0].attrib['uid']

        info_list.append(result_dist)

    brand = {}
    wltStats = {} 
    if user_ids:
        get_brand_headers = {
            'Accept':'*/*',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Host':'zp.service.58.com',
            'Referer':url,
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
        }
        params = {'userIds': '|'.join(user_ids)}
        get_brand_url = 'http://zp.service.58.com/api?returnType=1&action=wltStats,brand&callback=jQuery110207922296067085253_%s&params=%s&_=%s' % (str(int(time.time()*1000)), urllib.quote(json.dumps(params)), str(int(time.time()*1000)))
        get_brand_response = utils.download(url=get_brand_url, headers=get_brand_headers, proxy=proxy_ip, allow_redirects=False, is_json=False, retry_time=3)
        if not get_brand_response['code']:
            get_brand_json_list = re.findall('[^\(]*\((.*)\)[^\)]*', get_brand_response['data'])
            
            if get_brand_json_list and get_brand_json_list[0]:
                get_brand_json = json.loads(get_brand_json_list[0])
                brand = get_brand_json.get('brand', {}).get('data', {})
                wltStats = get_brand_json.get('wltStats', {}).get('data', {})

    for i in info_list:
        if i.get('uid', ''):
            if i['uid'] in brand and brand[i['uid']]:
                i['authentication']['58_renzheng'] = 1
            if i['uid'] in wltStats and wltStats[i['uid']].startswith('wlt') and wltStats[i['uid']][3:].isdigit():
                i['memberFlag'] = int(wltStats[i['uid']][3:])

    list_dis['info_list'] = info_list
    next_url = None
    if len(info_list) >= 1:  # 每页总数55
        next_url = tree.xpath('//div[@class="pagesout"]/a[@class="next"]')

    if next_url:
        list_dis['next_url'] = next_url[0].attrib.get('href')
        return list_dis
    else:
        list_dis['next_url'] = None
        return list_dis


def get_html(url, retry, track_id, proxy_ip, headers=None, allow_redirects=False):
    """
    访问连接列表页面
    :return: 获得的列表页面html 异常返回null
    """
    if not url:
        return
    if retry <= 0:
        return None
    proxy = find('.*?(\d+\.\d+\.\d+\.\d+:\d+)', proxy_ip.get("http"))
    if headers:
        result = utils.download(url=url, proxy=proxy_ip, headers=headers, allow_redirects=allow_redirects)
    else:
        result = utils.download(url=url, proxy=proxy_ip, allow_redirects=allow_redirects)

    if result['code'] != 0:
        logger.error("连接页面异常,url= %s ,重试: retry= %s" % (url, retry))
        proxy_ip.update(local_proxy())
        return get_html(url, retry - 1, track_id, proxy_ip, headers)
    elif '用户数不够' in result['data'] \
            or '在线用户数超过' in result['data'] \
            or len(result['data']) < 500:
        logger.error("代理异常,url= %s ,重试: retry= %s" % (url, retry))
        proxy_ip.update(local_proxy())
        return get_html(url, retry - 1, track_id, proxy_ip, headers)
    return [result['data'], proxy]


def info_main(baseUrl, info_list, trackId, param_dict, proxy_ip):
    """
    职位详情页面主方法
    :param info_list: list: adtag,info_url ,layout_time
    :return:
    """
    if info_list:
        for key, info in enumerate(info_list):
            info_url = info.get('info_url')
            headers = spider_utils.get_info_headers(baseUrl)
            logger.info("开始连接详情页面 %s" % info_url)
            try:
                html_info = get_html(info_url, 5, trackId, headers=headers, allow_redirects=True, proxy_ip=proxy_ip)

                if html_info:
                    logger.info("detail_html success when download: " + info_url)
                    logger.info("开始解析jd-详情 %s, %s" % (trackId, info_url))
                    parse_info_html(html_info, info, trackId, param_dict, proxy_ip)
                else:
                    logger.error("连接详情页面失败 本页第 %s 个" % (key + 1))
            except:
                logger.error("连接详情页面失败 本页第 %s 个" % (key + 1))


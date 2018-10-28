#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25


import oss2
import json
import uuid
import requests
import time
import traceback
from lxml import etree
import re
import sys
import random
from settings import project_settings
import datetime

reload(sys)
sys.setdefaultencoding("utf8")
sys.path.append("../common")
import utils


def local_proxy():
    proxy = {
        'http':
            'http://H30ZT3VT34B219PD:58A97FEF36CC1833@proxy.abuyun.com:9020',
        'https':
            'https://H30ZT3VT34B219PD:58A97FEF36CC1833@proxy.abuyun.com:9020'
    }
    return proxy


def process(task):
    logger = utils.get_logger()
    data = json.loads(task['data'][0]['executeParam'], encoding="utf8")
    result = parse_list(data)
    if result['code'] and str(result['code']) == '200':
        logger.info('任务执行成功 %s ' % data)
        return {'code': 0, 'executeResult': 'SUCCESS'}
    else:
        logger.info('任务执行失败- %s ' % data)
        return {'code': 500, 'executeResult': 'FAILURE', 'executeParam': json.dumps(result, encoding='utf8')}

    '''
    分页解析
    '''


def parse_list(data):
    logger = utils.get_logger()
    # 入口页面解析
    base_url = data['cityUrl'] + data['funcUrl']
    page_num = data['pageNum']
    result_code = 0
    if not page_num:
        page_num = 1
    flg = True
    while flg:
        logger.info('当前请求第 %s 页 ' % page_num)
        url = parse_url(base_url=base_url, page_num=page_num)
        result = download_page(url=url, method='get', need_session=True)
        proxy = result['proxy']
        if result['code'] == 0:
            content = result['data']
            session = result['session']
            if '所有职位' in content:
                # 第一次请求到正常页面，进行首页解析
                list_result = parse_list_page(page_num=page_num, list_url=url, page=content, data=data, refer=url,
                                              session=session, proxy=proxy)
                # 当前页遍历 每一条成功，如果返回True，进行翻页操作
                if list_result['status'] is True:
                    # if True:
                    # 如果存在 info_length，表示翻页请求的正文不包含列表信息，表示抓取完成
                    if 'info_length' in list_result:
                        result_code = 200
                        break
                    else:
                        page_num += 1
                else:
                    logger.info('列表遍历失败 %s ' % url)
                    # 当前页面遍历列表失败，返回500
                    flg = False
                    result_code = 500
                    break
            else:
                logger.info('当前返回的是错误页面 %s ' % url)
                flg = False
                result_code = 200
                break
        else:
            # 第一次访问失败，返回500
            logger.info('首页访问失败 %s ' % url)
            result_code = 500
            flg = False
            break

    data['pageNum'] = page_num
    data['code'] = result_code
    return data

    '''
    请求列表页面
    '''


def parse_list_page(page_num=None, page=None, list_url=None, data=None, refer=None, session=None, proxy=None):
    logger = utils.get_logger()
    logger.info('当前解析第 %s 页面列表 %s ' % (page_num, list_url))
    result = {'status': False}
    if '没有找到相关的信息' in page:
        logger.info('没有符合条件的职位 %s' % json.dumps(data))
        result['status'] = True
        result['info_length'] = 0
    else:
        try:
            document = etree.HTML(page.decode('utf-8'))
            dl_list = document.xpath('//dl[@class="list-noimg job-list clearfix new-dl"]')
            if dl_list and len(dl_list) > 0:
                logger.info('当前页有 %s 条数据' % len(dl_list))
                page_index = 1
                for dl in dl_list:
                    logger.info("解析第 %s 条" % page_index)
                    puid = re.search('puid="(\\d+)"', etree.tostring(dl, encoding='utf-8'))
                    if puid:
                        puid_ = puid.group(1)
                        if not puid_:
                            continue
                        key = 'ganji_' + puid_
                        if utils.redis_get(key):
                            logger.info('不进行重复抓取 %s %s ' % (key, page_index))
                            continue
                        else:
                            logger.info('进行抓取 %s %s ' % (key, page_index))
                            utils.redis_set(key, 1)
                    page_index += 1
                    jd_layout_time = dl.xpath('dd[@class="pub-time"]/span/text()')[0]
                    logger.info('发布时间： %s' % jd_layout_time)
                    # 获取前天
                    time_ = datetime.datetime.now() - datetime.timedelta(days=2)
                    time_str_ = time_.strftime('%m') + '-' + time_.strftime('%d')
                    if time_str_ in jd_layout_time:
                        logger.info(' %s 当前行 发布时间为 %s ，或者更前，程序退出 ' % (refer, time_str_))
                        result['info_length'] = 0
                        result['status'] = True
                        break
                    detail_url = dl.xpath('dt/a/@href')
                    logger.info('详情页面URL为：%s' % detail_url)
                    if detail_url:
                        pay_data = {}
                        # 赶集帮帮
                        bb_count = dl.xpath('.//span[@class="ico-bang-new"]/text()')
                        if bb_count:
                            pay_data['memberFlag'] = bb_count[0]
                        # 企业邮箱认证
                        ganji_email = dl.xpath('.//span[@class="s-mailbox01"]/text()')
                        if ganji_email:
                            pay_data['ganji_email'] = 1
                        # 热招职位
                        ganji_hot = dl.xpath('.//span[@class="ico-hot"]/text()')
                        if ganji_hot:
                            pay_data['hotFlag'] = 1
                        # 驴招
                        ganji_lv = dl.xpath('.//span[@class="icon-safety"]')
                        if ganji_lv:
                            pay_data['ganji_lv'] = 1
                        # 置顶
                        ganji_top = dl.xpath(
                            './/span[contains("class","new-top-icon") or contains("class","ico-stick-yellow")]')
                        if ganji_top:
                            pay_data['onTopFlag'] = 1
                        # 品牌
                        ganji_branch = dl.xpath('.//span[@class="icon-pp"]')
                        if ganji_branch:
                            pay_data['ganji_branch'] = 1
                        logger.info('付费的数据 %s ' % pay_data)
                        parse_detail_page(detail_url=detail_url[0], list_url=list_url, data=data,
                                          jd_layout_time=jd_layout_time,
                                          page_num=page_num,
                                          page_index=page_index, refer=refer, session=session, proxy=proxy,
                                          pay_data=pay_data)
            else:
                logger.error('没有解析到 new-dl 元素 %s' % list_url)
                result['info_length'] = 0
            result['status'] = True
        except Exception as e:
            logger.error('parse_list_page 列表页解析异常 %s %s ' % (list_url, traceback.format_exc()))
            result['status'] = False
    logger.info('parse_list_page %s 第 %s 页 执行完毕 %s' % (list_url, page_num, result))
    return result


'''
解析详情页面
'''


def parse_detail_page(detail_url=None, list_url=None, data=None, jd_layout_time=None, page_num=None, page_index=None,
                      refer=None, session=None, proxy=None, pay_data=None):
    logger = utils.get_logger()
    # page = get_page(detail_url, refer=refer)
    logger.info('parse_detail_page当前抓取 %s 第 %s 页 第 %s 行 ' % (list_url, page_num, page_index))
    headers = {
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0(Windows NT 10.0; WOW64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        'Accept': 'text/html, application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Referer': refer,
    }
    page = download_page(url=detail_url, method='get', header=headers, proxy=proxy, session=session, need_session=True)
    if page['code'] == 0:
        new_session = page['session']
        content = page['data']
        if '当前职位不再继续招聘' in content:
            logger.info('当前职位不再继续招聘 %s ' % detail_url)
            return
        if '用户数不够，请与遥志软件联系购买' in content:
            logger.info('详情页面显示“用户数不够，请与遥志软件联系购买”，不入库 %s ' % detail_url)
            return
        if '本次访问需要输入验证码' in content:
            logger.info('详情页面显示 “本次访问需要输入验证码”，不入库 %s ' % detail_url)
            return
        document = etree.HTML(content.decode('utf-8'))
        phone_url = parse_phone(document=document, data=data, refer=detail_url)
        logger.info('保存的电话号码图片地址：%s' % phone_url)
        company_img = parse_company_img(document=document)
        logger.info('公司图片 %s ' % len(company_img))
        post_data = parse_post_count(list_url=list_url, detail_url=detail_url, detail_page=content,
                                     session=new_session, proxy=proxy)
        post_data['cityUrl'] = data['cityUrl']
        post_data['cityName'] = data['cityName']
        post_data['funcUrl'] = data['funcUrl']
        post_data['funcName'] = data['funcName']
        post_data['pageNum'] = page_num

        save_db(page_content=content, proxy=proxy, city_name=data['cityName'], phone_url=phone_url,
                jd_layout_time=jd_layout_time,
                page_url=detail_url, company_img=company_img, page_num=page_num, page_index=page_index,
                post_data=post_data, pay_data=pay_data)
    else:
        logger.error('parse_detail_page 详情页面访问失败：%s ' % detail_url)


'''
    解析在招职位跟已收简历数
    :return: 
'''


def parse_post_count(list_url=None, detail_url=None, detail_page=None, session=None, proxy=None):
    logger = utils.get_logger()
    company_id = re.search('companyId  = \'(.*?)\';', detail_page)
    user_id = re.search('hq_userId = \'(.*?)\';', detail_page)
    hash_ = re.search('window\.PAGE_CONFIG\.__hash__ = \'(.*?)\';', detail_page)

    if not company_id or not user_id or not hash_:
        logger.error('详情页面 userid 跟 companyid 解析失败')
        return {}
    origin = re.search('(http[\\s\\S]*?com)', list_url).group(1)
    host = re.search('http://([\\s\\S]*?com)', list_url).group(1)
    post_url = origin + '/ajax.php?_pdt=zhaopin&module=getHighQualityCompanyInfo'
    company_id = company_id.group(1)
    user_id = user_id.group(1)
    hash_ = hash_.group(1)
    params = {'company_id': company_id, 'user_id': user_id, '__hash__': hash_}
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": detail_url,
        "Origin": origin,
        "Host": host,
    }
    try:
        result = download_page(url=post_url, method='post', header=headers, data=params, session=session, proxy=proxy)
        if result['code'] == 0:
            content = result['data']
            post_count = re.search(',"postsCount":(\\d+),', content)
            resume_count = re.search(',"resumeCount":(\\d+),', content)
            call_num = re.search('"callNum":(\\d+)', content)
            if post_count:
                post_count = post_count.group(1)
            if resume_count:
                resume_count = resume_count.group(1)
            if call_num:
                call_num = call_num.group(1)
            logger.info('在招职位跟已收简历数 请求成功 %s' % post_url)
            return {'post_count': post_count, 'resume_count': resume_count, 'call_num': call_num}
    except Exception as e:
        logger.error('parse_post_count 出错 %s %s ' % (post_url, traceback.format_exc()))
    return {}

    '''
    解析公司图片   
    :param content: 
    :param datas: 
    :return: 
    '''


def parse_company_img(document):
    logger = utils.get_logger()
    try:
        img_div = document.xpath('//div[@class="part3"]')
        if img_div:
            img_div_content = etree.tostring(img_div[0], encoding='utf-8').replace('\\', '')
            imgs = re.search('data-imgs="([\\s\\S]*?)"/>', img_div_content)
            if imgs:
                imgStr = str(imgs.group(1)).replace('&quot;', '').replace('{', '').replace('}', '').replace('[',
                                                                                                            '').replace(
                    ']',
                    '').replace(
                    'sImgs', '').replace('mImgs', '').replace('bImgs', '')
                return imgStr
    except Exception as e:
        logger.error('parse_company_img 出错了 %s ' % traceback.format_exc())
    return ''

    '''
    解析电话号码
    :param page: 
    :param data: 
    :return: 
    '''


def parse_phone(document=None, data=None, refer=None):
    logger = utils.get_logger()
    phone_elements = document.xpath('//li[@class="fl w-auto topshow mt-5"]')
    if phone_elements:
        phone_imgs = phone_elements[0].xpath('span[@style="display:none"]/img/@src')
        logger.info('parse_phone 解析到电话号码的个数：%s' % len(phone_imgs))
        img_urls = ''
        for items in phone_imgs:
            img_url = data['cityUrl'] + items
            current_img_oss_save_path = save_mobile_imgs_to_oss(img_url=img_url, retry=5, refer=refer)
            if current_img_oss_save_path:
                img_urls += current_img_oss_save_path + ";"
        return img_urls
    else:
        return ''


"""
  连接获取电话图片保存oss
  :return:
  """


def save_mobile_imgs_to_oss(img_url=None, retry=None, refer=None, trackid=None, city_url=None):
    logger = utils.get_logger()
    logger.info("准备连接并保存电话图片:%s" % img_url)
    if not img_url or retry <= 0:
        return None
    try:
        if city_url:
            city_url = str(city_url).replace('/', '').replace('http', '').replace(':', '')
        input = requests.get(url=img_url, headers={
            "Referer": refer,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            "Accept": "*/*",
            'Host': city_url
        }, proxies=local_proxy(), timeout=6)
        logger.info('success when download %s ' % img_url)
        # 存储oss
        logger.error("准备存储oss: %s " % trackid)
        auth = oss2.Auth('LTAIa3y58SBV0Kyn', 'yBZcBKhQTgtf4cV55ljpnNCSk1XWaI')
        bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'ocr-img')
        # oss_api = OssAPI('http://oss-cn-beijing.aliyuncs.com', 'LTAIa3y58SBV0Kyn', 'yBZcBKhQTgtf4cV55ljpnNCSk1XWaI')
        oss_addr = 'spider/GJ_HR/JD_SEARCH/NEW/' + str(uuid.uuid1()) + '.jpg'
        bucket.put_object(oss_addr, input)
        return oss_addr
    except Exception as e:
        logger.error('error when download %s ' % img_url)
        logger.error("连接电话图片异常: %s 重试 %s 异常 %s" % (trackid, retry, traceback.format_exc()))
        return save_mobile_imgs_to_oss(img_url=img_url, retry=retry - 1, trackid=trackid, refer=refer,
                                       city_url=city_url)

    '''
    保存数据到数据库    
    :return: 
    '''


def save_db(page_content=None, proxy=None, city_name=None, phone_url=None, jd_layout_time=None, page_url=None,
            company_img=None, page_num=None,
            page_index=None, post_data=None, pay_data=None):
    logger = utils.get_logger()
    try:
        # print post_data
        city_url = post_data['cityUrl']
        func_url = post_data['funcUrl']
        # city url跟funcurl 不入raw表
        post_data['cityUrl'] = ''
        post_data['funcUrl'] = ''
        page_content = utils.remove_emoji(page_content).decode('utf8', 'ignore')
        pay_data['content'] = page_content
        track_id = str(uuid.uuid4())
        sql = 'insert into jd_raw(trackId,source,content,createTime,createBy,ip,pageNum,pageIndex,pageUrl,jobCity,jdLayoutTime,ocrImg,searchConditions)values(%s,"GJ_HR",%s,now(),"python",%s,%s,%s,%s,%s,%s,%s,%s)'
        # search_conditions = {'post_count': post_data['post_count'], 'resume_count': post_data['resume_count'],'':post_data}
        sql_val = [track_id, json.dumps(pay_data, ensure_ascii=False), proxy["http"].replace("http://", ""), page_num,
                   page_index, page_url,
                   city_name, jd_layout_time, phone_url, json.dumps(post_data, ensure_ascii=False)]
        post_data['cityUrl'] = city_url
        post_data['funcUrl'] = func_url
        kafka_data = {
            "channelType": "WEB",
            "content": {
                "trackId": track_id,
                "content": json.dumps(pay_data, ensure_ascii=False),
                "id": '',
                "createTime": int(time.time() * 1000),
                "createBy": "python",
                "ip": proxy["http"].replace("http://", ""),
                "ocrImg": phone_url,
                "jdLayoutTime": jd_layout_time,
                "pageUrl": page_url,
                "pageNum": page_num,
                "pageIndex": page_index,
                "companyImgs": company_img,
                "source": "GJ_HR",
                "jobCity": city_name,
                "searchConditions": json.dumps(post_data, ensure_ascii=False)
            },
            "interfaceType": "PARSE",
            "resourceDataType": "RAW",
            "resourceType": "JD_SEARCH",
            'protocolType': 'HTTP',
            "source": "GJ_HR",
            "trackId": track_id,
        }
        flg = utils.save_data(sql, sql_val, kafka_data)
        logger.info('入库成功 %s ', str(flg))
    except Exception as e:
        logger.error(traceback.format_exc())


def parse_cookie(cookies):
    if cookies:
        cookie_str = ''
        for cookie in cookies:
            cookie_str = cookie_str + cookie + "=" + cookies.get(cookie) + ";"
        return cookie_str
    return ''


def parse_url(base_url, page_num):
    logger = utils.get_logger()
    url = None
    # u0表示不限 u1表示最近三天,默认取最小搜索时间3天
    u = 1
    if project_settings.get('U'):
        u = project_settings.get("U")
    if base_url and page_num:
        url = base_url + '/u' + str(u) + 'o' + str(page_num)
        logger.info('当前分页的URL为：%s' % url)
    return url


def download_page(url=None, method=None, header=None, proxy=None, data=None, session=None, need_session=False):
    logger = utils.get_logger()
    if not proxy:
        proxy = local_proxy()
    for x in xrange(0, 5):
        result = utils.download(url=url, headers=header, data=data, method=method, need_session=need_session,
                                session=session, proxy=proxy,
                                allow_redirects=True, retry_time=1)
        if result['code'] == 0:
            logger.info('success when download %s ' % url)
            break
        else:
            proxy = local_proxy()
            result['code'] = 500
        time.sleep(1)
    result['proxy'] = proxy
    return result


if __name__ == '__main__':
    utils.set_setting([])
    logger = utils.get_logger()
    task = {"pageNum": 1, "funcUrl": "zpruanjiangongchengshi", "funcName": "软件工程师", "cityName": "北京",
            "cityUrl": "http://bj.ganji.com/"}
    parse_list(data=task)

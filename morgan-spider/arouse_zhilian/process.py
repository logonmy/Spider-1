#!coding:utf8

# version: python2.7
# author: yanjialei
# time: 2017.4.25


# import ganji_jd
import json
import uuid
import requests
import datetime
import time
import random
import traceback
from lxml import etree
import re
import sys
import settings
import os

reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('../common')

import sys
import utils

logger = utils.get_logger()

page_size = 20
max_page = 50


def process(task):
    data = json.loads(task['data'][0]['executeParam'], encoding="utf-8")
    # result = {'code': 0}
    result = search(data)
    if result['code'] and '0' == result['code']:
        return {'code': 0, 'executeResult': 'SUCCESS'}
    else:
        return {'code': 0, 'executeResult': 'FAILURE', 'executeParam': json.dumps(result, encoding='utf8')}


def load_account():
    # account_sql = 'select userName,password,cookie FROM morgan_manager.account_bean WHERE source="ZHI_LIAN" AND useType="RESUME_FETCH" AND valid=1 AND cookieValid=1'
    # result = utils.query_by_sql(account_sql)
    # if result:
    #     logger.info('找到 %s 个账户  ' % len(result))
    result = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    data = utils.download(url=settings.project_settings['loadCookieUrl'], headers=headers, method='GET')
    rs = json.loads(data['data'], encoding='utf-8')
    if rs and 'SUCCESS' in rs['msg']:
        for r in rs['data']:
            result.append({'userName': r['userName'], 'passsowrd': r['password'], 'cookie': r['cookie'],
                           'accountName': r['accountName']})
    return result


def get_page(url, header, proxy=None):
    logger.info('get_page url %s' % url)
    for x in xrange(4):
        try:
            if not proxy:
                proxy = utils.get_proxy()
            logger.info('get_page[use proxy %s]' % proxy)
            session = requests.session()
            content = session.get(url=url, headers=header, proxies=proxy, timeout=5).content
            if content:
                logger.info('[the page use proxy %s] ' % proxy)
                return {'content': content, 'proxy': proxy}
            else:
                logger.info('[request returns null page %s]' % url)

        except Exception as e:
            logger.error(str(traceback.format_exc()))
            proxy = utils.get_proxy()
    return None


def post_page(url, header, data=None, proxy=None):
    logger.info('get_page url %s' % url)
    for x in xrange(4):
        try:
            if not proxy:
                proxy = utils.get_proxy()
            logger.info('get_page[use proxy %s]' % proxy)
            session = requests.session()
            content = session.post(url=url, headers=header, data=data, proxies=proxy, timeout=5).content
            if content:
                logger.info('[the page use proxy %s] ' % proxy)
                return {'content': content, 'proxy': proxy}
            else:
                logger.info('[request returns null page %s]' % url)

        except Exception as e:
            logger.error(str(traceback.format_exc()))
            proxy = utils.get_proxy()
    return None


accounts = load_account()


def get_cookie(index=None):
    if not accounts:
        logger.error('没有可以使用的账户')
        return None

    if not index:
        index = 0
    cookie = accounts[index]['cookie']
    # logger.info('use account %s:%s' % (accounts[index][0], accounts[index][1]))
    #  + ';Home_ResultForCustom_orderBy=DATE_MODIFIED%2C1; Home_ResultForCustom_pageSize=60;SearchHead_Erd=rd;SearchHistory_StrategyId_1=%2fHome%2fResultForCustom%3fSF_1_1_2%3d045%26SF_1_1_7%3d1%252c9%26SF_1_1_5%3d4%252c16%26SF_1_1_18%3d530%26orderBy%3dDATE_MODIFIED%252c1%26pageSize%3d60%26SF_1_1_27%3d0%26exclude%3d1; '
    # cookie_list = []
    # for k in cookie_json:
    #     cookie_list.append(k + "=" + cookie_json.get(k))
    # cookie = ";".join(cookie_list).decode('utf8')
    # cookie = 'pageReferrInSession=http%3A//rd2.zhaopin.com/s/homepage.asp; FSSBBIl1UgzbN7N80S=KKlR3OeVzm8SK_A.WQVn8qklS.PpBLgwtGAup80ZUIPEwX.qMM4kGGFSl1pnWK7t; FSSBBIl1UgzbN7N80T=19BLN1hQ.fO.sMsIII2DWuLVv57jjAF7IiQTx67mrE4tmLZTYHEUcIji7vYJJpOWhoGBd3JxiqhzQhB.GYP57M1Phb90DIIGg7jIDsU6.gq5SudVIR_0IBV2HCKIz00Wuz5u_fTXU75mqRHnQhqHX4OxJ_45fLaIPEduzoWNxaA4x4DBJy4nJEiV3dzWfaG2nSvZ3VElfMWnZ0LxHzK.HgsM9A7WP26CzdO4X6D3.Ws1MV0WvcCuPtnU4EQruiIvHkRkMEwvsHkn2ZQj9.CuCCS5n0_YLED85q6sQEii._X_crL9BCOvvwYMn5PBxGxiYEWA; Home_1_CustomizeFieldList=2%3b3%3b7%3b4%3b5%3b6%3b18%3b8; dywez=95841923.1494329499.1.1.dywecsr=(direct)|dyweccn=(direct)|dywecmd=(none)|dywectr=undefined; urlfrom=121126445; urlfrom2=121126445; adfcid=none; adfcid2=none; adfbid=0; adfbid2=0; JsOrglogin=2073713048; at=8467db2187df4a32a1e7f4e7225599f7; Token=8467db2187df4a32a1e7f4e7225599f7; rt=8146b2a622a544dda8707c51bdf052ff; uiioit=3D672038046A52644E64416F5A6757380E6A52644F64426F536726387D6A59644364486F586752380F6A53644364486F53677; xychkcontr=48066748%2c0; lastchannelurl=https%3A//passport.zhaopin.com/org/login%3FDYWE%3D1489037787973.344544.1489037788.1489037788.1; JsNewlogin=691237682; RDpUserInfo=; isNewUser=1; cgmark=2; NewPinLoginInfo=; NewPinUserInfo=; utype=1; ihrtkn=; RDsUserInfo=3D753D6857645E7540685B645A754A685D645E75416858645375356824645575006801640A751A685E64507549685C645E754E685E64507542683F6426754468BBF453753B682E6455754D68526458754F685C645F754D68526453753B68246455756E3BC62AD110233B2EE92B2498270504B90CF90A630338E31539923753752D682764557542682F642575446859645B754F685964587540685C6458754E685C64287508681B6446751A6805640575426839643C7544685B64537538683E6455754C684764517559685B64517543685964597542682E642C7544685E64507549685C645E754E685E64507542682E64267544687D37C43BC00D30372CF83A398B2B0715A811EA06611229FE0635902642682664257544685A64587549685B6453753A682E6455754C685964587542683F643C7544685B645875486851642B75386857642B753A685E64507549685C645E754E685E6450754F6851642C75386857642B753A685E64507549685C645E754E685E6450754F6851642C753A685764587542683964217544685964537530683A6455754B685E645A7557685B64597548685164297535685764587542683; ensurew58=1; SearchHead_Erd=rd; __utma=269921210.1170401875.1494330097.1494330097.1494330097.1; __utmb=269921210.1.10.1494330097; __utmc=269921210; __utmz=269921210.1494330097.1.1.utmcsr=rd2.zhaopin.com|utmccn=(referral)|utmcmd=referral|utmcct=/s/homepage.asp; SearchHistory_StrategyId_1=%2fHome%2fResultForCustom%3fSF_1_1_2%3d045%26SF_1_1_7%3d1%252c9%26SF_1_1_5%3d4%252c16%26SF_1_1_18%3d530%26orderBy%3dDATE_MODIFIED%252c1%26pageSize%3d60%26SF_1_1_27%3d0%26exclude%3d1; Home_ResultForCustom_orderBy=DATE_MODIFIED%2C1; dywea=95841923.3133438666882913300.1494329499.1494329499.1494329499.1; dywec=95841923; dyweb=95841923.9.9.1494329514114; Hm_lvt_38ba284938d5eddca645bb5e02a02006=1493973477,1494221927,1494313507,1494330097; Hm_lpvt_38ba284938d5eddca645bb5e02a02006=1494330253; Home_ResultForCustom_pageSize=60'
    # cookie = 'FSSBBIl1UgzbN7N80S=KKlR3OeVzm8SK_A.WQVn8qklS.PpBLgwtGAup80ZUIPEwX.qMM4kGGFSl1pnWK7t; FSSBBIl1UgzbN7N80T=19BLN1hQ.fO.sMsIII2DWuLVv57jjAF7IiQTx67mrE4tmLZTYHEUcIji7vYJJpOWhoGBd3JxiqhzQhB.GYP57M1Phb90DIIGg7jIDsU6.gq5SudVIR_0IBV2HCKIz00Wuz5u_fTXU75mqRHnQhqHX4OxJ_45fLaIPEduzoWNxaA4x4DBJy4nJEiV3dzWfaG2nSvZ3VElfMWnZ0LxHzK.HgsM9A7WP26CzdO4X6D3.Ws1MV0WvcCuPtnU4EQruiIvHkRkMEwvsHkn2ZQj9.CuCCS5n0_YLED85q6sQEii._X_crL9BCOvvwYMn5PBxGxiYEWA; Home_1_CustomizeFieldList=2%3b3%3b7%3b4%3b5%3b6%3b18%3b8; Home_ResultForCustom_pageSize=60; dywez=95841923.1494335004.2.2.dywecsr=rdsearch.zhaopin.com|dyweccn=(referral)|dywecmd=referral|dywectr=undefined|dywecct=/home/redirecttord/vm0xdfrjgqt6oe2ifqlwyq_1_1; Home_ResultForCustom_isOpen=true; __zpWAM=1494407663353.330560.1494407663.1494407663.1; urlfrom=121126445; urlfrom2=121126445; adfcid=none; adfcid2=none; adfbid=0; adfbid2=0; JsOrglogin=2064034493; at=6d63a4c5accc4272998648a743d42a85; Token=6d63a4c5accc4272998648a743d42a85; rt=0d568c09087f46c39c54ff115228f0bd; uiioit=2264202C55795C6900374D79586B4664552C5C7953690F374E792A6B3364592C5C795269093744795D6B47645D2C507951695; xychkcontr=48115098%2c0; lastchannelurl=https%3A//passport.zhaopin.com/org/login%3FDYWE%3D1489037787973.344544.1489037788.1489037788.1; JsNewlogin=688011497; cgmark=2; NewPinLoginInfo=; NewPinUserInfo=; RDpUserInfo=; isNewUser=1; ihrtkn=; utype=688011497; ensurew58=1; getMessageCookie=1; RDsUserInfo=3D753D6857645E7541685264587548685B645C7540685D6453753568246455751A68076411751A68586453752C68246455752B683964683B433B516426753768576453753B682E6455754D685264597548685F6458754068526453753B68246455756E3BC62A630F7BEBE317E01AA811EA06611229FE0635902642683E64257544685B642E7542682F64257544680864187514682A64127511680B640775096803640675576809640775146844640B75176851643B752D685764597542682B643C7544685F64457548685F6448754D68506459754C6851642C753D68576459754868596459754D685C645D7548685A6453753D6824645575721268E7E106F1075864537535682764557549685A64587548685A6458754968596453753A682E6455754C685964587542682B64247544685A6453752C682B645575426829642975446829642B754D685264597548685F645875406852645A7542682E642975446829642B754D685264597548685F645875406852645A753D68536458754B685F64587549685A645A7549685A64587542682E642B7544685A6453752A68236455754A6851642175296857645A754D685864467548685B64587542683F643C7544685B6458754A6851643; SearchHead_Erd=rd; dywea=95841923.3133438666882913300.1494329499.1494493380.1494790878.6; dywec=95841923; dyweb=95841923.18.9.1494790903245; __utmt=1; __utma=269921210.1170401875.1494330097.1494790879.1494792952.6; __utmb=269921210.1.10.1494792952; __utmc=269921210; __utmz=269921210.1494792952.6.2.utmcsr=rd2.zhaopin.com|utmccn=(referral)|utmcmd=referral|utmcct=/s/homepage.asp; Hm_lvt_38ba284938d5eddca645bb5e02a02006=1494330097,1494381979,1494407649,1494792952; Hm_lpvt_38ba284938d5eddca645bb5e02a02006=1494792952; Home_ResultForCustom_orderBy=DATE_MODIFIED%2C1; Home_ResultForCustom_searchFrom=custom'
    return cookie


def invalid_cookie(cookie_index):
    global accounts
    if not accounts:
        return None
    acc = accounts[cookie_index]
    user_name = acc[0]
    password = acc[1]
    result = utils.download(
        url=settings.project_settings['invalidUrl'] + 'userName=' + user_name + "&password=" + password, )
    # print result
    result_json = json.loads(result['data'], encoding='utf8')
    # print result_json
    if 'SUCCESS' == result_json['msg']:
        logger.info('cookie失效成功')
    else:
        logger.error('cookie试失效失败 %s \n %s ' % (user_name, result_json['msg']))
        # accounts = load_account()
        # logger.info('重新加载账户完毕')


def search(data):
    region_code = data['cityCode']
    job_code = data['funcCode']
    page_num = data['pageNum']
    # executeParam = {'cityCode': region_code, 'funcCode': job_code, 'pageNum': page_num}
    # result = {
    #     'code', 500
    # }
    # date_time = data['deadline']
    # 直接搜索60条
    # SF_1_1_8=20%2C30 年龄 20-30
    # pagIndex= 第几页
    # SF_1_1_5=5%2C16 大专以上
    cookie_index = 0
    cookie = get_cookie(cookie_index)
    if not cookie:
        return {'code': 500, 'msg': 'no cookie to use'}
    url = 'http://rdsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_5=5%2C16&exclude=1&orderBy=DATE_MODIFIED,1&' \
          'SF_1_1_27=0&SF_1_1_7=1%2C9&SF_1_1_8=20%2C30&SF_1_1_18=' + region_code + '&SF_1_1_2=' + job_code + \
          '&pageSize=60'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        "cache-control": "no-cache",
        "Host": "rdsearch.zhaopin.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": url,
        "Cookie": cookie
    }
    page = get_page(url, header=headers)
    flg = parse_list_page(cookie_index=cookie_index, page=page, page_num=page_num, referer=url)
    if flg and 'success' == flg['msg']:
        flg_s = True
        while True:
            tree = etree.HTML(page['content'])
            next_page_url = tree.xpath('//div[@class="bottom-page"]/a[@class="rd-page-lefticon right-icon"]/@href')[0]
            proxy = page['proxy']
            cookie_index = flg['cookieIndex']
            if cookie_index == len(accounts):
                logger.info('已经遍历到最大账户数，停止抓取')
                flg_s = True
                break
            if not next_page_url:
                logger.error('没有解析到详情页面URL')
                flg_s = True
                break
            else:
                next_page_url_d = 'http://rdsearch.zhaopin.com/' + next_page_url
                page = get_page(url=next_page_url_d, header={
                    "cache-control": "no-cache",
                    "Host": "rdsearch.zhaopin.com",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Referer": url,
                    "Cookie": cookie,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
                }, proxy=proxy)
                flg = parse_list_page(cookie_index=cookie_index, page=page, page_num=page_num, referer=next_page_url_d)
                if not flg:
                    logger.error('列表访问异常 \n %s %s %s' % (cookie_index, page_num, next_page_url_d))
                    # executeParam['pageNum'] = page_num
                    data['pageNum'] = page_num
                    flg_s = False
                    break
                    # 测试代码
                    # if page_num == 2:
                    #     flg_s = True
                    #     break;
        if flg_s:
            # result = {'code': 0}
            data['code'] = '0'
        else:
            data['code'] = '500'
    else:
        data['code'] = '500'
        data['pageNum'] = flg['pageNum']
    # result['executeParam'] = json.dumps(executeParam, encoding='utf8')
    # result['deadline'] = int(time.mktime(time.strptime(date_time, '%Y-%m-%d %H:%M:%S'))) * 1000
    return data


def parse_list_page(cookie_index, page, page_num, referer):
    cookie = get_cookie(cookie_index)
    if not cookie:
        logger.error('no cookie to use')
        return {'msg': 'failed', 'cookieIndex': cookie_index, 'pageNum': page_num}
    if page and cookie:
        content = page['content']
        if content.find('根据关键词搜索简历结果') != -1:
            proxy = page['proxy']
            tree = etree.HTML(content)
            form = tree.xpath('//form[@name="frmResult"]')
            raws = form[0].xpath('//tr[@valign="middle"]')
            if raws:
                for x in xrange(0, 60):
                    if page_num == 50:
                        cookie_index += 1
                        cookie = get_cookie(cookie_index)
                        page_num = 0
                    time.sleep(2)
                    logger.info('睡眠结束 %s ' % x)
                    raw = raws[x]
                    next_page_url = raw.xpath('td/a/@href')[0]
                    if not str(next_page_url).startswith('http'):
                        next_page_url = 'http:' + next_page_url
                    resume_update_time = raw.xpath('td[last()]/text()')[0]
                    t = raw.xpath('td/a/@t')[0]
                    k = raw.xpath('td/a/@k')[0]
                    rg = raw.xpath('td/a/@rg')[0]
                    select_unique_id = re.search(
                        '<input type="hidden" name="select_unique_id" value="([\\s\\S]*?)"/>',
                        etree.tostring(form[0])).group(1)
                    selectedResumeList = re.search(
                        '<input type="hidden" name="selectedResumeList" value="([\\s\\S]*?)"/>',
                        etree.tostring(form[0])).group(
                        1)
                    resumeName = re.search('<input type="hidden" name="resumeName" value="([\\s\\S]*?)"/>',
                                           etree.tostring(form[0])).group(1)
                    resumeUrl = re.search('<input type="hidden" name="resumeUrl" value="([\\s\\S]*?)"/>',
                                          etree.tostring(form[0])).group(1)
                    chkid = re.search('<input type="hidden" name="chkid" value="([\\s\\S]*?)"/>',
                                      etree.tostring(form[0])).group(1)
                    searchKeyword = re.search('<input type="hidden" name="searchKeyword" value="([\\s\\S]*?)"/>',
                                              etree.tostring(form[0])).group(1)
                    schoolName = re.search('<input type="hidden" name="schoolName" value="([\\s\\S]*?)"/>',
                                           etree.tostring(form[0])).group(1)
                    companyName = re.search('<input type="hidden" name="companyName" value="([\\s\\S]*?)"/>',
                                            etree.tostring(form[0])).group(1)
                    post_data = {
                        "select_unique_id": select_unique_id,
                        "selectedResumeList": selectedResumeList,
                        "resumeName": resumeName,
                        "resumeUrl": resumeUrl,
                        "chkid": chkid,
                        "searchKeyword": searchKeyword,
                        "schoolName": schoolName,
                        "companyName": companyName,
                        "t": t,
                        "k": k,
                        "rg": rg,
                    }
                    flg = parse_detail_page(data=post_data, update_time=resume_update_time, cookie=cookie,
                                            referer=referer,
                                            next_page_url=next_page_url, proxy=proxy, cookie_index=cookie_index)
                    logger.info('访问详情页面返回信息： %s' % flg)
                    # 测试代码
                    # if page_num == 2:
                    #     return {'msg': 'success', 'cookieIndex': cookie_index, 'pageNum': page_num}
                    if flg:
                        page_num += 1
                    else:
                        return {'pageNum': page_num, 'msg': 'failed', 'cookieIndex': cookie_index}
                return {'msg': 'success', 'cookieIndex': cookie_index, 'pageNum': page_num}
        else:
            logger.error('没有找到搜索结果 \n %s ' % content)
            invalid_cookie(cookie_index)
    else:
        logger.error('列表页面访问返回 异常 ')
        invalid_cookie(cookie_index)
    return {'msg': 'failed', 'cookieIndex': cookie_index, 'pageNum': page_num}


def parse_detail_page(data, update_time, cookie, referer, next_page_url, proxy, cookie_index):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        "Cache-Control": "max-age=0",
        "Host": "rdsearch.zhaopin.com",
        "Origin": "http://rdsearch.zhaopin.com",
        "Referer": referer,
        "Cookie": cookie,
    }
    print 'first post data \n %s \n %s \n %s' % (next_page_url, data, referer)
    post_result = post_page(url=next_page_url, header=headers, data=data, proxy=proxy)
    if post_result:
        content = post_result['content']
        redirect_url = re.search('document.frmRedirectToRd.action = "([\\s\\S]*?)"', content)
        if redirect_url:
            redirect_url_get = redirect_url.group(1)
            if not str(redirect_url_get).startswith('http'):
                redirect_url_get = 'http:' + redirect_url_get
            proxy = post_result['proxy']
            key_word = re.search('<input type="hidden" name="searchKeyword" value="(.*?)" />', content).group(1)
            post_result = post_page(redirect_url_get, header={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                "Cache-Control": "max-age=0",
                "Host": "rd.zhaopin.com",
                "Origin": "http://rdsearch.zhaopin.com",
                "Referer": next_page_url,
                "Cookie": cookie,
            }, data={
                "searchKeyword": key_word
            }, proxy=proxy)
            if post_result:
                page = post_result['content']
                if '保存到我的电脑' in page or '转发简历到邮箱' in page:
                    return save_db(page=page, resume_udpate_time=update_time, proxy=post_result['proxy'])
                elif '链接失效' in page:
                    logger.error('页面返回 链接失效 %s' % next_page_url)
                    invalid_cookie(cookie_index=cookie_index)
                    return True
                else:
                    f = file('zhilian_arrouse_detail_error.txt', 'a+')
                    f.write(page + '\n')
                    f.close()
                    logger.info('错误页面保存成功')
                    logger.error('重定向页面提交请求错误  %s \n %s' % (next_page_url, page))
                    invalid_cookie(cookie_index=cookie_index)
    else:
        logger.error('没有找到重定向url %s ' % post_result)
    return False


def save_db(page, resume_udpate_time, proxy):
    trackId = str(uuid.uuid4())
    sql = 'insert into spider_search.resume_raw(source,content,createTime,createBy,trackId,resumeUpdateTime)values("ZHI_LIAN",%s,now(),"python",%s,%s)'
    sql_val = [page, trackId,
               resume_udpate_time]
    kafka_data = {
        "channelType": "WEB",
        "content": {
            "content": page.encode("utf8"),
            "id": '',
            "createBy": "python",
            "createTime": int(time.time() * 1000),
            "ip": proxy,
            "resumeUpdateTime": resume_udpate_time,
            "source": "ZHI_LIAN",
            "trackId": trackId,
        },
        "interfaceType": "PARSE",
        "resourceDataType": "RAW",
        "resourceType": "RESUME_SEARCH",
        'protocolType': 'HTTP',
        "source": "ZHI_LIAN",
        "trackId": trackId,
    }
    flg = utils.save_data(sql, sql_val, kafka_data)
    logger.info('数据库保存完毕 %s ' % flg)
    return flg


#
if __name__ == '__main__':
    # task = {
    #     'cityName': '北京',
    #     'cityCode': '530',
    #     'funcCode': '045',
    #     'jobName': '软件工程师',
    #     'pageNum': 1,
    # }
    # search(task)
    # invalid_cookie(0)
    load_account()

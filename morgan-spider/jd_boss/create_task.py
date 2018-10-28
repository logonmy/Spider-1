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
import urllib
import MySQLdb
from DBUtils.PersistentDB import PersistentDB
import datetime

CITY_LIST = [
    ["101010100", u"北京"], 
    ["101020100", u"上海"], 
    ["101030100", u"天津"], 
    ["101040100", u"重庆"], 
    ["101050100", u"哈尔滨"], 
    ["101050200", u"齐齐哈尔"], 
    ["101050300", u"牡丹江"], 
    ["101050400", u"佳木斯"], 
    ["101050500", u"绥化"], 
    ["101050600", u"黑河"], 
    ["101050700", u"伊春"], 
    ["101050800", u"大庆"], 
    ["101050900", u"七台河"], 
    ["101051000", u"鸡西"], 
    ["101051100", u"鹤岗"], 
    ["101051200", u"双鸭山"], 
    ["101060100", u"长春"], 
    ["101060200", u"吉林"], 
    ["101060300", u"四平"], 
    ["101060400", u"通化"], 
    ["101060500", u"白城"], 
    ["101060600", u"辽源"], 
    ["101060700", u"松原"], 
    ["101060800", u"白山"], 
    ["101060900", u"延边"], 
    ["101070100", u"沈阳"], 
    ["101070200", u"大连"], 
    ["101070300", u"鞍山"], 
    ["101070400", u"抚顺"], 
    ["101070500", u"本溪"], 
    ["101070600", u"丹东"], 
    ["101070700", u"锦州"], 
    ["101070800", u"营口"], 
    ["101070900", u"阜新"], 
    ["101071000", u"辽阳"], 
    ["101071100", u"铁岭"], 
    ["101071200", u"朝阳"], 
    ["101071300", u"盘锦"], 
    ["101071400", u"葫芦岛"], 
    ["101080100", u"呼和浩特"], 
    ["101080200", u"包头"], 
    ["101080300", u"乌海"], 
    ["101080400", u"通辽"], 
    ["101080500", u"赤峰"], 
    ["101080600", u"鄂尔多斯"], 
    ["101080700", u"呼伦贝尔"], 
    ["101080800", u"巴彦淖尔"], 
    ["101080900", u"乌兰察布"], 
    ["101081000", u"锡林郭勒"], 
    ["101090100", u"石家庄"], 
    ["101090200", u"保定"], 
    ["101090300", u"张家口"], 
    ["101090400", u"承德"], 
    ["101090500", u"唐山"], 
    ["101090600", u"廊坊"], 
    ["101090700", u"沧州"], 
    ["101090800", u"衡水"], 
    ["101090900", u"邢台"], 
    ["101091000", u"邯郸"], 
    ["101091100", u"秦皇岛"], 
    ["101100100", u"太原"], 
    ["101100200", u"大同"], 
    ["101100300", u"阳泉"], 
    ["101100400", u"晋中"], 
    ["101100500", u"长治"], 
    ["101100600", u"晋城"], 
    ["101100700", u"临汾"], 
    ["101100800", u"运城"], 
    ["101100900", u"朔州"], 
    ["101101000", u"忻州"], 
    ["101101100", u"吕梁"], 
    ["101110100", u"西安"], 
    ["101110200", u"咸阳"], 
    ["101110300", u"延安"], 
    ["101110400", u"榆林"], 
    ["101110500", u"渭南"], 
    ["101110600", u"商洛"], 
    ["101110700", u"安康"], 
    ["101110800", u"汉中"], 
    ["101110900", u"宝鸡"], 
    ["101111000", u"铜川"], 
    ["101120100", u"济南"], 
    ["101120200", u"青岛"], 
    ["101120300", u"淄博"], 
    ["101120400", u"德州"], 
    ["101120500", u"烟台"], 
    ["101120600", u"潍坊"], 
    ["101120700", u"济宁"], 
    ["101120800", u"泰安"], 
    ["101120900", u"临沂"], 
    ["101121000", u"菏泽"], 
    ["101121100", u"滨州"], 
    ["101121200", u"东营"], 
    ["101121300", u"威海"], 
    ["101121400", u"枣庄"], 
    ["101121500", u"日照"], 
    ["101121600", u"莱芜"], 
    ["101121700", u"聊城"], 
    ["101130100", u"乌鲁木齐"], 
    ["101130200", u"克拉玛依"], 
    ["101130300", u"昌吉"], 
    ["101130400", u"巴音郭楞"], 
    ["101130500", u"博尔塔拉"], 
    ["101130600", u"伊犁"], 
    ["101130700", u"克孜勒苏柯尔克孜"], 
    ["101150100", u"西宁"], 
    ["101150200", u"海东"], 
    ["101150300", u"海北"], 
    ["101150400", u"黄南"], 
    ["101150500", u"海南"], 
    ["101150600", u"果洛"], 
    ["101150700", u"玉树"], 
    ["101150800", u"海西"], 
    ["101160100", u"兰州"], 
    ["101160200", u"定西"], 
    ["101160300", u"平凉"], 
    ["101160400", u"庆阳"], 
    ["101160500", u"武威"], 
    ["101160600", u"金昌"], 
    ["101160700", u"张掖"], 
    ["101160800", u"酒泉"], 
    ["101160900", u"天水"], 
    ["101161000", u"白银"], 
    ["101161100", u"陇南"], 
    ["101161200", u"嘉峪关"], 
    ["101161300", u"临夏"], 
    ["101161400", u"甘南"], 
    ["101170100", u"银川"], 
    ["101170200", u"石嘴山"], 
    ["101170300", u"吴忠"], 
    ["101170400", u"固原"], 
    ["101170500", u"中卫"], 
    ["101180100", u"郑州"], 
    ["101180200", u"安阳"], 
    ["101180300", u"新乡"], 
    ["101180400", u"许昌"], 
    ["101180500", u"平顶山"], 
    ["101180600", u"信阳"], 
    ["101180700", u"南阳"], 
    ["101180800", u"开封"], 
    ["101180900", u"洛阳"], 
    ["101181000", u"商丘"], 
    ["101181100", u"焦作"], 
    ["101181200", u"鹤壁"], 
    ["101181300", u"濮阳"], 
    ["101181400", u"周口"], 
    ["101181500", u"漯河"], 
    ["101181600", u"驻马店"], 
    ["101181700", u"三门峡"], 
    ["101190100", u"南京"], 
    ["101190200", u"无锡"], 
    ["101190300", u"镇江"], 
    ["101190400", u"苏州"], 
    ["101190500", u"南通"], 
    ["101190600", u"扬州"], 
    ["101190700", u"盐城"], 
    ["101190800", u"徐州"], 
    ["101190900", u"淮安"], 
    ["101191000", u"连云港"], 
    ["101191100", u"常州"], 
    ["101191200", u"泰州"], 
    ["101191300", u"宿迁"], 
    ["101191400", u"昆山"], 
    ["101191500", u"新沂"], 
    ["101200100", u"武汉"], 
    ["101200200", u"襄阳"], 
    ["101200300", u"鄂州"], 
    ["101200400", u"孝感"], 
    ["101200500", u"黄冈"], 
    ["101200600", u"黄石"], 
    ["101200700", u"咸宁"], 
    ["101200800", u"荆州"], 
    ["101200900", u"宜昌"], 
    ["101201000", u"十堰"], 
    ["101201100", u"随州"], 
    ["101201200", u"荆门"], 
    ["101201300", u"恩施"], 
    ["101201400", u"仙桃"], 
    ["101201500", u"潜江"], 
    ["101210100", u"杭州"], 
    ["101210200", u"湖州"], 
    ["101210300", u"嘉兴"], 
    ["101210400", u"宁波"], 
    ["101210500", u"绍兴"], 
    ["101210600", u"台州"], 
    ["101210700", u"温州"], 
    ["101210800", u"丽水"], 
    ["101210900", u"金华"], 
    ["101211000", u"衢州"], 
    ["101211100", u"舟山"], 
    ["101220100", u"合肥"], 
    ["101220200", u"蚌埠"], 
    ["101220300", u"芜湖"], 
    ["101220400", u"淮南"], 
    ["101220500", u"马鞍山"], 
    ["101220600", u"安庆"], 
    ["101220700", u"宿州"], 
    ["101220800", u"阜阳"], 
    ["101220900", u"亳州"], 
    ["101221000", u"滁州"], 
    ["101221100", u"淮北"], 
    ["101221200", u"铜陵"], 
    ["101221300", u"宣城"], 
    ["101221400", u"六安"], 
    ["101221500", u"池州"], 
    ["101221600", u"黄山"], 
    ["101230100", u"福州"], 
    ["101230200", u"厦门"], 
    ["101230300", u"宁德"], 
    ["101230400", u"莆田"], 
    ["101230500", u"泉州"], 
    ["101230600", u"漳州"], 
    ["101230700", u"龙岩"], 
    ["101230800", u"三明"], 
    ["101230900", u"南平"], 
    ["101240100", u"南昌"], 
    ["101240200", u"九江"], 
    ["101240300", u"上饶"], 
    ["101240400", u"抚州"], 
    ["101240500", u"宜春"], 
    ["101240600", u"吉安"], 
    ["101240700", u"赣州"], 
    ["101240800", u"景德镇"], 
    ["101240900", u"萍乡"], 
    ["101241000", u"新余"], 
    ["101241100", u"鹰潭"], 
    ["101250100", u"长沙"], 
    ["101250200", u"湘潭"], 
    ["101250300", u"株洲"], 
    ["101250400", u"衡阳"], 
    ["101250500", u"郴州"], 
    ["101250600", u"常德"], 
    ["101250700", u"益阳"], 
    ["101250800", u"娄底"], 
    ["101250900", u"邵阳"], 
    ["101251000", u"岳阳"], 
    ["101251100", u"张家界"], 
    ["101251200", u"怀化"], 
    ["101251300", u"永州"], 
    ["101251400", u"湘西"], 
    ["101260100", u"贵阳"], 
    ["101260200", u"遵义"], 
    ["101260300", u"安顺"], 
    ["101260400", u"铜仁"], 
    ["101260500", u"毕节"], 
    ["101260600", u"六盘水"], 
    ["101260700", u"黔东南"], 
    ["101260800", u"黔南"], 
    ["101260900", u"黔西南"], 
    ["101270100", u"成都"], 
    ["101270200", u"攀枝花"], 
    ["101270300", u"自贡"], 
    ["101270400", u"绵阳"], 
    ["101270500", u"南充"], 
    ["101270600", u"达州"], 
    ["101270700", u"遂宁"], 
    ["101270800", u"广安"], 
    ["101270900", u"巴中"], 
    ["101271000", u"泸州"], 
    ["101271100", u"宜宾"], 
    ["101271200", u"内江"], 
    ["101271300", u"资阳"], 
    ["101271400", u"乐山"], 
    ["101271500", u"眉山"], 
    ["101271600", u"雅安"], 
    ["101271700", u"德阳"], 
    ["101271800", u"广元"], 
    ["101271900", u"阿坝"], 
    ["101272000", u"凉山"], 
    ["101272100", u"甘孜"], 
    ["101280100", u"广州"], 
    ["101280200", u"韶关"], 
    ["101280300", u"惠州"], 
    ["101280400", u"梅州"], 
    ["101280500", u"汕头"], 
    ["101280600", u"深圳"], 
    ["101280700", u"珠海"], 
    ["101280800", u"佛山"], 
    ["101280900", u"肇庆"], 
    ["101281000", u"湛江"], 
    ["101281100", u"江门"], 
    ["101281200", u"河源"], 
    ["101281300", u"清远"], 
    ["101281400", u"云浮"], 
    ["101281500", u"潮州"], 
    ["101281600", u"东莞"], 
    ["101281700", u"中山"], 
    ["101281800", u"阳江"], 
    ["101281900", u"揭阳"], 
    ["101282000", u"茂名"], 
    ["101282100", u"汕尾"], 
    ["101290100", u"昆明"], 
    ["101290200", u"曲靖"], 
    ["101290300", u"保山"], 
    ["101290400", u"玉溪"], 
    ["101290500", u"普洱"], 
    ["101290700", u"昭通"], 
    ["101290800", u"临沧"], 
    ["101290900", u"丽江"], 
    ["101291000", u"西双版纳"], 
    ["101291100", u"文山"], 
    ["101291200", u"红河"], 
    ["101291300", u"德宏"], 
    ["101291400", u"怒江"], 
    ["101291500", u"迪庆"], 
    ["101291600", u"大理"], 
    ["101291700", u"楚雄"], 
    ["101300100", u"南宁"], 
    ["101300200", u"崇左"], 
    ["101300300", u"柳州"], 
    ["101300400", u"来宾"], 
    ["101300500", u"桂林"], 
    ["101300600", u"梧州"], 
    ["101300700", u"贺州"], 
    ["101300800", u"贵港"], 
    ["101300900", u"玉林"], 
    ["101301000", u"百色"], 
    ["101301100", u"钦州"], 
    ["101301200", u"河池"], 
    ["101301300", u"北海"], 
    ["101301400", u"防城港"], 
    ["101310100", u"海口"], 
    ["101310200", u"三亚"], 
    ["101310300", u"三沙"], 
    ["101340100", u"台北"], 
    ["101340200", u"新北"], 
    ["101340300", u"台中"], 
    ["101340400", u"台南"], 
    ["101340500", u"高雄"], 
    ["101340600", u"基隆"], 
    ["101340700", u"嘉义"], 
    ["101340800", u"屏东"], 
    ["101140100", u"拉萨"], 
    ["101320300", u"香港"], 
    ["101330100", u"澳门"], 
]
# ZONE_LIST = []
INDUSTRY_LIST = [502, 503, 504, 505, 506, 507, 507, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 501]
MONEY_LIST = [1, 2, 3, 4, 5, 6, 7, 8]
EDUCATION_LIST = [207, 206, 202, 203, 204, 205]
EXPERIENCE_LIST = [102, 103, 104, 105, 106,107]
SIZE_LIST = [301, 302, 303, 304, 305, 306]

def get_list(city=None, zone=None, money=None, education=None, experience=None, size=None, page_now=None, is_get_zone=None, proxy=None, jobtitle=None, **kwargs):
    logger = utils.get_logger()
    
    proxy = proxy if proxy else utils.get_proxy()
    # proxy = utils.get_proxy()
    
    # logger.info('split_list_thread start!!!')
    result = {'code': 0}
    # list_url = 'http://www.zhipin.com/%s/e_105-d_203-s_302-y_4-b_%E6%9C%9D%E9%98%B3%E5%8C%BA/?page=%s&ka=page-next'
    city_param = 'c' + str(city)
    zone_param =  'b_' + str(zone) if zone else ''
    # industry_param = 'i'+str(industry)+'-' if industry else ''
    jobtitle_param = '-p'+str(jobtitle) if jobtitle else ''
    money_param = 'y_'+str(money)+'-' if money else ''
    education_param = 'd_'+str(education)+'-' if education else ''
    experience_param = 'e_'+str(experience)+'-' if experience else ''
    size_param = 's_'+str(size)+'-' if size else ''
    # list_url = 'http://www.zhipin.com/%s/?page=%s' % (city, page_now)
    if experience_param or education_param or size_param or money_param or zone_param:
        list_url = 'http://www.zhipin.com/'+city_param+jobtitle_param+'/'+experience_param+education_param+size_param+money_param+zone_param+'/?page='+str(page_now)+'&ka=page-next'
    else:
        list_url = 'http://www.zhipin.com/'+city_param+jobtitle_param+'/?page='+str(page_now)+'&ka=page-next'
    logger.info('the url, proxy is'+list_url+'    '+str(proxy))
    # time.sleep(2)
    list_header = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'zh-CN,zh;q=0.8',
        'Host':'www.zhipin.com',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }
    while True:
        logger.info('download url:'+list_url)
        try:
            response = requests.get(list_url, headers=list_header, allow_redirects=False, proxies=proxy, timeout=10)
            if response.status_code in [200, '200']:
                if len(response.text) < 1024:
                    logger.info('get '+response.text)
                else:
                    break
            else:
                logger.info('not get 200 when download list!!!'+ str(response.status_code))
                # result['code']=1
        except Exception, e:
            logger.info(str(traceback.format_exc()))
        proxy.update(utils.get_proxy())


    tree = etree.HTML(response.text.encode('utf8'))
    jobs_list = tree.xpath('//div[@class="job-box"]/div[@class="job-list"]/ul/li')
    result['jobs']=[]
    for job in jobs_list:
        if job.xpath('./a') and job.xpath('.//div[@class="job-time"]/span'):
            result['jobs'].append({'href': 'http://www.zhipin.com'+job.xpath('./a')[0].attrib['href'], 'job_time': job.xpath('.//div[@class="job-time"]/span')[0].text})
        else:
            logger.info('get error when parse job!!!')
            #logger.info('get error when parse job!!!'+str(response.text.encode('utf8')))
            # error_file_lock.acquire()
            # f=open('error_file', 'a')
            # f.write(base64.b64encode(response.text.encode('utf8')))
            # f.close()
            # error_file_lock.release()
            
    if is_get_zone :
        result['zone'] = []
        if tree.xpath('//dl[@class="condition-district show-condition-district"]'):
            dts = tree.xpath('//dl[@class="condition-district show-condition-district"]/dt')
            dds = tree.xpath('//dl[@class="condition-district show-condition-district"]/dd')
            if dts and dds and dts[0].text == u'区域：':
                a_s = dds[0].xpath('./a')
                for a in a_s:
                    if len(a.attrib['href'].split('b_'))>1:
                        result['zone'].append([a.attrib['href'].split('_')[-1][:-1], a.text])
        
    return result

def main():
    logger = utils.get_logger()
    global zones
    global industrys
    proxy = utils.get_proxy()
    
    if not proxy:
        logger.info('did not get proxy, quit!!!')
        return 
    # proxy = None
    job_file = open('keys_number', 'r')
    jobtitles = job_file.readlines()
    job_file.close()
    apply_origin_task = False
    origin_task = {"city": "101010100", "zone": "%E6%9C%9D%E9%98%B3%E5%8C%BA", "money": 5, "jobtitle": "170501", "education": 205}
    for city in CITY_LIST:
        logger.info('---------------------------------------------------------')
        # time.sleep(10)
        if apply_origin_task and 'city' in origin_task:
            if city[0] != origin_task['city']:
                continue
            else:
                origin_task.pop('city')
            if not origin_task:
                apply_origin_task = False
                continue
        print apply_origin_task, origin_task, city
        process_dict = {'city': city[0], 'cityName': city[1]}
        list_result = get_list(page_now=30, is_get_zone=True, proxy=proxy, **process_dict)
        logger.info('1================'+str(list_result))
        # time.sleep(5)
        if (len(list_result['jobs'])<=14) and (not apply_origin_task):
            task_file = open('task_file', 'a')
            task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
            task_file.close()
            continue
        for zone in list_result['zone']:
            if apply_origin_task and 'zone' in origin_task:
                if zone[0] != origin_task['zone']:
                    continue
                else:
                    origin_task.pop('zone')
                if not origin_task:
                    apply_origin_task = False
                    continue

            else:
                process_dict = {'city': city[0], 'zone': zone[0], 'cityName': city[1]+'-'+urllib.unquote(zone[0]).decode('utf8')}
                list_result = get_list(page_now=30, proxy=proxy, **process_dict)
                logger.info('2================'+str(list_result))
                # time.sleep(5)
                if len(list_result['jobs'])<=14:
                    task_file = open('task_file', 'a')
                    task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
                    task_file.close()
                    continue
            for jobtitle in jobtitles:
                if apply_origin_task and 'jobtitle' in origin_task:
                    if jobtitle.split()[0] != origin_task['jobtitle']:
                        continue
                    else:
                        origin_task.pop('jobtitle')
                    if not origin_task:
                        apply_origin_task = False
                        continue
                else:
                    process_dict = {'city': city[0], 'zone': zone[0], 'jobtitle': jobtitle.split()[0], 'cityName': city[1]+'-'+urllib.unquote(zone[0]).decode('utf8')}
                    list_result = get_list(page_now=30, proxy=proxy, **process_dict)
                    logger.info('3================'+str(list_result))
                    # time.sleep(5)
                    if len(list_result['jobs'])<=14:
                        task_file = open('task_file', 'a')
                        task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
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
                        process_dict = {'city': city[0], 'zone': zone[0], 'jobtitle': jobtitle.split()[0], 'money': money, 'cityName': city[1]+'-'+urllib.unquote(zone[0]).decode('utf8')}
                        list_result = get_list(page_now=30, proxy=proxy, **process_dict)
                        logger.info('4================'+str(list_result))
                        # time.sleep(5)
                        if len(list_result['jobs'])<=14:
                            task_file = open('task_file', 'a')
                            task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
                            task_file.close()
                            continue
                    for education in EDUCATION_LIST:
                        if apply_origin_task and 'education' in origin_task:
                            if education != origin_task['education']:
                                continue
                            else:
                                origin_task.pop('education')
                            if not origin_task:
                                apply_origin_task = False
                                continue
                        else:
                            process_dict = {'city': city[0], 'zone': zone[0], 'jobtitle': jobtitle.split()[0], 'money': money, 'education': education, 'cityName': city[1]+'-'+urllib.unquote(zone[0]).decode('utf8')}
                            list_result = get_list(page_now=30, proxy=proxy, **process_dict)
                            logger.info('5================'+str(list_result))
                            # time.sleep(5)
                            if len(list_result['jobs'])<=14:
                                task_file = open('task_file', 'a')
                                task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
                                task_file.close()
                                continue
                        for experience in EXPERIENCE_LIST:
                            if apply_origin_task and 'experience' in origin_task:
                                if experience != origin_task['experience']:
                                    continue
                                else:
                                    origin_task.pop('experience')
                                if not origin_task:
                                    apply_origin_task = False
                                    continue
                            else:
                                process_dict = {'city': city[0], 'zone': zone[0], 'jobtitle': jobtitle.split()[0], 'money': money, 'education': education, 'experience': experience, 'cityName': city[1]+'-'+urllib.unquote(zone[0]).decode('utf8')}
                                list_result = get_list(page_now=30, proxy=proxy, **process_dict)
                                logger.info('6================'+str(list_result))
                                # time.sleep(5)
                                if len(list_result['jobs'])<=14:
                                    task_file = open('task_file', 'a')
                                    task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
                                    task_file.close()
                                    continue
                            for size in SIZE_LIST:
                                if apply_origin_task and 'size' in origin_task:
                                    if size != origin_task['size']:
                                        continue
                                    else:
                                        origin_task.pop('size')
                                    if not origin_task:
                                        apply_origin_task = False
                                        continue
                                else:
                                    process_dict = {'city': city[0], 'zone': zone[0], 'jobtitle': jobtitle.split()[0], 'money': money, 'education': education, 'experience': experience, 'size': size, 'cityName': city[1]+'-'+urllib.unquote(zone[0]).decode('utf8')}
                                    task_file = open('task_file', 'a')
                                    task_file.write(json.dumps(process_dict, ensure_ascii=False)+'\n')
                                    task_file.close()

    # task_file.close()

def main2():
    f=open('cities', 'r')
    a=f.readline()
    f.close()
    b=json.loads(a)
    job_file = open('keys_number', 'r')
    jobtitles = job_file.readlines()
    job_file.close()
    task_file = open('task_file', 'w')
    for city in b:
        if city[2]:
            for zone in city[2]:
                for jobtitle in jobtitles:
                    task_file.write(json.dumps({"city": city[0], "cityName": city[1]+"-"+zone, "zone": urllib.quote(zone.encode('utf8')).upper(), "jobtitle": jobtitle}, ensure_ascii=False).encode('utf8')+'\n')
        else:
            for jobtitle in jobtitles:
                    task_file.write(json.dumps({"city": city[0], "cityName": city[1], "jobtitle": jobtitle}, ensure_ascii=False).encode('utf8')+'\n')

    task_file.close()
    print 'done'

def add_old_task():
    logger = utils.get_logger()
    f=open('task_file', 'r')
    count=20000000
    start = 0
    for i in f:
        if start:
            start -= 1
            continue
        add_task_url = common_settings.TASK_URL +common_settings.CREATE_TASK_PATH
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',}
        # add_task_traceid = str(uuid.uuid1())
        add_task_data = {
            "callSystemID": settings.project_settings['CALLSYSTEMID'], 
            "source": settings.project_settings['SOURCE'], 
            "traceID": str(uuid.uuid1()),
            "executeParam": i, 
            "taskType": settings.project_settings['TASK_TYPE'], 
        }
        # add_task_data = json.loads(i)
        # add_task_data['traceID'] = add_task_traceid
        add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
        # count -= 1
        # if not count:
        #     break
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
    city_number = cur.execute('select cityName, url, code from city_entrence where source="BOSS_HR" and valid=1')
    cities = cur.fetchall()
    function_number = cur.execute('select thirdFunctionCode from function_entrence where source="BOSS_HR" and valid=1')
    functions = cur.fetchall()
    logger.info('the number of city and functions is:%s, %s' % (city_number, function_number))
    if not city_number or not function_number:
        return
    add_task_url = common_settings.TASK_URL +common_settings.CREATE_TASK_PATH
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',}
    deadline = datetime.datetime.now() + datetime.timedelta(days=2)
    deadline = int(time.mktime(deadline.timetuple())) * 1000
    task_deleted_file = open('task_deleted', 'r')
    task_deleted = json.loads(task_deleted_file.readline())
    task_deleted_file.close()
    for city in cities:
        funcs_deleted = task_deleted.get(city[0], [])
        for function in functions:
            if not city[1] and function[0] not in funcs_deleted:
                add_task_data = {
                    "callSystemID": settings.project_settings['CALLSYSTEMID'],
                    "source": settings.project_settings['SOURCE'],
                    "traceID": str(uuid.uuid1()),
                    "executeParam": json.dumps({"city": city[2], "cityName": city[0], "jobtitle": function[0]}, ensure_ascii=False),
                    "taskType": settings.project_settings['TASK_TYPE'],
                    'deadline': deadline
                }
                add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
            else:
                for zone in json.loads(city[1]):
                    add_task_data = {
                        "callSystemID": settings.project_settings['CALLSYSTEMID'],
                        "source": settings.project_settings['SOURCE'],
                        "traceID": str(uuid.uuid1()),
                        "executeParam": json.dumps({"city": city[2], "cityName": city[0]+'-'+zone, "zone": urllib.quote(zone.encode('utf8')), "jobtitle": function[0]}, ensure_ascii=False),
                        "taskType": settings.project_settings['TASK_TYPE'],
                        'deadline': deadline,
                    }
                    add_task_result = utils.download(url=add_task_url, is_json=True, headers=headers, method='post', data=add_task_data)
    logger.info('done.')


if __name__ == '__main__':
    utils.set_setting({"PROJECT_NAME": 'jd_boss_create_task',})
    # main2()
    # main()
    # add_old_task()
    create_task_from_mysql()

#!/usr/bin python
# encoding:utf-8
# @Time    : 2018/4/4
# @Author  : ZhangXueTong
# @Site    :
# @File    : jianli.py
# @Software: PyCharm
# @Pythonenvironment : python2.7


# 导入所需要的模块
import requests
from lxml import etree
import time
import sys
from test_log import get_log
from bs4 import BeautifulSoup
import request
import json
import uuid
import traceback
import utils

logger = get_log()

# 为了防止乱码的出现
reload(sys)
sys.setdefaultencoding('utf-8')


# 使用类进行优化和封装
class JianLi(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        self.request = requests.session()
        self.url = "http://www.jianlika.com"
        self.username = "18629947965"
        self.password = "l56441193"

    # 模拟登录简历咖
    def login(self):
        '''
        :return:
        '''
        # 等待30秒,防止速度过快
        time.sleep(30)
        url = "http://www.jianlika.com/Index/login.html"
        data = {'remember': 'on', 'username': self.username, 'password': self.password}
        # 容错处理,为了增强代码的健壮性
        try:
            self.request.post(url=url, data=data, headers=self.headers)
            logger.info("登入成功")
        except Exception as e:
            logger.exception(str(e))

    # 进行关键词的搜索
    def search(self, key_word):
        '''
        :param key_word:
        :return:
        '''
        # 关键词  大客户销售   销售代表
        # 北京 110000 上海 310000
        i = "110000"
        print"开始爬取{},地区为{}".format(key_word, i)
        data = {
            'keywords': key_word,
            'searchNear': 'on',
            'hopeCity': i,
            'sex': '0',
            'updateDate': '0',
        }
        post_url = "http://www.jianlika.com/Search/index.html"
        # 容错处理,为了增强代码的健壮性
        try:
            # 等待15秒,防止速度过快
            time.sleep(15)
            res = self.request.post(url=post_url, data=data, headers=self.headers)
        except Exception as e:
            logger.exception(str(e))
            return " "
        link = res.text
        url = res.url
        self.get_page(link, url)

    # 进行翻页以及获得列表详情页面的链接
    def get_page(self, res, url):
        '''
        :param res:
        :param url:
        :return:
        '''
        logger.info("开始翻页")
        # 等待10秒,防止速度过快
        time.sleep(10)
        content = etree.HTML(res)
        page = int(content.xpath('//input[@id="maxPage"]/@value')[0])
        new_url = url.replace(".html", "")
        for i in range(1, page + 1):
            n_url = new_url + "/p/{}.html".format(i)
            print"总共有{}页正在请求{}".format(page, n_url)
            number = self.request.get(n_url, headers=self.headers)
            link = etree.HTML(number.text).xpath(
                '//div[@class="panel border"]/table/tbody/tr/td[@width="215"]/a/@data-href')
            self.resume_info(link)

    # 获取详情页面的网页源码
    def resume_info(self, links):
        '''
        :param links:
        :return:
        '''
        logger.info("开始解析列表页面信息")
        for i in links:
            # 容错处理,为了增强代码的健壮性
            try:
                # 详情页面的链接
                links = self.url + i
                logger.info("详情页面的链接是:%s" % links)
                # 等待10秒,防止速度过快
                time.sleep(10)
                res = self.request.get(url=links, headers=self.headers)
                res.encoding = 'utf-8'
                self.resume_parse(res.text)
            except Exception as e:
                logger.exception(str(e))

    # 匹配详情页面的相对应的简历信息
    def resume_parse(self, source):
        '''
        :param info:
        :return:
        '''
        # print(source)
        # source代表的是源码信息
        logger.info("详细信息正在解析")
        soup = BeautifulSoup(source, 'lxml')
        matchs = soup.find_all("div", class_="tab-content")
        for match in matchs:
            connect = str(match.text).strip().replace("下载联系方式", '').replace("暂存简历", '').replace("打印简历", '').replace(
                "导出简历", '').replace("关键词：UI共出现6次", '')
            logger.info("简历信息是:%s" % connect)
        resume_uuid = uuid.uuid1()
        try:
            content = json.dumps({'name': '', 'email': '', 'phone': '', 'html': source},
                                 ensure_ascii=False)
            sql = 'insert into spider_search.resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
            sql_value = ('RESUME_KA', content, resume_uuid, '18629947965', '销售', '北京', '')

            resume_update_time = ''
            # resume_update_time =  resume_result['json']['updateDate']
            kafka_data = {
                "channelType": "WEB",
                "content": {
                    "content": content,
                    "id": '',
                    "createBy": "python",
                    "createTime": int(time.time() * 1000),
                    "ip": '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": resume_update_time,
                    "source": 'RESUME_KA',
                    "trackId": str(resume_uuid),
                    "avatarUrl": '',
                    "email": '18629947965',
                    'emailJobType': '销售',
                    'emailCity': '北京',
                    'subject': ''
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_SEARCH",
                "source": 'RESUME_KA',
                "trackId": str(resume_uuid),
                'traceID': str(resume_uuid),
                'callSystemID': 'python',
            }
            utils.save_data(sql, sql_value, kafka_data)
        except Exception, e:
            logger.info('get error when write mns, exit!!!' + str(traceback.format_exc()))
            # return

    pass


# 把之前的函数进行整合
def main():
    '''
    :return:
    '''
    utils.set_setting([])
    # 实例化类
    jian = JianLi()
    # 调用相对应的函数
    jian.login()
    link = jian.search("大客户销售")


# 程序入口
if __name__ == '__main__':
    # 调用整合后的函数
    main()

# -*- coding: utf-8 -*-
import time

import scrapy
from scrapy import FormRequest
from datetime import datetime
from crwy.utils.common import cookie2dict, dict2obj
from crwy.utils.scrapy_plugs.settings import LoadSettingsFromConsul
from crwy.utils.html.font_analysis import FontAnalysis, font_mapping
import json, requests, time
from zhao_pin_gou.zhao_pin_gou.items import ZhaoPinGouItem, SpiderSearchResumeRawItemLoader

settings = dict2obj(LoadSettingsFromConsul.get_settings(key='scrapy/zhao_pin_gou/search', host='172.16.25.36'))


class SearchSpider(scrapy.Spider):
    name = 'search'
    allowed_domains = ['qiye.zhaopingou.com']

    randTime = str(int(time.time() * 1000))
    start_urls = [
        'http://qiye.zhaopingou.com/zhaopingou_interface/find_warehouse_by_position_new?timestamp=' + randTime]
    pageNum = 0
    header = {
        'Cookie': 'JSESSIONID=4F531CF1CDBF74B68ABF8C5DB6B3220C; fanwenTime1="2018-10-09 10:49:38"; fangWenNumber1=7; xiaxifanwenTime1="2018-10-09 16:56:16"; fangWenIp=119.2.14.66; xiaoxiNumber=3; xiaoxisuoTime="2018-10-09 16:59:16"; zhaopingou_select_city=-1; zhaopingou_zengsong_cookie_newDay=2018-09-21%3D8; zhaopingou_account=13409807285; Hm_lvt_b025367b7ecea68f5a43655f7540e177=1538183696,1538269918,1538961551,1539053305; zhaopingou_htm_cookie_register_userName=; zhaopingou_htm_cookie_newDay=2018-10-09; JSESSIONID=598B5900B6D30D0E373F14E2648647A7; rd_apply_lastsession_code=0; hrkeepToken=EC12E058F4DC380D0A0E94CC6BB8B173; zhaopingou_login_callback=/; Hm_lpvt_b025367b7ecea68f5a43655f7540e177=1539075743',
        'Referer': 'http://qiye.zhaopingou.com/resume?job=1037&pn=1'
    }
    formdata = {
        "pageSize": "1",
        "pageNo": "25",
        "keyStr": "",
        "companyName": "",
        "schoolName": "",
        "keyStrPostion": "1037",
        "postionStr": "Python",
        "startDegrees": "-1",
        "endDegress": "-1",
        "startAge": "0",
        "endAge": "0",
        "gender": "-1",
        "region": "",
        "timeType": "-1",
        "startWorkYear": "-1",
        "endWorkYear": "-1",
        "beginTime": "",
        "endTime": "",
        "isMember": "-1",
        "hopeAdressStr": "",
        "cityId": "-1",
        "updateTime": "",
        "tradeId": "",
        "startDegreesName": "",
        "endDegreesName": "",
        "tradeNameStr": "",
        "regionName": "",
        "isC": "0",
        "is211_985_school": "0",
        "clientNo": "",
        "userToken": "EC12E058F4DC380D0A0E94CC6BB8B173",
        "clientType": "2",
    }

    def start_requests(self):
        url = 'http://qiye.zhaopingou.com/zhaopingou_interface/find_warehouse_by_position_new?timestamp=' + self.randTime
        req = scrapy.FormRequest(url, headers=self.header, method='POST', formdata=self.formdata)
        req.cookies = cookie2dict(self.header['Cookie'])
        req.meta['list_req_data'] = self.formdata
        req.meta['proxy'] = "http://49.4.80.34:5000"
        yield req

    def parse_detail(self, response):
        # content = response.xpath('//div[@class="new_resume_outer"]').extract()
        # print(content)
        # infomation = json.loads(response.text)
        url = 'http://qiye.zhaopingou.com/zhaopingou_interface/zpg_find_resume_html_details?timestamp=%s' % str(
            self.randTime)
        header = {
            'Cookie': 'JSESSIONID=4F531CF1CDBF74B68ABF8C5DB6B3220C; fanwenTime1="2018-10-09 10:49:38"; fangWenNumber1=7; xiaxifanwenTime1="2018-10-09 16:56:16"; fangWenIp=119.2.14.66; xiaoxiNumber=3; xiaoxisuoTime="2018-10-09 16:59:16"; zhaopingou_select_city=-1; zhaopingou_zengsong_cookie_newDay=2018-09-21%3D8; zhaopingou_account=13409807285; Hm_lvt_b025367b7ecea68f5a43655f7540e177=1538183696,1538269918,1538961551,1539053305; zhaopingou_htm_cookie_register_userName=; zhaopingou_htm_cookie_newDay=2018-10-09; JSESSIONID=598B5900B6D30D0E373F14E2648647A7; rd_apply_lastsession_code=0; hrkeepToken=EC12E058F4DC380D0A0E94CC6BB8B173; zhaopingou_login_callback=/; Hm_lpvt_b025367b7ecea68f5a43655f7540e177=1539075743',
            'Referer': response.url
        }
        data = {
            # 'resumeHtmlId': str(resume_id),
            'keyStr': '',
            'keyPositionName': '',
            'tradeId': '',
            'postionStr': '',
            'jobId': '0',
            'clientNo': '',
            'userToken': 'EC12E058F4DC380D0A0E94CC6BB8B173',
            'clientType': '2',
            'companyName': '',
            'schoolName': '',
        }
        res = scrapy.FormRequest(url, headers=header, method='POST', formdata=data)
        yield res

    def parse(self, response):

        url = self.start_urls[0]
        data = response.meta['list_req_data']
        print(data)
        while self.pageNum < 2:
            data.update({'pageSize': self.pageNum})
            res = requests.get(url, params=data, headers=self.header)

            listOne = []
            for people in res.json()['warehouseList']:
                listOne.append(people['resumeHtmlId'])
            print(listOne)
            self.pageNum += 1

            listTwo = []
            for ll in listOne:
                listTwo.append("http://qiye.zhaopingou.com/resume/detail?resumeId=" + str(ll))
            print(listTwo)

            for link in listTwo:
                # print(link)
                yield scrapy.Request(link, callback=self.parse_detail)

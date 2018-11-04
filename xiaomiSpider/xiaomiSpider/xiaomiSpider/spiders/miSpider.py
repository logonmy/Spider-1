# -*- coding: utf-8 -*-
import json
import scrapy
from xiaomiSpider.items import XiaomispiderItem
from lxml import etree



class MispiderSpider(scrapy.Spider):
    name = 'miSpider'
    allowed_domains = ['koubei.baidu.com']
    url = 'https://koubei.baidu.com/search/getsearchresultajax?wd=%25E8%25A3%2585%25E4%25BF%25AE&page='
    page_num = 1
    start_urls = [url+str(page_num),]


    def parse_second(self,response):
        '''
        该函数用于处理详情页请求
        并将清洗过后的数据进行返回
        :param response:
        :return:
        '''
        item = response.meta["item"]
        response_json = json.loads(response.text)['data']['tpl']
        response_html = etree.HTML(response_json)
        # print(type(response_json))

        # 投诉标题列表
        title_list = response_html.xpath('//ul[@class="kb-truth-list"]/li/div/h4/div[2]/a/text()')
        # 投诉内容列表
        title_conts = response_html.xpath('//ul[@class="kb-truth-list"]/li/div/div[1]/a/pre/text()')

        # 把投诉内容封装成字符串
        content = {}
        # 遍历投诉标题和投诉内容，用投诉标题做键，内容做值
        for i in range(len(title_list)):
            content[title_list[i]] = title_conts[i]
            if content[title_list[i]]:
                # 判断content是否为空，为空就不写入
                item['content']=content

        print(item)
        yield item


    def parse(self, response):
        '''
        该方法处理第一层请求
        主要获取企业id 名称和网站地址
        :param response:
        :return:
        '''
        response_content = json.loads(response.text)
        mems_cont = response_content['data']["mems"]

        items = []

        for data in mems_cont:
            # 将获取到的数据进行第一次保存
            item = XiaomispiderItem()
            item['memname'] = data['memname']
            item['compname'] = data['compname']
            item['memid'] = data['memid']
            items.append(item)

        # 实现翻页
        if self.page_num <= 6:
            self.page_num += 1
            # 拼接列表页链接，实现全爬取
            new_url = self.url+str(self.page_num)
            # 回调处理url
            yield scrapy.Request(new_url,callback=self.parse,dont_filter=False)

        # 循环items取出memid用于拼接详情页url
        for item in items:
            memid = item['memid']
            # 拼接详情页url
            second_url = 'https://koubei.baidu.com/s/gettruthlistajax?memid='+str(memid)+'&page=1&isself=0&iscomp=0&includeme=0&fr=site_tab_truth&_=1535643188266'
            # 将详情页url交给parse_second方法处理
            yield scrapy.Request(second_url, callback=self.parse_second, meta={"item": item}, dont_filter=False)
















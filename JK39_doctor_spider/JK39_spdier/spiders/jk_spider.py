# -*- coding: utf-8 -*-
import scrapy
from JK39_spdier.items import Jk39SpdierItem
import json

class JkSpiderSpider(scrapy.Spider):

    name = 'jk_doctor_spider'
    start_urls = ['http://ask.39.net/browse/jibing.html']

    def parse(self, response):

        for url in response.xpath("//div[@class='cap']/a")[:-1]:

            if url.xpath("./text()").extract()[0] != u'药品':

                url = 'http://ask.39.net'+url.xpath("./@href").extract()[0]

                yield scrapy.Request(url=url,

                                     callback=self.ks_more

                                     )

    def ks_more(self, response):
        for url in response.xpath("//div[@class='J_check_more check-more']/a"):
            url = "http://ask.39.net" + url.xpath("./@href").extract()[0]
            yield scrapy.Request(url=url, callback=self.disease_lsit_info)

    # #2级标签
    # def disease_lsit(self,response):
    #
    #     for url in response.xpath("//div[@class='page-subnav']/a"):
    #
    #         url = 'http://ask.39.net/news' + ''.join(url.xpath("./@href").extract()[0][url.xpath("./@href").extract()[0].rfind('/'):].split('-1.html')) + '.html'
    #
    #         yield scrapy.Request(url=url,
    #
    #                              callback=self.disease_lsit_info,
    #
    #                              )



    #循环及翻页
    def disease_lsit_info(self,response):

        if len(response.xpath("//ul[@class='list_ask list_ask2']/li")) == 0:
            return

        for url in response.xpath("//p[@class='p1']/a/@href"):

            yield scrapy.Request(url='http://ask.39.net' + url.extract(),

                                 callback=self.detail

                                 )
        #页码加1
        page = int(response.url[response.url.find('-')+1:response.url.rfind('.')])+1

        url = response.url[:response.url.find('-')+1]+str(page)+'.html'

        yield scrapy.Request(url=url,

                             callback=self.disease_lsit_info

                             )

    def detail(self,response):

        for x in response.xpath("//div[@class='sele_all marg_top']"):

            item = Jk39SpdierItem()
            #名字
            item['name'] = x.xpath(".//span[@class='doc_name']/text()").extract()[0]
            #职位
            item['job'] = x.xpath(".//span[@class='doc_yshi']/text()").extract()[0]

            if len(x.xpath(".//span[@class='doc_yshi']/text()")) > 1:
                #医院
                item['hospital'] = x.xpath(".//span[@class='doc_yshi']/text()").extract()[1]

            else:
                item['hospital'] = ''

            if len(x.xpath(".//p[@class='doc_sc']/span/text()")) > 0:
            #擅长
                item['good'] = x.xpath(".//p[@class='doc_sc']/span/text()").extract()[0]

            else:
                item['good'] = ''
            #医生回答
            item['detail'] = x.xpath(".//p[@class='sele_txt']/text()").extract()[0]
            #时间
            item['time'] = x.xpath(".//p[@class='doc_time']/text()").extract()[0]
            # 追问
            text = ''

            if len(x.xpath(".//div[@class='doc_zw']")) > 0:

                for y in x.xpath(".//div[@class='doc_zw']/span"):

                    text += ''.join(''.join(y.xpath("./text()").extract()).split(' ')).strip()

            item['zw'] = text

            item['link'] = response.url
            #医生pid
            pid = str(response.xpath("//div[@class='doctor_all']/@mid").extract()[0])
            #医生url
            json_url = 'http://askdatafmy.39.net/home/askapi.ashx?callback=jQuery172033868943235912363_1539677691886&action=doctorTopicCount&pid='+pid


            yield scrapy.Request(url=response.xpath("//div[@class='doc_img']/a/@href").extract()[0],

                                 callback=self.get_room,

                                 dont_filter=True,

                                 meta={'item': item, 'json_url': json_url}

                                 )

    def get_room(self,response):

        item = response.meta['item']
        #room 科室
        if len(response.xpath("//div[@class='doctor-msg-job']/span/text()")) > 1:

            item['room'] = response.xpath("//div[@class='doctor-msg-job']/span[2]/text()").extract()[0]

        else:

            item['room'] =''

        yield scrapy.Request(url = response.meta['json_url'],

                             callback= self.return_item,

                             meta={'item': item}

                             )

    #获取帮助人数
    def return_item(self,response):

        item = response.meta['item']

        item['helper'] = json.loads(response.body[response.body.find('(')+1:-1])['data']['all']

        return item
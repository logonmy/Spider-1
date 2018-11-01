# -*- coding: utf-8 -*-
import scrapy

from doctor.items import DoctorItem


class DoctorlistSpider(scrapy.Spider):
    name = 'doctorList'
    allowed_domains = ['ask.39.net']
    page = 0
    start_urls = ['http://ask.39.net/browse/jibing.html']

    # 处理字符串
    def handlerStr(self, str1):
        ss = str1.split("-")[1].split(".")[0]
        return ss

    # 处理url
    def handlerUrl(self, url):
        ss = url.split("/")[-1].split('-')[0]
        return ss

    def parseDetail(self, response):
        # 医生姓名
        name = response.xpath('//span[@class="doc_name"]/text()').extract()
        # print(name)
        # 医生级别
        level = response.xpath('//span[@class="doc_yshi"][1]/text()').extract()
        # 工作单位
        company = response.xpath('//span[@class="doc_yshi"][2]/text()').extract()
        print(company)
        # 擅长的领域
        good = response.xpath('//p[@class="doc_sc"]/span/text()').extract()
        print(good)
        # 回答答案
        detail = response.xpath('//p[@class="sele_txt"]/text()').extract()
        # 回答时间
        time = response.xpath('//p[@class="doc_time"]/text()').extract()

        for i in range(len(name)):
            item = DoctorItem()
            if len(name) > 0:
                item['name'] = name[i]
                item['level'] = level[i]
                item['company'] = company[i]
                item['good'] = good[i]
                item['detail'] = detail[i]
                item['time'] = time[i]
                item['link'] = response.url
            # print(item)
            yield item

    def parseTwo(self, response):
        urlTwos = response.xpath("//p[@class='p1']/a/@href").extract()  # 详情链接
        # end--- //spa
        end = response.xpath("//span[@class='pgleft']/a/@href").extract()[-1]
        totalNum = self.handlerStr(str(end))
        urlThree = response.url
        typeKey = self.handlerUrl(str(urlThree))
        for urlTwo in urlTwos:
            listUrl = "http://ask.39.net" + urlTwo
            yield scrapy.Request(listUrl, callback=self.parseDetail)

        # 分页
        # while self.page <= int(totalNum):
        while self.page <= 2:
            self.page = self.page + 1
            url = "http://ask.39.net/news/" + typeKey + "-" + str(self.page) + ".html"

            yield scrapy.Request(url, callback=self.parseTwo)

    def parseOne(self, response):
        links = response.xpath('//div[@class="J_check_more check-more"]/a/@href').extract()[0]
        url = "http://ask.39.net" + links
        # 进入二级菜单的列表页
        yield scrapy.Request(url, callback=self.parseTwo)

    def parse(self, response):
        linkuUrl = response.xpath('//li[@class="sublink"]/a/@href').extract()
        listOne = []
        for url in linkuUrl:
            listOne.append("http://ask.39.net" + url)
        # 从二级菜单进入
        for oneUrl in listOne:
            yield scrapy.Request(oneUrl, callback=self.parseOne)

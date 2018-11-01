# -*- coding: utf-8 -*-
import scrapy
from sick.items import SickItem


class SicklistSpider(scrapy.Spider):
    name = 'sickList'
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
        item = SickItem()
        # 问题类目
        catOne = response.xpath('//div[@class="sub"]/span[2]/a/text()').extract()[0]
        catTwo = response.xpath('//div[@class="sub"]/span[3]/a/text()').extract()[0]
        catThree = response.xpath('//div[@class="sub"]/span[4]/a/text()').extract()[0]
        catFour = response.xpath('//span[@class="sub_here"]/text()').extract()[0].strip()

        # 问题标题
        title = response.xpath('//p[@class="ask_tit"]/text()').extract()[0].strip()

        # 患者性别
        gender = response.xpath('//p[@class="mation"]/span[1]/text()').extract()[0]
        # 年龄
        age = response.xpath('//p[@class="mation"]/span[2]/text()').extract()[0].strip()
        # 发病时间
        startTime = response.xpath('//p[@class="mation"]/span[3]/text()').extract()[0]
        # 问题描述
        question = response.xpath('//p[@class="txt_ms"]/text()').extract()[0].strip()
        # 提问时间
        questionTime = response.xpath('//p[@class="txt_nametime"]/span[2]/text()').extract()[0]
        # 问题标签
        questionTag = response.xpath('//p[@class="txt_label"]/span/a/text()').extract()
        # 问题链接
        questionUrl = response.url

        strTag = ""
        for tag in questionTag:
            strTag += "|" + tag

        item['catOne'] = catOne
        item['catTwo'] = catTwo
        item['catThree'] = catThree
        item['catFour'] = catFour
        item['title'] = title
        item['gender'] = gender
        item['age'] = age
        item['startTime'] = startTime
        item['question'] = question
        item['questionTime'] = questionTime
        item['questionTag'] = strTag
        item['questionUrl'] = questionUrl
        yield item

        # # doctor
        # # 医生姓名
        # name = response.xpath('//span[@class="doc_name"]/text()').extract()
        # # 医生级别
        # level = response.xpath('//p[@class="doc_xinx"]/span[1]/text()').extract()
        # # 工作单位
        # company = response.xpath('p[@class="doc_xinx"]/span[3]/text()').extract()
        # # 擅长的领域
        # good = response.xpath('//p[@class="doc_sc"]/span/text()').extract()
        # # 回答答案
        # detail = response.xpath('//p[@class="sele_txt"]/text()').extract()
        # # 回答时间
        # time = response.xpath('//p[@class="doc_time"]/text()').extract()
        # for i in len(name):

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

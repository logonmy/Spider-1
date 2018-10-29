# -*- coding: utf-8 -*-
import scrapy
from gaoxueya.items import GaoxueyaItem


class SpiderhypertensionSpider(scrapy.Spider):
    name = 'spiderhypertension'
    allowed_domains = ['ask.familydoctor.com.cn']
    # start_url = ['http://ask.familydoctor.com.cn/did/63/?page=']
    page = 1
    url = "http://ask.familydoctor.com.cn/did/63/?page="
    start_urls = [url + str(page)]

    def handlesQuestion(self,doctors):
        ss=doctors.split()
        doctor=ss[0]
        level=ss[1]
        return doctor,level
    def parse_info(self, response):
        item = GaoxueyaItem()
        # 标题
        title = response.xpath('//div[@class="cont"]/h3/text()').extract()[0]
        # 提问时间
        question_time = response.xpath('//div[@class="patient-info"]/span/text()').extract()[0]
        # 疾病
        disease = response.xpath('//p[@class="illness-type"]/a/text()').extract()[0]
        # question
        question = response.xpath('//div[@class="illness-pics"]/p/text()').extract()[0].strip()
        # 医生
        doctors = response.xpath('//div[@class="main lfloat main-small"]/div[2]/ul/li/div[2]/dl/dt/a/p/text()').extract()
        # 点赞数
        good_num = response.xpath(
            '//div[@class="main lfloat main-small"]/div[2]/ul/li/div[2]/dl/dt/div/i[1]/text()').extract()
        # 踩数量
        bad_num = response.xpath(
            '//div[@class="main lfloat main-small"]/div[2]/ul/li/div[2]/dl/dt/div/i[2]/text()').extract()
        # 回答内容
        answers = response.xpath('//p[@class="answer-words"]/text()').extract()
        # 回答时间
        answers_time = response.xpath(
            '//div[@class="main lfloat main-small"]/div[2]/ul/li/div[2]/dl/dd/div//span/text()').extract()

        for i in range(len(doctors)):
            # 题目
            item['title'] = title
            # 提问时间
            item['question_time'] = question_time
            item['disease'] = disease
            item['question'] = question
            doctor,level=self.handlesQuestion(doctors[0])
            item['doctor'] = doctor
            item['level']=level
            item['good_num'] = good_num[i]
            item['bad_num'] = bad_num[i]
            for an in answers:
                item['answers'] = an.strip()
            item['answers_time'] = answers_time[i]
            item['wt_url'] = response.url
            yield item

    def parse(self, response):
        # 得到所有问题的链接
        links = response.xpath("//div[@class='cont faq-list']/dl/dt/p/a/@href").extract()
        for link in links:
            yield scrapy.Request(link, callback=self.parse_info)

        if self.page < 3738:
            self.page += 1
            new_url = self.url + str(self.page)
            yield scrapy.Request(new_url, callback=self.parse)

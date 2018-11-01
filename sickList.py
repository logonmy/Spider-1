# -*- coding: utf-8 -*-
import scrapy
from sick.items import SickItem
# from scrapy.contrib.spiders import CrawlSpider,Rule
# from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class SicklistSpider(CrawlSpider):
	name = 'sickList'
	allowed_domains = ['ask.39.net']
	page = 0
	start_urls = ['http://ask.39.net']

	rules = (
		Rule(LinkExtractor(allow=r'browse'), follow=True),
		Rule(LinkExtractor(allow=r'question/(\d+).html'), callback='parse_item', follow=True),
		)

	def parse_item(self, response):
		print('response.url===========',response.url)
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

		# 医生姓名
		names = response.xpath('//span[@class="doc_name"]/text()').extract()
		# 医生级别
		levels = response.xpath('//p[@class="doc_xinx"]/span[1]/text()').extract()
		# 工作单位
		companys = response.xpath('p[@class="doc_xinx"]/span[3]/text()').extract()
		# 擅长的领域
		goods = response.xpath('//p[@class="doc_sc"]/span/text()').extract()
		# 回答答案
		details = response.xpath('//p[@class="sele_txt"]/text()').extract()
		# 回答时间
		times = response.xpath('//p[@class="doc_time"]/text()').extract()

		for i in range(len(names)):
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
			item['name'] = names[i]
			item['level'] = levels[i]
			item['company'] = companys[i]
			item['good'] = goods[i]
			item['detail'] = details[i]
			item['time'] = times[i]
			# print(item)


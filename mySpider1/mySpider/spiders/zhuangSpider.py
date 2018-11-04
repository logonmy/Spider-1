# -*- coding: utf-8 -*-
import scrapy,re
from datetime import datetime
from mySpider.items import MyspiderItem

class ZhuangspiderSpider(scrapy.Spider):
    name = 'zhuangSpider'
    # allowed_domains = ['http://315.66zhuang.com/']
    page = 1
    url = 'http://315.66zhuang.com/list/p'
    start_urls = [url+str(page)]

    def start_requests(self):
        yield scrapy.Request(self.url, callback=self.parse)

    def parse_detail(self,response):
        item = response.meta['meta_item']
        #投诉标题
        title = response.xpath('//div[@class="zxts_show_detcont"]/ul/li[1]/span/text()').extract()[0]

        #投诉公司
        companyname = response.xpath('//div[@class="zxts_show_detcont"]/ul/li[3]/a/text()').extract()[0]

        #地点
        address = response.xpath('//div[@class="zxts_show_detcont"]/ul/li[4]/text()').extract()[0].replace('所在地区：',"")
        # print("===========",address)
        if "-" in address:
            province = address.split("-")[0]
            cityname = address.split("-")[1]
        else:
            province = cityname = address

        #时间
        complainttime = response.xpath('//div[@class="zxts_show_detcont"]/ul/li[5]/text()').extract()[0].replace('投诉时间：',"")

        #图片地址
        content_pic = response.xpath('//div[@class="zxts_show_detcont"]/ul/li[6]/p/img/@src | //div[@class="zxts_show_detcont"]/ul/li[6]/img/@src | //div[@class="zxts_show_detcont"]/ul/li[6]/div/div/img/@src | //div[@class="zxts_show_detcont"]/ul/li[6]/div/span/img/@src').extract()


        #详情
        content= response.xpath('//div[@class="zxts_show_detcont"]/ul/li[6]/span/p/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/p[@class]/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/p/span/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/span/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/p/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/div/text() | //div[@class="zxts_show_detcont"]/ul/li[7]/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/div/p/text() | //div[@class="zxts_show_detcont"]/ul/li[6]/p/strong/span/text()').extract()
        content = "".join(content).strip().replace('\r\n\t','').replace('\r\n\r\n','').replace('\r\n','').replace('\xa0','').replace('\t','')

        addtime = str(datetime.now())[:-7]


        #标签
        tag = response.xpath('//div[@class="zxts_show_detcont"]/div[1]/div/a/text()').extract()
        tag = ",".join(tag)

        for pic in content_pic:
            pic = "http://315.66zhuang.com" + pic
            if len(pic) > 0:
                content = content + pic + ' '

        item['title'] = title
        item['companyname'] = companyname
        item['province'] = province
        item['cityname'] = cityname
        item['complainttime'] = complainttime
        item['content'] = content
        item['tag'] = tag
        item['addtime'] = addtime


        yield item


    def parse(self, response):
        # print(response.url)
        # print(response.text)

        sourcename = response.xpath('//div[@class="zxts_list_clatitle"]/h1/text()').extract()[0]
        source_urls = response.xpath('//td[@class="td1"]/a/@href').extract()

        # print('source_urls===',source_urls)
        for source in source_urls:
            sourceurl = "http://315.66zhuang.com" + source
            # print(sourceurl)
            item = MyspiderItem()
            item['sourceurl'] = sourceurl
            item['sourcename'] = sourcename

            yield scrapy.Request(sourceurl,callback=self.parse_detail,meta={'meta_item':item})

        if self.page <= 397:
            self.page += 1
            # 拼接列表页链接，实现全爬取
            new_url = self.url + str(self.page)
            # 回调处理url
            yield scrapy.Request(new_url, callback=self.parse)



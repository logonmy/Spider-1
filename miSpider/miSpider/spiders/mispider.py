# -*- coding: utf-8 -*-
import scrapy
import json

from miSpider.items import MispiderItem


class MispiderSpider(scrapy.Spider):
    name = 'mispider'
    allowed_domains = ['home.fang.com/album']



    start_urls = [
        'http://home.fang.com/album/bj/s24/',
        'http://home.fang.com/album/bj/s24/2/',
        'http://home.fang.com/album/bj/s24/3/',
        'http://home.fang.com/album/bj/s24/4/',
        'http://home.fang.com/album/bj/s24/5/',
        'http://home.fang.com/album/bj/s24/6/',
        'http://home.fang.com/album/bj/s24/7/',
        'http://home.fang.com/album/bj/s24/8/',
        'http://home.fang.com/album/bj/s24/9/',
        'http://home.fang.com/album/bj/s24/10/',
        'http://home.fang.com/album/bj/s24/11/',
        'http://home.fang.com/album/bj/s24/12/',
        'http://home.fang.com/album/bj/s24/13/',
        'http://home.fang.com/album/bj/s24/14/',
        'http://home.fang.com/album/bj/s24/15/',
        'http://home.fang.com/album/bj/s24/16/',
        'http://home.fang.com/album/bj/s24/17/',
        'http://home.fang.com/album/bj/s24/18/',
        'http://home.fang.com/album/bj/s24/19/',
        'http://home.fang.com/album/bj/s24/20/',
        'http://home.fang.com/album/bj/s24/21/',
        'http://home.fang.com/album/bj/s24/22/',
        'http://home.fang.com/album/bj/s24/23/',
        'http://home.fang.com/album/bj/s24/24/',
        'http://home.fang.com/album/bj/s24/25/',
        'http://home.fang.com/album/bj/s24/26/',
        'http://home.fang.com/album/bj/s24/27/',
        'http://home.fang.com/album/bj/s24/28/',
        'http://home.fang.com/album/bj/s24/29/',
        'http://home.fang.com/album/bj/s24/30/',
        'http://home.fang.com/album/bj/s24/31/',
        'http://home.fang.com/album/bj/s24/32/',
        'http://home.fang.com/album/bj/s24/33/',
        'http://home.fang.com/album/bj/s24/34/',
        'http://home.fang.com/album/bj/s24/35/',
        'http://home.fang.com/album/bj/s24/36/',
        'http://home.fang.com/album/bj/s24/37/',
        'http://home.fang.com/album/bj/s24/38/',
        'http://home.fang.com/album/bj/s24/39/',
        'http://home.fang.com/album/bj/s24/40/',
        'http://home.fang.com/album/bj/s24/41/',
        'http://home.fang.com/album/bj/s24/42/',
        'http://home.fang.com/album/bj/s24/43/',
        'http://home.fang.com/album/bj/s24/44/',
        'http://home.fang.com/album/bj/s24/45/',
        'http://home.fang.com/album/bj/s24/46/',
        'http://home.fang.com/album/bj/s24/47/',
        'http://home.fang.com/album/bj/s24/48/',
        'http://home.fang.com/album/bj/s24/49/',
        'http://home.fang.com/album/bj/s24/50/',
        'http://home.fang.com/album/bj/s24/51/',
        'http://home.fang.com/album/bj/s24/52/',
        'http://home.fang.com/album/bj/s24/53/',
        'http://home.fang.com/album/bj/s24/54/',
        'http://home.fang.com/album/bj/s24/55/',
        'http://home.fang.com/album/bj/s24/56/',
        'http://home.fang.com/album/bj/s24/57/',
        'http://home.fang.com/album/bj/s24/58/',
        'http://home.fang.com/album/bj/s24/59/',
        'http://home.fang.com/album/bj/s24/60/',
        ]

    def parse_detail(self,response):
        item = response.meta["item"]
        #标签
        tags = response.xpath('//div[@class="tag"]/ul/a/text()').extract()
        #大图地址
        bigpicurls = response.xpath('//head/meta[2]/@content').extract()
        item['tag'] = str(tags)
        item['bigpicurl'] = bigpicurls[0]
        yield item



    def parse(self, response):
        print(response.url)
        # 图片标题
        titles = response.xpath('//div[@class="photo_list"]/ul/li/ol/p/a/text()').extract()
        # 详情页url
        urls = response.xpath('//li[contains(@id,"img_")]/ol/p/a/@href').extract()
        # 缩略图地址
        imgs = response.xpath('//img[contains(@id,"photo_")]/@src').extract()

        # 总页数
        #page_num = response.xpath('//div[@id="zxxgtlist_B07_01"]/ul/i[2]/a/@href').extract()
        #page_num = "".join(page_num).split("/")[-2]
        #print(type(page_num))

        ids = []
        items = []
        for url in urls:
            # 图片id
            id = "".join(url).split("/")[4].split('_')[0]
            ids.append(id)

        for i in range(len(urls)):
            item = MispiderItem()
            item['title'] = titles[i]
            item['smallpicurl'] = 'http:' + imgs[i]
            item['pictureid'] = ids[i]
            item['detailsurl'] = urls[i]

            items.append(item)


        for item in items:
            details_url = 'http:' + item['detailsurl']
            yield scrapy.Request(details_url, callback=self.parse_detail, meta={"item": item}, dont_filter=True)











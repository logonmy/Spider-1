# -*- coding: utf-8 -*-
import scrapy
import json
import requests
from dzSpider.items import DzspiderItem,DzcspiderItem
from lxml import etree
# from fake_useragent import UserAgent

class DzdpspiderSpider(scrapy.Spider):
    name = 'dzdpSpider'
    pg = 1
    # allowed_domains = ['http://www.dianping.com/']
    # start_urls = ['http://www.dianping.com/beijing/ch90/g25475',]
    def start_requests(self):
        # ua = UserAgent()
        # headers = {'User-Agent': ua.random}
        # url = 'http://www.dianping.com/beijing/ch90/g25475'
        locations = ['r14','r15','r16']
        for loc in locations:
            # time.sleep(random.randint(5, 10))
            url = 'http://www.dianping.com/beijing/ch90/g25475' + loc
            # print('====列表页各区url====', url)
            # print('====列表页各区url====', headers)
            yield scrapy.Request(url,callback=self.parse)

    def parse_detail(self,response):
        item1 = DzspiderItem()
        item2 = DzcspiderItem()

        shop_id = response.url[response.url.rfind('/') + 1:]
        # 用户评论url
        comment_url = 'http://www.dianping.com/jiazhuang/shop/ajax/designreviewlist?_nr_force=1536999855199&act=getreviewlist&shopid=' + str(shop_id) + '&tab=all&order=&page='

        # 信息源
        item1['sourcename'] = '大众点评'
        # 来源url
        sourceurl = response.url
        item1['sourceurl'] = sourceurl

        # 公司名
        companyname = response.xpath('//div[@class="shop-name"]/h1/text()').extract()
        companyname = ''.join(companyname)
        if len(companyname) > 0:
            item1['companyname'] = companyname
            item2['companyname'] = companyname
        else:
            item1['companyname'] = ' '
            item2['companyname'] = ' '
        # 地址
        address = response.xpath('//div[@id="J_boxDetail"]/div/p/span/@title').extract()
        address = ''.join(address)
        if len(address) > 0:
            item1['address'] = address
        else:
            item1['address'] = ' '
        # 电话
        tel = response.xpath('//div[@class="shop-contact telAndQQ"]/span/strong/text()').extract()
        tel = ''.join(tel)
        if len(tel) > 0:
            item1['tel'] = tel
        else:
            item1['tel'] = ' '
        # 公司介绍
        compcontent = response.xpath('//div[@class="business-card clearfix"]/p/text()').extract()
        compcontent = "".join(compcontent).strip()
        if len(compcontent) > 0:
            item1['compcontent'] = compcontent
        else:
            item1['compcontent'] = ' '
        # 合同均价
        avgprice = response.xpath('//span[@class="avg-price"]/text()').extract()
        avgprice = "".join(avgprice).replace('合同均价：', '')
        if len(avgprice) > 0:
            item1['avgprice'] = avgprice
        else:
            item1['avgprice'] = ' '
        yield item1

        page_num = response.xpath('//a[@class="pageLink"]/text()')
        if page_num:
            response_user = requests.get(comment_url)
            response_content = json.loads(response_user.text)
            response_str = response_content['msg']
            response_html = etree.HTML(response_str)
            # 用户评论最大页码
            max_num = response_html.xpath('//a[@class="pageLink"]/text()')[-1:]
            print('=====max_num======',max_num)
            max_num = "".join(max_num)
            for i in range(1, int(max_num)+1):

                # 拼接用户评论页url
                new_url = comment_url + str(i)
                response = requests.get(new_url)
                response_content = json.loads(response.text)
                response_str = response_content['msg']
                response_html = etree.HTML(response_str)

                div = response_html.xpath('//div[@class="comment-list"]/ul/li')

                for dd in div:
                    # 信息源
                    item2['sourcename'] = '大众点评'
                    #来源url
                    item2['sourceurl'] = new_url
                    # 用户名
                    username = dd.xpath('./div[2]/div[1]/div[1]/p/a/text()')[0]
                    item2['username'] = username

                    # 评论时间
                    commtime = dd.xpath('.//span[@class="time"]/text()')[0]
                    item2['commtime'] = commtime

                    # 评论内容
                    commcontent = dd.xpath('./div[2]/div[2]/div[2]/text()')
                    if commcontent:
                        commcontent = "".join(commcontent).strip()
                        item2['commcontent'] = commcontent
                    else:
                        commcontent = dd.xpath('./div[2]/div[2]/div/text()')
                        commcontent = "".join(commcontent).strip()
                        item2['commcontent'] = commcontent


                    # 装修形式
                    formstyle = dd.xpath('./div[2]/ul[2]/li[1]/text()')
                    if formstyle:
                        formstyle = "".join(formstyle).replace('形式:', '')
                        item2['formstyle'] = formstyle
                    else:
                        item2['formstyle'] = ' '


                    # 装修类型
                    category = dd.xpath('./div[2]/ul[2]/li[2]/text()')
                    if category:
                        category = "".join(category).replace('类型：', '')
                        item2['category'] = category
                    else:
                        item2['category'] = ' '


                    # 面积
                    areas = dd.xpath('./div[2]/ul[2]/li[3]/text()')
                    if areas:
                        areas = "".join(areas).replace('面积：', '')
                        item2['areas'] = areas
                    else:
                        item2['areas'] = ' '


                    # 费用
                    price = dd.xpath('./div[2]/ul[2]/li[4]/text()')
                    if price:
                        price = "".join(price).replace('费用：', '')
                        item2['price'] = price
                    else:
                        item2['price'] = ' '


                    # 阶段
                    stage = dd.xpath('./div[2]/ul[2]/li[6]/text()')
                    if stage:
                        stage = "".join(stage)
                        item2['stage'] = stage
                    else:
                        stage = dd.xpath('./div[2]/ul[2]/li[5]/text()')
                        stage = "".join(stage)
                        item2['stage'] = stage

                    # 施工分值
                    constructinscore_list = dd.xpath('./div[2]/div/div[2]/span[1]/text()')
                    if constructinscore_list:
                        constructinscore_str = "".join(constructinscore_list)
                        if constructinscore_str.split('：')[0] == '施工':
                            item2['constructinscore'] = constructinscore_str.split('：')[1]
                        else:
                            item2['constructinscore'] = ' '
                    else:
                        item2['constructinscore'] = ' '

                    # 服务分值
                    servicescore_list = dd.xpath('./div[2]/div/div[2]/span[2]/text()')
                    if servicescore_list:
                        servicescore_str = "".join(servicescore_list)
                        if servicescore_str.split('：')[0] == '服务':
                            item2['servicescore'] = servicescore_str.split('：')[1]
                        else:
                            item2['servicescore'] = ' '
                    else:
                        item2['servicescore'] = ' '

                    yield item2


    def parse_list(self,response):
        # print('====parse_list=======', response.url)
        #得到列表页所有公司链接地址
        com_urls = response.xpath('//div[@class="shop-title"]/h3/a/@href').extract()
        # print('====com_urls=======', com_urls)

        for com_url in com_urls:
            #装修公司信息详情页url
            com_url = 'http:' + com_url
            # ua = UserAgent()
            # headers = {'User-Agent': ua.random}
            # print('====详情页com_url====', com_url)
            # print('====详情页com_url========', headers)
            # time.sleep(random.randint(5, 10))
            # yield scrapy.Request(comment_url, callback=self.parse_comment_detail)
            yield scrapy.Request(com_url,callback=self.parse_detail,dont_filter=True)


    def parse(self, response):
        # print("=====parse_url======",response.url)
        pg = 0
        pages = response.xpath('//div[@class="pages"]/a/text()').extract()
        if len(pages) > 0:
            pg = pages[len(pages) - 2]
        #最大页码
        pg = int(str(pg)) + 1
        url = str(response.url)
        for p in range(1, pg):
            # ua = UserAgent()
            # headers = {'User-Agent': ua.random}
            #列表页链接地址
            # time.sleep(random.randint(5, 10))
            ul = url + 'p' + str(p)
            # print('====列表页ul========', ul)
            # print('====列表页ul========', headers)
            yield scrapy.Request(ul,callback=self.parse_list,dont_filter=True)












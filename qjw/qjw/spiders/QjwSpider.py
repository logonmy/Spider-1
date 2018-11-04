# -*- coding: utf-8 -*-
import scrapy
from qjw.items import QjwcItem,QjwItem
from fake_useragent import UserAgent
# from urllib import parse

class QjwspiderSpider(scrapy.Spider):
    name = 'QjwSpider'
    pg = 1

    def start_requests(self):
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        locations = ['beijing','shanghai','shenzhen','chengdu','chongqing','tianjin','wuhan','suzhou','wuxi','nanjing','nantong','hefei','kunshan','fuzhou','hangzhou','changsha','nanchang','nanning','xian','kunming','guiyang','taiyuan','zhengzhou','qingdao','jinan','shijiazhuang','shenyang','changchun','dalian','dalian','guangzhou','gddg']
        for loc in locations:
            # time.sleep(random.randint(5, 10))
            url = 'http://www.jia.com/zx/%s/company/gexingbao/?order=koubei&' %(loc)
            # print('====列表页各区url====', url)
            # print('====列表页各区url====', headers)
            yield scrapy.Request(url,callback=self.parse,dont_filter=False,headers=headers)


    def parse_three(self,response):
        item2 = response.meta['item']
        div = response.xpath('//div[@class="comment-con"]/div/ul')

        # gongdi_url = response.url.split('_')[0]
        # googurl = gongdi_url + '_gongdi/'

        for dd in div:
            # 信息源
            item2['sourcename'] = '齐家网'
            # 来源url
            item2['sourceurl'] = response.url
            # 用户名
            username = dd.xpath('./li[1]/p/text()')[0].extract()
            item2['username'] = username

            # 评论时间
            commtime = dd.xpath('./li[3]/p[2]/text()')[0].extract()
            item2['commtime'] = commtime

            # 评论内容
            commcontent = dd.xpath('./li[2]/p[1]/text()').extract()
            if commcontent:
                commcontent = "".join(commcontent).strip()
                item2['commcontent'] = commcontent
            else:
                item2['commcontent'] = ' '

            # 阶段
            stage = dd.xpath('./li[2]/p[2]/a/span[2]/text()').extract()
            if stage:
                stage = "".join(stage)
                item2['stage'] = stage
            else:
                item2['stage'] = ' '

            # 装修形式
            item2['formstyle'] = ' '

            # 装修类型
            item2['category'] = ' '

            # 面积
            item2['areas'] = ' '
            #费用
            item2['price'] = ' '

            # 专业技能
            constructinscore = dd.xpath('//li[@class="user-result"]/div[1]/text()').extract()
            if constructinscore:
                con = "".join(constructinscore)
                if con == '专业技能：':
                    s = dd.xpath('//li[@class="user-result"]/div[1]/span/span/i/@class').extract()
                    item2['constructinscore'] = s.count('on')
                else:
                    item2['constructinscore'] = ' '
            else:
                item2['constructinscore'] = ' '

            # 服务态度
            servicescore = dd.xpath('//li[@class="user-result"]/div[2]/text()').extract()
            if servicescore:
                con = "".join(servicescore)
                if con == '服务态度：':
                    s = dd.xpath('//li[@class="user-result"]/div[2]/span/span/i/@class').extract()
                    item2['servicescore'] = s.count('on')
                else:
                    item2['servicescore'] = ' '
            else:
                item2['servicescore'] = ' '

            yield item2


    def parse_detail(self, response):
        item1 = QjwItem()
        item2 = QjwcItem()

        s = response.url
        # 信息源
        item1['sourcename'] = '齐家网'
        # 来源url
        sourceurl = s
        item1['sourceurl'] = sourceurl

        # 公司名
        companyname = response.xpath('//div[@class="des"]/h3/span/text()').extract()
        companyname = ''.join(companyname).strip()
        if len(companyname) > 0:
            item1['companyname'] = companyname
            item2['companyname'] = companyname
        else:
            item1['companyname'] = ' '
            item2['companyname'] = ' '
        # 地址
        item1['address'] = ' '
        # 电话
        item1['tel'] = ' '
        # 公司介绍
        compcontent = response.xpath('//textarea/text()').extract()
        compcontent = "".join(compcontent).strip()
        if len(compcontent) > 0:
            item1['compcontent'] = compcontent
        else:
            item1['compcontent'] = ' '
        # 合同均价
        item1['avgprice'] = ' '
        yield item1

        page_num = response.xpath('//div[@class="p_page"]/a/text()').extract()
        if len(page_num) > 0:
            # 用户评论最大页码
            pg = page_num[len(page_num) - 2]
            # 最大页码
            max_num = int(str(pg)) + 1
            for i in range(1, int(max_num) + 1):
                comment_url = s + '0/1/' + str(i)
                ua = UserAgent()
                headers = {'User-Agent': ua.random}
                yield scrapy.Request(comment_url, callback=self.parse_three, dont_filter=False, headers=headers,meta={"item": item2})

    def parse_list(self, response):
        # print('====parse_list=======', response.url)
        # 得到列表页所有公司链接地址
        com_urls = response.xpath('//div[@class="company-list"]/div/div/a/@href').extract()
        # print('====com_urls=======', com_urls)

        for com_url in com_urls:
            # 装修公司信息详情页url
            com_url = 'http:' + com_url
            url = com_url[0:com_url.rfind('/')]
            # 用户评论url
            comment_url = url + '_comment/'
            ua = UserAgent()
            headers = {'User-Agent': ua.random}
            print('====详情页com_url====', com_url)
            print('====详情页com_url========', headers)
            # time.sleep(random.randint(5, 10))
            # yield scrapy.Request(comment_url, callback=self.parse_comment_detail)
            yield scrapy.Request(comment_url, callback=self.parse_detail, dont_filter=False, headers=headers)

    def parse(self, response):
        # print("=====parse_url======",response.url)
        pg = 0
        pages = response.xpath('//div[@class="p_page"]/a/text()').extract()
        if len(pages) > 0:
            pg = pages[len(pages) - 2]
        # 最大页码
        pg = int(str(pg)) + 1
        url = str(response.url)
        for p in range(1, pg):
            ua = UserAgent()
            headers = {'User-Agent': ua.random}
            # 列表页链接地址
            # time.sleep(random.randint(5, 10))
            ul = url + 'page=' + str(p)
            # print('====列表页ul========', ul)
            # print('====列表页ul========', headers)
            yield scrapy.Request(ul, callback=self.parse_list, dont_filter=True, headers=headers)

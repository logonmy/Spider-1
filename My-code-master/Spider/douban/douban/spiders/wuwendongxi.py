# -*- coding: utf-8 -*-
import scrapy
import csv
import os

# 'scrapy startproject object_name' 创建scrapy项目命令 这里object_name用douban

# 'scrapy crawl name' 测试命令 这里name用 dongxi_comment


class wuwendongxi(scrapy.Spider):
    folder_path = '/Users/LiweiHE/acquisition'  # where to store
    name = 'dongxi_comment'
    pages = 0
    headers = {
        'Connection': 'keep - alive',  # 保持链接状态
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:59.0) Gecko/20100101 Firefox/59.0'
    }

    cookie = 'll="108099"; bid=Ze9hut8g1xM; __utmc=30149280; _ga=GA1.2.1011585287.1522412857; _gid=GA1.2.2092290661.1522412868; dbcl2="174682013:Wonpugfb5T8"; ck=VPt9; __yadk_uid=9Li7akBZAjFSZ6UsblCCWlcihJYwX7bM; push_doumail_num=0; __utmv=30149280.17468; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1522463539%2C%22https%3A%2F%2Fwww.google.com.au%2F%22%5D; _pk_ses.100001.8cb4=*; ap=1; push_noty_num=0; __utma=30149280.1011585287.1522412857.1522412857.1522463543.2; __utmz=30149280.1522463543.2.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmt=1; __utmb=30149280.2.10.1522463543; _pk_id.100001.8cb4=c489e3fa346b0016.1522412852.2.1522463571.1522412871.'
    start_urls = [
        "https://movie.douban.com/subject/6874741/comments?start={}&limit=20&sort=new_score&status=P&percent_type="
    ]

    def start_requests(self):
        itemDict = {}
        items = self.cookie.split(';')
        for item in items:
            key = item.split('=')[0].replace(' ', '')
            value = item.split('=')[1]
            itemDict[key] = value
        self.cookie = itemDict

        self.log('Creating folder')
        self.create_folder(self.folder_path)
        self.log('Change the current file to it')
        os.chdir(self.folder_path)  # 切换路径至上面创建的文件夹

        yield scrapy.Request(url=self.start_urls[0], headers=self.headers, cookies=self.cookie, callback=self.parse)

    def parse(self, response):

        self.log('start')
        divs = response.xpath('//div[@class="comment"]')
        with open('douban.txt', 'a+', encoding='utf-8', newline='') as csvf:
            writer = csv.writer(csvf)
            self.log('open file')

            for div in divs:
                comment_votes = div.xpath('./h3/span[@class="comment-vote"]/span[@class="votes"]/text()')[0].extract()
                if int(comment_votes) > 10:
                    comment = div.xpath('./p/text()').extract_first().strip()
                    time = div.xpath(
                        './h3/span[@class="comment-info"]/span[@class="comment-time "]/text()').extract_first().strip()
                    # ./h3/span[@class="comment-info"]/span["comment-time "]/text()'
                    detail = (time, comment)
                    writer.writerow(detail)
            self.log('close file')

        # next page(https://docs.scrapy.org/en/latest/intro/tutorial.html#following-links)
        self.pages += 1
        url = response.css('a.next::attr(href)').extract_first()

        if url:
            url = "https://movie.douban.com/subject/6874741/comments" + url
            return scrapy.Request(url=url, headers=self.headers, cookies=self.cookie, callback=self.parse)

        else:
            self.log('finished, totally: ' + str(self.pages) + 'pages')


    def create_folder(self, path):
        path = path.strip()
        is_valid = os.path.exists(path)
        if not is_valid:
            self.log('Create a file called ', path)
            os.makedirs(path)
        else:
            self.log('This folder is already existed.')



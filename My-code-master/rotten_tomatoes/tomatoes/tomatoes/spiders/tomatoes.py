import scrapy
import xlwt
import os
import re

# 'scrapy startproject object_name' 创建scrapy项目命令 这里object_name用douban

# 'scrapy crawl name' 测试命令 这里name用 tomatoes_comment


class tomatoes(scrapy.Spider):
    folder_path = '/Users/LiweiHE/acquisition'  # where to store
    name = 'tomatoes_comment'
    current_page = 0
    page = 0
    bh = 0

    start_urls = [
        "https://www.rottentomatoes.com/m/a_quiet_place_2018/reviews/"
    ]

    def start_requests(self):
        self.log('Creating folder')
        self.create_folder(self.folder_path)
        self.log('Change the current file to it')
        os.chdir(self.folder_path)

        yield scrapy.Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response):
        self.log('start')
        divs = response.xpath('//div[@class="review_desc"]')
        self.log('open file')

        if self.current_page == 0:
            global workbook
            global worksheet
            global style
            workbook = xlwt.Workbook(encoding='ascii')
            worksheet = workbook.add_sheet('My Worksheet')
            style = xlwt.XFStyle()  # 初始化样式
            font = xlwt.Font()  # 为样式创建字体
            font.name = 'Times New Roman'
            font.bold = True  # 黑体
            # font.underline = True # 下划线
            # font.italic = True # 斜体字
            style.font = font  # 设定样式
            worksheet.write(0, 0, "ID", style)
            worksheet.write(0, 1, "Grades", style)
            worksheet.write(0, 2, "length of Comment", style)

            self.page = response.xpath('//span[@class="pageInfo"]/text()').extract_first().strip()
            self.page = re.findall(r"\d+", self.page)
            self.page = int(self.page[-1])



        for i in range(0, len(divs)):
            comment = divs[i].xpath('./div[@class="the_review"]/text()').extract_first().strip()
            length = len(comment)
            core = divs[i].xpath(
                    './div[@class="small subtle"]/text()')[1].extract().strip()
            core = re.findall(r"\d+\.?\d*", core)
            if core:
                core[0] = float(core[0])
                core[1] = float(core[1])
                core = core[0]/core[1]
            else:
                core = 0

            self.bh += 1
            worksheet.write(self.bh, 0, self.bh, style)
            worksheet.write(self.bh, 1, core, style)
            worksheet.write(self.bh, 2, length, style)

        self.log('close file')
        # next page(https://docs.scrapy.org/en/latest/intro/tutorial.html#following-links)
        self.current_page += 1
        if self.page >= self.current_page:
            url = "https://www.rottentomatoes.com/" + "m/a_quiet_place_2018/reviews/?page=" + str(self.current_page) + "&sort="
            return scrapy.Request(url=url, callback=self.parse)
        else:
            workbook.save('comments.xls')
            self.log('finished, totally: ' + str(self.current_page - 1) + 'pages')



    def create_folder(self, path):
        path = path.strip()
        is_valid = os.path.exists(path)
        if not is_valid:
            self.log('Create a file called ', path)
            os.makedirs(path)
        else:
            self.log('This folder is already existed.')
from scrapy.spider import CrawlSpider
from scrapy import Request, FormRequest
import json
from Crawlers.items import CrawlersItem


class LagouSpider(CrawlSpider):
    name = "lagouSpider"
    host = "https://www.lagou.com"
    start_urls = ["https://www.lagou.com/jobs/list_python"]
    # start_urls = ["https://www.lagou.com/zhaopin/webqianduan/"]
    page = 1
    header = {
        "Referer": " https://www.lagou.com/jobs/list_python",
        # "Referer": " https://www.lagou.com/zhaopin/webqianduan/",
        "Cookie": "user_trace_token=20180715134349-b7771ebf-990b-4b45-9f8e-4e49c2f59f78; _ga=GA1.2.2143932590."
                  "1531633431; LGUID=20180715134351-0d94b395-87f2-11e8-9dec-5254005c3644; showExpriedIndex=1; "
                  "showExpriedCompanyHome=1; showExpriedMyPublish=1; hasDeliver=1; index_location_city=%E5%8C%"
                  "97%E4%BA%AC; _gid=GA1.2.1780780338.1532266786; JSESSIONID=ABAAABAAAFCAAEG855575F81B3DC781BA"
                  "912E8A12E2255B; _gat=1; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1531633465,1532142182,15323"
                  "03517,1532343900; LGSID=20180723190500-3e58de54-8e68-11e8-a34e-525400f775ce; PRE_UTM=; PRE_"
                  "HOST=; PRE_SITE=; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist_python; _putrc=4000B85"
                  "22701349D; login=true; unick=%E6%9D%8E%E5%88%9A; gate_login_token=d6155ab4a16ffd873e4628825"
                  "696bd9154ecd4a8f917534d; SEARCH_ID=14ff864712ef492eb6c02c1181763b37; Hm_lpvt_4233e74dff0ae5"
                  "bd0a3d81c6ccf756e6=1532343902; LGRID=20180723190503-3fb199cb-8e68-11e8-a34e-525400f775ce",
    }

    def parse(self, response):
        with open('lagou.html', 'w') as f:
            f.write(response.text)
        print(response.headers.getlist('Set-Cookie'))
        formdata = {"kd": "python", "pn": '1', "first": 'true'}
        url = "https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false"
        yield FormRequest(url, headers=self.header, callback=self.parse_lagou, formdata=formdata)

    def parse_lagou(self, response):
        print(response.text)
        text = json.loads(response.text)
        res = []
        try:
            res = text["content"]["positionResult"]["result"]
        except:
            pass
        if len(res) > 0:
            for position in res:
                item = CrawlersItem()
                try:
                    item['title'] = position['positionName']
                    item['education'] = position['education']
                    item['company'] = position['companyFullName']
                    item['experience'] = position['workYear']
                    item['location'] = position['city']
                    item['salary'] = position['salary']
                except:
                    pass
                yield item
            self.page += 1
            url = "https://www.lagou.com/jobs/positionAjax.json?needAddtionalResult=false"
            formdata = {"kd": "python", "pn": str(self.page), "first": "false"}
            print('formdata: ', formdata)
            yield FormRequest(url, headers=self.header, callback=self.parse_lagou, formdata=formdata)
        else:
            print("爬虫结束了！")

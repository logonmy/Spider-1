# -*- coding: utf-8 -*-

# Scrapy settings for xiaomiSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'xiaomiSpider'

SPIDER_MODULES = ['xiaomiSpider.spiders']
NEWSPIDER_MODULE = 'xiaomiSpider.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'xiaomiSpider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)

# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs

# 设置爬取时间间隔
# DOWNLOAD_DELAY = 3


# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:

# 添加请求头
DEFAULT_REQUEST_HEADERS = {
'Host': 'koubei.baidu.com',
'Connection': 'keep-alive',
'Pragma': 'no-cache',
'Cache-Control': 'no-cache',
'Accept': 'application/json, text/javascript',
'X-Requested-With': 'XMLHttpRequest',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
'Content-Type': 'application/x-www-form-urlencoded',
'Referer': 'https://koubei.baidu.com/s/e4dcdf6e1fe4ce0a93c56369b72c059a?src=searchexp',
'Accept-Language': 'zh-CN,zh;q=0.9',
'Cookie': 'PSTM=1526975645; BIDUPSID=18A1B3C6E73CBCA06B2B1C24569666A3; BAIDUID=F7EA9C2A0009F724D8D4612CF26F6BC9:SL=0:NR=10:FG=1; __cfduid=dd6e4157ff7493ecb18b27253a2b9d0b31528453571; BDUSS=GE1Uml2a1gzR3hTb3R-OUd6WEFoRnJObENZMDBULWM1Mlh-ZzBBbTVTTFU0bnRiQVFBQUFBJCQAAAAAAAAAAAEAAAD0oWBA6MnSudi8tKbFrtf5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANRVVFvUVVRbN; BDORZ=FFFB88E999055A3F8A630C64834BD6D0; MCITY=-%3A; KB_REF_KEY=https%3A%2F%2Fwww.baidu.com%2Fs%3Fword%3D%25E7%2599%25BE%25E5%25BA%25A6%25E5%258F%25A3%25E7%25A2%2591%26tn%3D92549761_hao_pg%26ie%3Dutf-8%26sc%3DUWY4nWRYrHTvnNqCmyqxTAThIjYkPHndPWDdPHcLrH04FhnqpA7EnHc1Fh7W5HcYnWbLPWndnW6%26ssl_sample%3Ds_4%252Cs_10%26srcqid%3D2347221148677828679; BDRCVFR[dXNllpFHdu_]=mk3SLVN4HKm; logid=; PSINO=5; Hm_lvt_a236098d9e01fb7877977ac4f7d38d64=1535615550,1535617389,1535617418; CKSQKb=IQ2NCsH49K4KZEHLLLHvm%2A8IjmM7OIp0FBK-i5x74KuHJLFDSjxsKrCH8gQ0S8%2AQ4%2Ajh48xfCXW%2Ayar4AES-6U; H_PS_PSSID=; Hm_lpvt_a236098d9e01fb7877977ac4f7d38d64=1535624831',
}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'xiaomiSpider.middlewares.XiaomispiderSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# 开启中间件
# DOWNLOADER_MIDDLEWARES = {
#     # 'xiaomiSpider.middlewares.RandomProxySpiderMiddleware': 530,
#     # 'xiaomiSpider.middlewares.RandomUserAgentSpiderMiddleware': 531,
#     'xiaomiSpider.middlewares.XiaomispiderDownloaderMiddleware': 543,
# }

# 配置日志
LOG_FILE = "xiaomiSpider.log"
# 日志等级  一般设置为DEBUG
LOG_LEVEL = "DEBUG"


# 设置爬取深度
# DEPTH_LIMIT = 2

# USER_AGENTS = [
#     # 模拟客户端身份User-Agent
#     "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
#     "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
# ]

#
# PROXY_LIST = [
#    #没有账号和密码的代理服务器
#    # 代理服务器ip池
#    #  {"ip_port": "118.190.145.138:9001", "user_password": None},
#    #  {"ip_port": "49.69.125.62:53281", "user_password": None},
#     # {"ip_port": "58.18.225.234:80", "user_password": None},
#     # {"ip_port": "106.14.206.26:8118", "user_password": None},
#     # {"ip_port": "115.223.215.144:9000", "user_password": None},
#     # {"ip_port": "123.133.206.4:9000", "user_password": None},
#     # {"ip_port": "27.214.49.138:9000", "user_password": None},
#     # {"ip_port": "114.234.83.179:9000", "user_password": None},
#     # {"ip_port": "210.72.14.142:80", "user_password": None},
#     # {"ip_port": "113.251.218.218:8123", "user_password": None},
#     # {"ip_port": "218.64.148.182:9000", "user_password": None},
#     # {"ip_port": "115.223.212.32:9000", "user_password": None},
#     # {"ip_port": "183.158.203.57:9000", "user_password": None},
#     # {"ip_port": "182.105.1.151:9000", "user_password": None},
#     # {"ip_port": "115.210.31.204:9000", "user_password": None},
#     # {"ip_port": "111.160.123.110:80", "user_password": None},
#     # {"ip_port": "118.117.137.76:9000", "user_password": None},
#     # {"ip_port": "117.90.1.53:9000", "user_password": None},
#     # {"ip_port": "218.6.16.233:8118", "user_password": None},
#     # {"ip_port": "218.64.147.130:9000", "user_password": None},
#     # {"ip_port": "115.212.39.248:9000", "user_password": None},
#     # {"ip_port": "114.235.23.13:9000", "user_password": None},
#     # {"ip_port": "117.90.5.58:9000", "user_password": None},
#     # {"ip_port": "117.90.2.138:9000", "user_password": None},
#     # {"ip_port": "115.218.215.250:9000", "user_password": None},
#     # {"ip_port": "180.76.136.77:9999", "user_password": None},
#     # {"ip_port": "183.3.221.186:8118", "user_password": None},
# ]
# #


# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html

# 项目管道
ITEM_PIPELINES = {
   'xiaomiSpider.pipelines.XiaomispiderPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

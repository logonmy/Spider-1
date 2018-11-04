# -*- coding: utf-8 -*-

# Scrapy settings for miSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'miSpider'

SPIDER_MODULES = ['miSpider.spiders']
NEWSPIDER_MODULE = 'miSpider.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'miSpider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
   #'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   #'Accept-Language': 'en',

'ser-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',

'Cookie': '__jsluid=c73c4bae163643ae9a0341c64f22d4f7; global_cookie=bzk2pbwf54omc4vod6pq3rytk1vjlnbpdoq; city=www; Integrateactivity=notincludemc; sfut=9C9EB95A5C73EF52A34EEB3A73D353906500153D2190CAD679102AA0D4AF378146A89A0C258ACBDDF069F5F06BBF7F42541D291ABAFAD634F2932FE3C512D6F05FED27D32B13D073DC14EC6516A722A823394F5AB7A1177FEE4EFF8A7997367E; new_loginid=108095844; login_username=passport3796374902; sf_source=; s=; HomeIdeabook=HomeIdeabook_dealerid=0&HomeIdeabook_usertype=1; Captcha=725A61456D314833365A78696E547177704D6572664F6D4D6576727A48554A363962584536757138394673474243723358394A554955686F6F6B6B526A57363536446E4B4B78662B3665513D; unique_cookie=U_4sfkp2w38kmmp4d50asp82s2k1djlofdhuk*99; homealbumsearchurl=&limit=36&start=2124&cityname=%b1%b1%be%a9&searchtype=1&sortid=24&cityname=%b1%b1%be%a9&searchall=1&orsearch=1&isnewvalid=1|60|42168|36; homealbuminfosearchurl=&limit=36&start=2124&cityname=%b1%b1%be%a9&searchtype=1&sortid=24&cityname=%b1%b1%be%a9&searchall=1&orsearch=1&isnewvalid=1|60|42168|36'
}

#添加splash服务器地址：
#SPLASH_URL = 'http://192.168.99.100:8050'


#数据库的配置信息
#MYSQL_HOST = '192.168.0.2'
#MYSQL_DBNAME = 'webspider'         #数据库名字
#MYSQL_USER = 'gpadmin'             #数据库账号
#MYSQL_PASSWD = 'gpadmin'         #数据库密码
#MYSQL_PORT = 5432               #数据库端口，在dbhelper中使用



# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
    #'miSpider.middlewares.MispiderSpiderMiddleware': 543,
    #'miSpider.middlewares.SplashDeduplicateArgsMiddleware': 543,
#}

#DUPEFILTER_CLASS='scrapy_splash.SplashAwareDupeFilter'
#HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {

    #'miSpider.middlewares.SplashCookiesMiddleware': 723,
   # 'miSpider.middlewares.SplashMiddleware': 725,
   # 'miSpider.middlewares.MispiderDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'miSpider.pipelines.MispiderPipeline': 300,
# }
ITEM_PIPELINES = {

	'miSpider.pipelines.MispiderImagePipeline': 200,
	'miSpider.pipelines.CrawlfangPipeline': 300,
	'miSpider.pipelines.MispiderPipeline': 400,
}

# 配置图片的保存路径
IMAGES_STORE = "./Images"

# 配置日志
LOG_FILE = "xiaomiSpider.log"
LOG_LEVEL = "DEBUG"


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

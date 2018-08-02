# BeautifulSoup as a tool to grab the useful info from website
# https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/#keyword
# r.text is the content of the response in unicode, and r.content is the content of the response in bytes.
# http://selenium-python.readthedocs.io/index.html

# Purpose: code here is used to pick up urls and pictures which related to topics I'm interested in
# the target website is an website based in Taiwan: https://wuso.me/forum-jsav-1.html

import requests
from bs4 import BeautifulSoup, re
from selenium import webdriver  #import the webdriver from Selenium
from selenium.webdriver.common.keys import Keys  #import Keys
import os
import time


class BeautifulPicture():
    def __init__(self):
        #mimic the chrome by providing a head into request 
        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:59.0) Gecko/20100101 Firefox/59.0'}  
        self.web_url = 'https://wuso.me/forum-jsav-1.html' # target website
        self.folder_path = '/Users/LiweiHE/acquisition'  # where to store
        self.driver = None


    def requests(self,url):
        r = requests.get(url)
        return r


    def create_folder(self,path):
        path = path.strip()
        is_valid = os.path.exists(path)
        if not is_valid:
            print('Create a file called ', path)
            os.makedirs(path)
        else:
            print('This folder is already existed.')

    def next_page(self):
        start = self.web_url[:-6]
        page = int(self.web_url[-6]) + 1
        end = self.web_url[-5:]

        self.web_url = start + str(page) + end


    def save(self, url, name):  ##store url
        print('start to store url')
        # https://docs.python.org/3/library/functions.html?highlight=open#open
        f = open(name, 'w')
        f.write(url)
        print(name, 'url received！')
        f.close()

    def save_img(self, url, name):  
        print('Start to pull the pic...')
        img = self.requests(url)
        # wait for the 
        time.sleep(5)
        file_name = name + '.jpg'
        # more info about 'open' in https://docs.python.org/3/library/functions.html?highlight=open#open
        f = open(file_name, 'ab')
        f.write(img.content)
        print(file_name, 'pulled！')
        f.close()

    def get_url(self):
        print('start the GET ')
        self.driver.get(self.web_url)  # send request
        print('Start to find all <a>')
        # keywords is a variable 
        all_a = BeautifulSoup(self.driver.page_source, 'lxml').find_all('a', class_='z', title=re.compile("keywords"))

        # print('start to create folder')
        # self.create_folder(self.folder_path)
        # print('start to change path')
        # os.chdir(self.folder_path)  # change the path to the target.
        print("The number of <a> is：", len(all_a))  # return the number of <a>

        old_urls = self.get_files(self.folder_path)

        for url in all_a:
            name = url['title']

            if name in old_urls:
                print("this url is already existing")
                continue
            else:
                self.save(url['href'], name)


    def get_pic_request(self):
        print('Start the GET')
        r = self.requests(self.web_url)
        print('Start to find all the <img>')
        text = BeautifulSoup(r.text, 'lxml')
        all_images = text.find_all('img', alt=re.compile("keywords"))  # find all the img with a "keywords" 
        print('create file')
        self.create_folder(self.folder_path)
        print('change the current file to it')
        os.chdir(self.folder_path)  # change the path to the target.
        i = 0
        all_pics = self.get_files(self.folder_path)
        for img in all_images:
            name_start_pos = img.index('photo')
            name_end_pos = img.index('?')
            name = img[name_start_pos:name_end_pos] + '.jpg'

            if name in all_pics:
                print("this pic is already existing")
                continue
            else:
                print(img)
                self.save_img(img['src'], name)
                i +=1

    def scroll_down(self, driver, times):
        for i in range(times):
            print("start ", str(i + 1), " times' scroll-down")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  #execute the JavaScript to scroll down
            print(str(i + 1), " times' scroll-down finished")
            print("waiting for the ", str(i + 1), "times' page loading......")
            time.sleep(20)  # wait for 20ms, so that page loading can finish in time.

    def get_files(self, path):
        pic_names = os.listdir(path)
        return pic_names

    def init_broswer(self):
        print('send get request')
        chromedriver = "/Users/LiweiHE/anaconda3/chromedriver"
        os.environ["webdriver.chrome.driver"] = chromedriver
        self.driver = webdriver.Chrome(chromedriver)  # initialise webdriver

    def close(self):
        self.driver.close()  #close webdriver

    def get_pic_Selenium(self):
        self.driver.get(self.web_url)  #send the url
        # if there is iframe in the page
        # driver.switch_to.frame("g_iframe")
        # self.scroll_down(driver=driver, times=1)
        print('grabing all <a>s')
        # css labels need '_' to identify
        all_a = BeautifulSoup(self.driver.page_source, 'lxml').find_all('a', class_='z', title=re.compile('keywords'))
        print("the number of <a> is ：", len(all_a))  #check the number of <a>

        pic_names = self.get_files(self.folder_path)
        i = 1
        for a in all_a:
            img = a.find('img')
            url = a['href']
            img_url = 'https://wuso.me/' + img['src']
            print('the content of <src> in <a>：', img_url)
            #first_pos = img_str.index('"') + 1  # 获取第一个双引号的位置，然后加1就是url的起始位置
            #second_pos = img_str.index('"', first_pos)  # 获取第二个双引号的位置
            #img_url = img_str[first_pos: second_pos]  # 使用Python的切片功能截取双引号之间的内容

            # 截取url中参数前面、网址后面的字符串为图片名
            # name_start_pos = img_url.index('photo')
            # name_end_pos = img_url.index('?')
            # img_name = img_url[name_start_pos: name_end_pos]
            img_name = str(i) + "."+ a['title']
            i +=1
            img_name = img_name.replace('/', '')  # delete all the '/'

            if img_name not in pic_names:
                self.save_img(img_url, img_name)  # call 'save_img' to solve imgs
                self.save(url, img_name)
            else:
                print("this image is already existed：", img_name, "，no more download。")



spider = BeautifulPicture()

spider.init_broswer()

print('Creating file')
spider.create_folder(spider.folder_path)
print('Change the current file to it')
os.chdir(spider.folder_path)  

# go through 20 pages
for i in range(0, 20):
    print('Moving to ', i + 1, ' page')
    spider.get_pic_Selenium()
    spider.next_page()
    print('page ', i + 1, ' finished')

spider.close()

# Note: code here is used to pick up urls and pictures which related to topics I'm interested in
# the target website is an website based in Taiwan.

import requests
from lxml import etree
from bs4 import BeautifulSoup
import re
import json



url = 'http://home.fang.com/album/p28004377_3_203_24/'
response = requests.get(url)

resp = response.text
text = etree.HTML(resp)
#
# print(resp)


biaoqian = text.xpath('//head/meta[2]/@content')
print(biaoqian)




# html = BeautifulSoup(resp,'lxml')
#
# src = html.select('body script')[3]
# cont = ''.join(src).split(";")[0].split('=')[1]
# print(cont)
# print(type(cont))
# print(cont)
# text = json.loads(cont)
# print(type(text))

test = 'http://img11.soufunimg.com/viewimage/zxb/2018_03/13/M13/1B/22/ChCE4FqnOM6IP2ExAAkCwVtTq0EABAAcAPyxTUACQLZ387/432x324c.jpg'
a = test.split('.')[-1]
print(a)

#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)


import logging
import traceback
from logging.handlers import RotatingFileHandler
import uuid
import time
import datetime
import json
import os
import requests
import re
# import scan_china_hr_mobile
import random
# from selenium import webdriver
import urllib

# from ctypes import *
import ctypes

logger = logging.getLogger()

companys = ["天津达人贸易有限公司", "天津峰运设计制造有限公司", "北京德慧智文化传媒有限责任公司", "天津利海同创实业有限公司", "天津恒商源贸易有限公司", "天津格海漫贸易有限公司", "天津麦乐文化创意有限公司", "北京京铁西实业开发有限公司", "北京炫秀场网络科技有限公司", "槌屋(北京)国际贸易有限公司", "冈谷钢机(北京)贸易有限公司", "北京美利同贸易有限公司", "北京麦望麦旺科技有限公司", "北京登倍魏同科技发展有限公司", "北京惠天美达信息科技有限公司", "北京溯源精微科技有限公司", "北京关谷传奇互联网有限公司 ", "天津传奇实业有限公司", "菲比寻常科技有限公司", "名文(北京)文化传播有限公司", "江西新中环工贸发展有限公司", "广州和诚金舆国际贸易", "北京幼特西电子商务有限公司", "江西世海实业投资有限公司", "北京舒美卫生用品有限公司", "许许投资(北京)文化传播有限公司", "广州康相伴生物科技有限公司", "天津麦乐创有限公司", "北京游漫天成网络技术有限公司", "天津和诚金舆国际贸易", "南昌东方家俱实业有限公司", "北京维杰资讯有限公司", "易立友信网络技术有限公司", "广州康相伴生物科技有限公司", "北京大轩科技", "上海林言堂实业有限公司", "天津艺人易道咨询有限公司", "天津泰宇飞鹰电子商务有限公司", "天津仁川开合贸易有限公司", "北京游漫天成网络技术有限公司", "北京炫扬传媒有限公司", "天津普瑞智能科技有限公司", "天津畅乐视享传媒有限公司", "天津舜世达贸易有限公司", "天津盛恒清励事业有限公司", "天津鸿朔源贸易有限公司", "上海许许投资文化传播有限公司", "上海关谷传奇互联网有限公司 ", "上海林言堂实业有限公司", "江西南昌东方家俱实业有限公司", "深圳天河蓝拓电子科技有限公司", "上海同济网络科技有限公司", "北京市施柏丽干洗技术有限公司广州分公司 ", "北京大轩科技", "上海幼特西电子商务有限公司", "北京麦乐科技 ", "北京维杰资讯有限公司", "果动时代(北京)网络技术有限公司", "北京游漫天成网络技术有限公司", "北京舒美卫生用品有限公司", "上海银娴机械设备有限公司", "上海格子教育科技有限公司", "上海游城贸易有限公司", "上海珞漫网络科技有限公司", "上海幼洋服装有限公司", "侣海实业(上海)有限公司", "上海博蓝医药生物科技有限公司", "爱得莱(上海)餐饮管理有限公司", "上海恒骅国际文化传播有限公司", "上海佳诚蓝科技有限公司", "上海索尼亚电子商务有限公司", "洛克克时装(上海)有限公司", "上海尤拉广告有限公司", "上海海盛格实业有限公司", "上海许天下科技网络有限公司", "上海维多克信息技术有限公司", "北京观景艺术发展有限公司", "上海蓝银鼑茂文化传播有限公司", "上海制衡凌展实业有限司", "上海浩洋易远贸易有限公司", "上海炫励普电子技术有限公司", "上海康达易捷网络科技有限公司", "上海创科励旗贸易有限公司", "上海捷泰锋实业有限公司", "上海亚环拓贸易有限公司", "上海惠天锋索信息技术有限公司", "上海凯达路遥信息技术有限公司", "上海舒海拓贸易有限公司", "上海励恒锋贸易有限公司", "上海达鑫创实业有限公司", "上海励瑞轩贸易有限公司", "上海盛纳荣网络技术有限公司", "上海爱乐食尚餐饮管理有限公司", "上海阔游远网络技术有限公司", "上海益信诚贸易有限公司", "上海索励科技有限公司", "上海可尚迪贸易有限公司", "上海日尤客网络技术有限公司", "上海游漫达科技有限公司", "上海泰顺恒达科技有限公司", "上海辉海锋网络技术有限公司", "上海致蓝达贸易有限公司", "上海晟锦祥贸易有限公司", "上海晟凯能科技有限公司", "上海易明通科技有限公司", "上海创世科贸易有限公司", "上海励能锋科技有限公司", "北京游漫天成网络技术有限公司", "北京炫扬传媒有限公司", "上海尤氏客电子商务有限公司", "上海洋中宝印务科技有限公司", "上海日天科技有限公司", "上海壹嘉禾广告传媒有限公司", "北京蒙康盛业科贸有限责任公司", "上海联想易天电子技术有限公司", "上海同济先声网络科技有限公司", "上海乐天广美通信技术有限公司", "上海斯瑞德服饰有限公司", "上海靳舜餐饮管理服务有限公司", "致远海程贸易（上海）有限公司", "四川凯达斯生物科技有限公司", "四川路遥信息技术有限公司", "可韵迪尚传媒（北京）有限公司", "辉立行科技（北京）有限公司", "深圳大袋鼠网络科技有限公司", "深圳颐亚国际传媒有限公司", "深圳芙拉国际时尚有限公司", "迪恩艾生物科技（深圳）有限公司", "深圳聚中丰达实业有限公司", "深圳辉励漫贸易有限公司", "深圳达凯峰网络技术有限公司", "北京塔丰塔科技有限公司", "北京冬麦脉武科技发展有限公司", "宣明讯讯", "北京朱珠茂科技发展有限公司", "深圳励盛博纳贸易有限公司", "深圳聚来海华实业有限公司", "深圳长荣胜西电子商务", "深圳天河蓝拓电子技术有限公司", "北京市施柏丽干洗技术有限公司", "南昌东方家俱实业有限公司", "北京舒美卫生用品有限公司", "深圳市励锐金控股份有限公司", "广州丽博华彩制造有限公司", "广州斓语文化传播有限公司", "广州安吉拉网络科技有限公", "广州潘朵时尚服饰有限公司", "广州博晟国际咨询有限公司", "广州腾冲信息科技有限公司", "广州泰恒盛世贸易有限公司", "广州励峰电子商贸有限公司", "四川清诚实业有限公司", "四川诚科世海实业有限公司", "四川励远达贸易有限公司", "四川凯励恒贸易有限公司", "四川舒漫网络技术有限公司", "四川海漫文化传播有限公司", "四川凯帝达科技有限公司", "四川励鑫创贸易有限公司", "湖北帝成科技有限公司", "武汉维希文化有限公司", "四川遨游飞扬网络科技有限公司", "四川海漫文化传播有限公司", "四川炫仕昌贸易有限公司", "四川励运贸易有限公司", "湖北银贤文化传播有限公司", "湖北恒鑫威尔电子商务有限公司", "湖北舜杰实业有限公司", "北京-炫扬传媒有限公司", "北京舒美卫生用品有限公司", "名文(北京)文化传播有限公司", "北京秦枫古典文化发展有限公司", "北京融通宝国际管理咨询有限公司广州分公司", "北京易立友信科技有限公司", "北京关谷传奇互联网有限公司 ", "北京市施柏丽干洗技术有限公司广州分公司", "许许投资(北京)文化传播有限公司", "北京幼特西电子商务有限公司", "北京臻味食尚餐饮管理有限公司", "北京游漫天成网络技术有限公司", "天津和诚金舆国际贸易", "果动时代(北京)网络技术有限公司", "南昌东方家俱实业有限公司", "北京维杰资讯有限公司", "江西新中环工贸发展有限公司", "江西世海实业投资有限公司", "北京睿仕嘉业商务咨询有限公司", "北京恒城科创商贸有限公司", "北京郦誉骐商贸有限公司", "南昌广播电视工程有限公司", "北京中核东方能源管理有限公司", "北京观景艺术发展有限公司", "北京多佐达利餐饮娱乐管理有限公司", "北京清美同创景观工程有限公司", "北京博雅时代国际文化传播有限公司", "中泰盛瑞(北京)建设有限公司", "北京燕生泽科技发展有限公司", "北京尚德中青教育科技中心", "北京华富国润资产管理有限公司", "北京百瑞祥酒店管理有限公司", "北京三格文化传媒有限公司", "北京有园艺术有限公司", "知守（北京）商业咨询有限公司", "北京蓝侣物实业有限公司", "北京励轩扬诚贸易有限公司", "北京辉立海凌科技有限公司", "北京谦乐网络技术有限公司", "北京盛恒漫游信息技术有限公司", "北京锐盛纳贸易有限公司", "北京聚荣控电子技术有限公司", "北京百吧餐饮有限公司", "北京乾坤炫耀网络技术有限公司", "北京素中电子有限公司", "北京索恒锋电子商贸有限公司", "北京励惠凯贸易有限公司", "北京博大远控科技有限责任公司", "北京天游天信科技发展有限公司", "北京海阔天高科技发展有限责任公司", "北京建者伟业科技发展有限公司", "北京智蓝信息科技有限公司南昌办事处", "北京地博资源科技有限公司江西分公司", "北京泰恒创科技有限公司", "励轩荣(北京)科技有限公司", "北京斯瑞乐天贸易有限公司", "北京锦谨贸易有限公司", "北京木森贸易有限公司", "北京屏网偌米科技有限公司", "北京罗兰萝莉科技有限公司", "北京兰蓝海网科技发展有限公司", "北京麦多麦格科技发展有限公司", "励扬博力", "北京摩登卡布科技发展有限公司", "北京易锋凤华科技有限公司", "北京超能战队科技有限公司", "星凯(北京)科技有限公司", "晟昱投资基金(北京)有限公司", "北京致远顺尧实业有限公司", "北京麦蓝励达网络技术有限公司", "北京致远可达贸易有限责任公司", "北京中宝先声实业有限公司", "北京辉瑾科技有限公司", "北京黄绿泉远科技发展有限公司", "北京美报迪迪科技发展有限公司", "北京商禹通贸科技有限公司", "北京水标瑞通科技有限公司", "北京亦如亦是科技有限公司", "北京易德海曼企业管理有限公司", "北京利历兰科技发展有限公司", "北京亦海德科技有限公司", "北京炫耀天下网络科技有限公司", "北京迅驰无限科技有限公司", "北京维杰资讯有限公司", "北京宏英国泰办公家具有限公司", "北京亮爱文化传播有限公司", "昊银网络（北京）科技有限公司", "北京游漫天成网络技术有限公司", "企福通企业管理服务（北京）有限公司", "北京蒙康盛业科贸有限责任公司", "北京瑾一商贸有限公司", "可韵迪尚传媒（北京）有限公司", "北京辉立行科技有限公司", "光线视界文化传播（北京）有限公司", "北京捷菲拓网络科技有限公司", "北京锋索实业有限公司", "北京惠天美达信息科技有限公司", "北京励通达网络技术有限公司", "北京亦如亦是科技有限公司", "北京易德海曼企业管理有限公司", "北京芷雪芷雪科技有限公司", "北京友森贸易有限公司", "北京郎郎昆科技有限公司", "北京岳悦快于科技有限公司", "北京安朵科技发展有限公司", "北京互然科技有限公司", "北京塞安贸易有限公司", "北京上好福贸易有限公司", "北京君顺通贸易有限公司", "北京艾特科技有限公司", "北京宇恒网络科技有限公司", "北京悦央缔造科技有限公司", "北京上武权科技有限公司", "北京家仪亿乐科技有限公司", "北京熠熠君科技有限公司", "北京传敏轮月科技有限公司", "北京上茂科技有限公司", "北京中泰高科科技有限公司", "北京武文贸商科技有限公司", "北京清雪视雪科技有限公司", "北京丰点易越科技有限公司", "北京合丰阳科技有限公司", "北京幻动智趣科技有限公司", "北京时代树人科技有限公司", "北京时代永道科技有限责任公司", "北京时代聚光科技有限公司", "武汉和邻居网络科技有限公司", "北京木洋数据科技有限公司", "上海百度祥科技有限公司", "上海腾讯城网络技术发展有限公司", "上海京东奇异电子技术有限公司", "上海华为尚网络技术有限公司", "上海华硕轩电子商务有限公司", "上海果壳儿电子商务有限公司", "上海国美润电子科技有限公司", "上海百励祥通网络技术有限公司", "上海晟锦电子科技有限公司", "上海军鹏电子科技发展有限公司", "上海洛汐传动科技有限公司", "上海辰圣激光科技有限公司", "上海铸衡电子科技有限公司", "上海晖翰自动化科技有限公司", "上海盈际数码科技有限公司", "上海酒通电子商务有限公司", "上海味专实业有限公司", "上海青弧网络科技有限公司", "上海爱观视觉科技有限公司", "上海步成教育科技有限公司", "上海美言信息科技有限公司", "上海韵熙网络科技有限公司", "上海东炫网络科技有限公司", "广州祥凯易科技有限公司", "广州朔轩恒贸易有限公司", "广州索游达科技有限公司", "广州核和诚科技有限公司", "广州睿扬格科技有限公司", "北京博纳聚荣科技有限公司", "广州励锦祥科技有限公司", "广州科励达网络技术有限公司", "广州泰博智网络技术有限公司", "广州和漫创衡实业有限公司", "广州易扬英创电子技术有限公司", "广州锋舆科技有限公司", "广州麦蓝德科技有限公司", "北京鸿特卓博咨询服务有限公司", "北京AIN科技有限公司", "北京联想易天科技有限公司", "北京幼特西网络技术有限公司", "北京舒维贸易有限公司", "北京寄游特科技有限公司", "北京励通达网络技术有限公司", "深圳瑾游昊亮科技有限公司", "上海可韵昊银网络有限公司", "北京谦乐网络技术有限公司", "北京西芒特科技有限公司", "海程可韵贸易（上海）有限公司", "北京联瑞海互联网有限公司", "北京蓝拓凯信科技有限公司", "上海迅驰无限科技有限公司", "北京方达科创科技有限公司", "北京博纳聚荣科技有限公司", "北京顾晟斯达科技有限公司", "天津麦蓝拓科技有限公司", "货达（天津）实业有限公司", "天津昊励贸易有限公司", "天津麦蓝致远科技有限公司", "天津路遥迪尚网络技术有限公司", "上海好易搜科技网络有限公司", "上海励泰越技术有限公司", "上海越遥科技有限公司", "成都惠丽海创科技有限公司", "成都舜世畅乐贸易有限公司", "成都炫扬普瑞科技有限公司", "北京恒维康科技有限公司", "广州励墨斯科技有限公司", "企福通企业管理服务（北京）有限公司", "北京好奇艺科网络技术有限公司", "北京暴风微众科技有限公司", "北京晟景科网络技术有限公司", ]
names = [u"赵", u"钱", u"孙", u"李", u"周", u"吴", u"郑", u"王", u"冯", u"陈", u"褚", u"卫", u"蒋", u"沈", u"韩", u"杨", u"朱", u"秦", u"尤", u"许", u"何", u"吕", u"施", u"张", u"孔", u"曹", u"严", u"华", u"金", u"魏", u"陶", u"姜", u"戚", u"谢", u"邹", u"喻", u"柏", u"水", u"窦", u"章", u"云", u"苏", u"潘", u"葛", u"奚", u"范", u"彭", u"郎", u"鲁", u"韦", u"昌", u"马", u"苗", u"凤", u"花", u"方", u"俞", u"任", u"袁", u"柳", u"酆", u"鲍", u"史", u"唐", u"费", u"廉", u"岑", u"薛", u"雷", u"贺", u"倪", u"汤", u"滕", u"殷", u"罗", u"毕", u"郝", u"邬", u"安", u"常", u"乐", u"于", u"时", u"傅", u"皮", u"卞", u"齐", u"康", u"伍", u"余", u"元", u"卜", u"顾", u"孟", u"平", u"黄", u"和", u"穆", u"萧", u"尹", u"姚", u"邵", u"湛", u"汪", u"祁", u"毛", u"禹", u"狄", u"米", u"贝", u"明", u"臧", u"计", u"伏", u"成", u"戴", u"谈", u"宋", u"茅", u"庞", u"熊", u"纪", u"舒", u"屈", u"项", u"祝", u"董", u"梁", u"杜", u"阮", u"蓝", u"闵", u"席", u"季", u"麻", u"强", u"贾", u"路", u"娄", u"危", u"江", u"童", u"颜", u"郭", u"梅", u"盛", u"林", u"刁", u"钟", u"徐", u"邱", u"骆", u"高", u"夏", u"蔡", u"田", u"樊", u"胡", u"凌", u"霍", u"虞", u"万", u"支", u"柯", u"昝", u"管", u"卢", u"莫", u"经", u"房", u"裘", u"缪", u"干", u"解", u"应", u"宗", u"丁", u"宣", u"贲", u"邓", u"郁", u"单", u"杭", u"洪", u"包", u"诸", u"左", u"石", u"崔", u"吉", u"钮", u"龚", u"程", u"嵇", u"邢", u"滑", u"裴", u"陆", u"荣", u"翁", u"荀", u"羊", u"於", u"惠", u"甄", u"麴", u"家", u"封", u"芮", u"羿", u"储", u"靳", u"汲", u"邴", u"糜", u"松", u"井", u"段", u"富", u"巫", u"乌", u"焦", u"巴", u"弓", u"牧", u"隗", u"山", u"谷", u"车", u"侯", u"宓", u"蓬", u"全", u"郗", u"班", u"仰", u"秋", u"仲", u"伊", u"宫", u"宁", u"仇", u"栾", u"暴", u"甘", u"钭", u"厉", u"戎", u"祖", u"武", u"符", u"刘", u"景", u"詹", u"束", u"龙", u"叶", u"幸", u"司", u"韶", u"郜", u"黎", u"蓟", u"薄", u"印", u"宿", u"白", u"怀", u"蒲", u"邰", u"从", u"鄂", u"索", u"咸", u"籍", u"赖", u"卓", u"蔺", u"屠", u"蒙", u"池", u"乔", u"阴", u"郁", u"胥", u"能", u"苍", u"双", u"闻", u"莘", u"党", u"翟", u"谭", u"贡", u"劳", u"逄", u"姬", u"申", u"扶", u"堵", u"冉", u"宰", u"郦", u"雍", u"舄", u"璩", u"桑", u"桂", u"濮", u"牛", u"寿", u"通", u"边", u"扈", u"燕", u"冀", u"郏", u"浦", u"尚", u"农", u"温", u"别", u"庄", u"晏", u"柴", u"瞿", u"阎", u"充", u"慕", u"连", u"茹", u"习", u"宦", u"艾", u"鱼", u"容", u"向", u"古", u"易", u"慎", u"戈", u"廖", u"庾", u"终", u"暨", u"居", u"衡", u"步", u"都", u"耿", u"满", u"弘", u"匡", u"国", u"文", u"寇", u"广", u"禄", u"阙", u"东", u"殴", u"殳", u"沃", u"利", u"蔚", u"越", u"夔", u"隆", u"师", u"巩", u"厍", u"聂", u"晁", u"勾", u"敖", u"融", u"冷", u"訾", u"辛", u"阚", u"那", u"简", u"饶", u"空", u"曾", u"毋", u"沙", u"乜", u"养", u"鞠", u"须", u"丰", u"巢", u"关", u"蒯", u"相", u"查", u"後", u"荆", u"红", u"游", u"竺", u"权", u"逯", u"盖", u"益", u"桓", u"公", u"万俟", u"司马", u"上官", u"欧阳", u"夏侯", u"诸葛", u"闻人", u"东方", u"赫连", u"皇甫", u"尉迟", u"公羊", u"澹台", u"公冶", u"宗政", u"濮阳", u"淳于", u"单于", u"太叔", u"申屠", u"公孙", u"仲孙", u"轩辕", u"令狐", u"钟离", u"宇文", u"长孙", u"慕容", u"鲜于", u"闾丘", u"司徒", u"司空", u"亓官", u"司寇", u"仉", u"督", u"子车", u"颛孙", u"端木", u"巫马", u"公西", u"漆雕", u"乐正", u"壤驷", u"公良", u"拓跋", u"夹谷", u"宰父", u"谷梁", u"晋", u"楚", u"闫", u"法", u"汝", u"鄢", u"涂", u"钦", u"段干", u"百里", u"东郭", u"南门", u"呼延", u"归", u"海", u"羊舌", u"微生", u"岳", u"帅", u"缑", u"亢", u"况", u"后", u"有", u"琴", u"梁丘", u"左丘", u"东门", u"西门", u"商", u"牟", u"佘", u"佴", u"伯", u"赏", u"南宫", u"墨", u"哈", u"谯", u"笪", u"年", u"爱", u"阳"]

def get_device():
    a='1234567890'
    b=[random.choice(a) for i in xrange(15)]
    return ''.join(b)

def handler_account(account, device_dict):
    logger.info('=======================================================')
    logger.info(str(account))
    device_id = device_dict.get(account['encode_mobile'], get_device())
    #p={'http': 'http://H1R88SO2032T1UZD:166C3BC57B0BD0CE@proxy.abuyun.com:9020', 'https': 'http://H1R88SO2032T1UZD:166C3BC57B0BD0CE@proxy.abuyun.com:9020'}
    p={'http': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun.com:9020', 'https': 'http://H01T3Z8ZSM11D61D:154F545DD00DA6B3@proxy.abuyun.com:9020'}
    # mobile = '13810808741'
    # password = '123qwe'

    a = '1234567890qwertyuiopasdfghjklzxcvbnm'
    # device_id = ''.join([random.choice(a) for j in xrange(15)])
    # device_id = '357989132322418'
    pbi_time = str(int(time.time()*1000))

    headers = {
        'versionCode': 'Android_29',
        'versionName': 'Android_5.8.0',
        'UMengChannel': '2',
        'uid': '',
        'appSign': '-1012826752',
        'deviceID': device_id,
        'deviceName': 'MI1S',
        'role': 'boss',
        'deviceModel': 'MI1S',
        'deviceVersion': '4.1.2',
        'pushVersion': '52',
        'platform': 'Android-16',
        'User-Agent': 'ChinaHrAndroid5.8.0',
        'extion': '',
        'pbi': '{"itemIndex":0,"action":"click","block":"03","time":%s,"targetPage":"b.LoginActivity\/","page":"2302","sourcePage":""}' % pbi_time, 
        'Brand': 'Xiaomi',
        'device_id': device_id,
        'device_name': 'MI1S',
        'device_os': 'Android',
        'device_os_version': '4.1.2',
        'app_version': '5.8.0',
        'uidrole': 'boss',
        'utm_source': '2',
        'tinkerLoadedSuccess': 'false',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'passport.chinahr.com',
        'Accept-Encoding': 'gzip',
    }

    # 登录
    try:
        session = requests.session()
        response = session.post('https://passport.chinahr.com/app/login', data={
            'input': account['encode_mobile'],
            'pwd': account['encode_pwd'],
            'source': '0',
            # 'msgCode': '',
        }, headers=headers, proxies=p)
        json_data = response.json()
        logger.info('login data %s' % json_data)
        code = json_data.get('code')
        msg = json_data.get('msg')
        data = json_data.get('data')
    except Exception, e:
        logger.info('login error!!!')
        logger.info(str(traceback.format_exc()))
        return
    
    if code == 0:  # 成功
        u_id = data.get('uid')
        info_flag = data.get('infoFlag')
        u_name = data.get('uName')
        im_token = data.get('imToken')
        new_im_token = data.get('newImToken')

        get_user_url = 'https://app.chinahr.com/buser/getUserInfo'
        headers['Host'] = 'app.chinahr.com'
        headers['pbi'] = '{"itemIndex":0,"action":"click","block":"03","time":%s,"targetPage":"b.MainActivity\/","page":"2302","sourcePage":""}' % pbi_time
        login_tag = False
        for login_index in range(3):
            try:
                response = session.get(get_user_url, headers=headers, proxies=p)
                logger.info(response.text)
                info_data = response.json()
                login_tag = True
                break
            except Exception, e:
                logger.info('login error!!!'+str(login_index))
        if not login_tag:
            return
            
        if info_data.get('code') in [0, '0']:
            print '-------------------------',info_data.get('data', {}).get('isUserFinished', False), info_data.get('data', {}).get('isCompFinished', False)
            if not info_data.get('data', {}).get('isUserFinished', False):
                # finish the user info
                try:
                    headers['uid'] = u_id
                    headers['Host'] = 'app.chinahr.com'
                    headers['pbi'] = '{"itemIndex":0,"action":"click","block":"03","time":%s,"targetPage":"b.CompanyInfoActivity\/","page":"2200","sourcePage":""}' % pbi_time
                    response = session.post('https://app.chinahr.com/buser/setUserInfo', headers=headers, data={
                        'nickname': random.choice(names)+random.choice([u'先生', u'女士', u'']), 'position': 'hr'}, proxies=p)
                    json_data = response.json()
                    logger.info('return data of finish user info %s' % json_data)
                    code = json_data.get('code')
                    msg = json_data.get('msg')
                    data = json_data.get('data')
                    rt = json_data.get('rt')
                    if code in [0, '0']:
                        logger.info('finish the user info!!!')
                    else:
                        logger.error('failed to finish user info - %s ' % (msg,))
                except Exception, e:
                    logger.info('error when finish user!!!'+ str(traceback.format_exc()))
                

            if not info_data.get('data', {}).get('isCompFinished', False):
                # finish company info
                try:
                    headers['uid'] = u_id
                    headers['Host'] = 'app.chinahr.com'
                    headers['pbi'] = '{"itemIndex":0,"action":"click","block":"02","time":%s,"targetPage":"b.CompanyInfoActivity\/","page":"2201","sourcePage":""}' % pbi_time
                    response = session.post('https://app.chinahr.com/buser/setCompanyInfo', headers=headers, data=u'name=%s&sizeId=3&typeId=7&industryId=1101,11000' % urllib.quote(random.choice(companys)), proxies=p)
                    company_json = response.json()
                    logger.info('return data of finish company %s' % company_json)
                    code = company_json.get('code')
                    msg = company_json.get('msg')
                    data = company_json.get('data')
                    rt = company_json.get('rt')
                    if code in [0, '0']:
                        logger.info('finish the company info!!!')
                    else:
                        logger.error('failed to finish company - %s ' % (msg,))
                except Exception, e:
                    logger.info('error when finish company!!!'+ str(traceback.format_exc()))
                

                #finish company address info
                try:
                    headers['uid'] = u_id
                    headers['Host'] = 'app.chinahr.com'
                    headers['pbi'] = '{"itemIndex":0,"action":"click","block":"04","time":%s,"targetPage":"b.CompanyInfoActivity\/","page":"2201","sourcePage":""}' % pbi_time
                    response = session.post('https://app.chinahr.com/buser/setCompAddrInfo', headers=headers, data=u'location=34,398,3545&addr=北京&compDesc=%s' % ''.join([random.choice(a) for x in xrange(70)]), proxies=p)
                    company_json = response.json()
                    logger.info('return data of finish company %s' % company_json)
                    code = company_json.get('code')
                    msg = company_json.get('msg')
                    data = company_json.get('data')
                    rt = company_json.get('rt')
                    if code in [0, '0']:
                        logger.info('finish the company address info!!!')
                    else:
                        logger.error('failed to finish company address - %s ' % (msg,))
                except Exception, e:
                    logger.info('error when finish company address!!!'+ str(traceback.format_exc()))
            try:
                headers['uid'] = u_id
                headers['Host'] = 'app.chinahr.com'
                headers['pbi'] = '{"itemIndex":0,"action":"click","block":"04","time":%s,"targetPage":"b.CompanyCompleteActivity\/","page":"2201","sourcePage":""}' % pbi_time
                response = session.post('https://app.chinahr.com/buser/lackJob', headers=headers, data=u'lackJob=%E9%94%80%E5%94%AE', proxies=p)
                company_json = response.json()
                logger.info('return data of finish lackJob %s' % company_json)
                code = company_json.get('code')
                msg = company_json.get('msg')
                data = company_json.get('data')
                rt = company_json.get('rt')
                if code in [0, '0']:
                    logger.info('finish the lackJob!!!')
                else:
                    logger.error('failed to finish lackJob - %s ' % (msg,))
            except Exception, e:
                logger.info('error when finish lackJob!!!'+ str(traceback.format_exc()))
                
        else:
            logger.info('get user info error!!!')
    else:
        logger.error('login failed - %s ' % (msg,))


def main():
    device_file = open('device', 'r')
    device_list = device_file.readlines()
    device_file.close()
    device_dict = {}
    for i in device_list:
        device_dict.update(eval(i))
    continue_count = 15956
    for i in open('accounts', 'r'):
        if continue_count:
            continue_count -= 1
            continue
        handler_account(eval(i), device_dict)


if __name__ == '__main__':
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('.', 'set_info'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)

    main()

#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: IntelliJ IDEA
@file: executor.py
@create at: 2018-09-29 10:46

这一行开始写关于本文件的说明与解释
"""

from scrapy.cmdline import execute


def main():
    execute('scrapy crawl search'.split())


if __name__ == '__main__':
    main()

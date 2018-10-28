#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com


import logging
import logging.config


logging.config.fileConfig('./conf/logger.conf')


class Logger(object):
    @staticmethod
    def file_logger():
        return logging.getLogger('fileLogger')

    @staticmethod
    def rt_logger():
        return logging.getLogger('rtLogger')

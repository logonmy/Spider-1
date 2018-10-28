# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy.utils.response import response_status_message
from crwy.utils.scrapy_plugs.middlewares import CookieMiddleware


class FiveEightDownloaderSearchMiddleware(CookieMiddleware):
    # def process_response(self, request, response, spider):
    #     # Called with the response returned from the downloader.
    #
    #     # Must either;
    #     # - return a Response object
    #     # - return a Request object
    #     # - or raise IgnoreRequest
    #     return response

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response

        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        if 'passport.58.com/login' in response.url:
            reason = 'cookie invalid'
            return self._retry(request, reason, spider) or response
        return response

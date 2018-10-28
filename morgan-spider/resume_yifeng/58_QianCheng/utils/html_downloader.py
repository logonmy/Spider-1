#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com

import requests


class HtmlDownloader(object):
    def __init__(self):
        self.session = requests.session()

    def download(self, url, method='GET', timeout=60, **kwargs):
        if method == 'GET':
            return self.session.get(url, timeout=timeout, **kwargs)
        else:
            return self.session.post(url, timeout=timeout, **kwargs)

    def downloadFile(self, url, save_path='./data/'):
        file_name = url.split('/')[-1]
        file = self.download(url, stream=True)
        with open(save_path+file_name, 'wb') as f:
            for chunk in file.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
            f.close()
        return save_path+file_name

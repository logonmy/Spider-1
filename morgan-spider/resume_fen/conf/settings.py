#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: wuyue
# Email: wuyue@mofanghr.com


project_settings = {
    'SOURCE': 'RESUME_FEN',
    'PROJECT_NAME': 'resume_fen',
    'TASK_TYPE': 'RESUME_FETCH',
    'SAVE_TYPE': 'mns',

    # 使用线上帐号
    'ACCOUNT_URL': 'http://172.16.25.41:8002/acc/getCookie.json?source=%s'
                   '&useType=%s',
    'SET_INVALID_URL': 'http://172.16.25.41:8002/acc/invalidCookie.json?'
                       'userName=%s&password=%s&source=%s'
}

#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: wuyue
@contact: wuyue92tree@163.com
@software: PyCharm
@file: resume_test.py
@create at: 2018-04-08 09:54

这一行开始写关于本文件的说明与解释
"""
import json

from resume_fen import ResumeFen


class ResumeFenTest(ResumeFen):
    def __init__(self):
        super(ResumeFenTest, self).__init__()

    def get_cookie(self):
        self.cookie = 'hdflag=invalite; hdflag=active; huodong=fenjianli; Hm_lvt_697a74c71a0302bb9222a9b9d3a9b934=1523185589; Hm_lpvt_697a74c71a0302bb9222a9b9d3a9b934=1523185674; JSESSIONID=B616A05DD77A50A00A8B1EF6FBB42644; Hm_lvt_553e06d0322a2c6ff45a820e1b26c315=1523156103; Hm_lpvt_553e06d0322a2c6ff45a820e1b26c315=1523253933; Hm_lvt_accc94e05dd4516e89bc93ebd0d3938e=1522733521,1523151022,1523153509; Hm_lpvt_accc94e05dd4516e89bc93ebd0d3938e=1523256916; username=18629947965; password=402e426ecf60bacf3f305937f165fe56; Hm_lvt_b9e62a948ba6b6274cc0fa7e61b1b38b=1522733521,1522737862,1523151022,1523153509; Hm_lpvt_b9e62a948ba6b6274cc0fa7e61b1b38b=1523256930; SERVERID=70356234b78238645df699ef52f30d81|1523256934|1523237672'
        self.auth_kwargs = {
            'username': u'18629947965'
        }
        return self.cookie

def main():
    runner = ResumeFenTest()
    runner.get_cookie()
    # params = {
    #     'job_name': u'电话销售',
    #     'area_name': u'北京',
    #     'area_code': '110000',
    #     'job_code': '246',
    # }
    # runner.get_resume_list_zl(page=1, **params)
    # print runner.cookie

    resume_id = '1000581548'
    runner.download_resume(resume_id=resume_id)

    # page = 1
    # while True:
    #     resume_list = runner.get_resume_list_lp(page=page, **params)
    #     print resume_list
    #     for resume in resume_list:
    #         print runner.get_resume_detail(resume.get('id'))
    #         print '-'*50
    #
    #     page += 1

if __name__ == '__main__':
    main()

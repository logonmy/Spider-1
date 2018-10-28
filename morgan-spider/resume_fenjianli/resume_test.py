#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/4/3 0003 14:07
# @Author  : huangyee
# @Email   : 1173842904@qq.com
# @File    : resume_test.py
# @Software: PyCharm
import sys
import os
import logging
import settings
import resume_fenjianli
import json
import time
import traceback

reload(sys)
sys.setdefaultencoding("utf-8")

current_file_path = os.path.abspath(__file__)
current_dir_file_path = os.path.dirname(__file__)
current_file_name = os.path.basename(__file__)
logger = logging.getLogger()
sys.path.append("../common")
import utils
import uuid

cookie = {'code': 0, 'cookie': {'SERVERID': '70356234b78238645df699ef52f30d81|1522806241|1522806241',
                                'JSESSIONID': 'A3CF43A5891596C98EDE1C2D5E5BE76A'}}
# cookie_str = 'SERVERID=' + cookie.get('cookie').get('SERVERID') + ';JSESSIONID=' + cookie.get(
#     'cookie').get(
#     'JSESSIONID')
cookie_str = 'hdflag=invalite; huodong=fenjianli; hdflag=active; JSESSIONID=343A34B643AA7E25BFB556B031FB67A5; Hm_lvt_accc94e05dd4516e89bc93ebd0d3938e=1522734203,1522808042; Hm_lpvt_accc94e05dd4516e89bc93ebd0d3938e=1522808042; Hm_lvt_b9e62a948ba6b6274cc0fa7e61b1b38b=1522734203,1522808042; username=18629947965; password=402e426ecf60bacf3f305937f165fe56; Hm_lpvt_b9e62a948ba6b6274cc0fa7e61b1b38b=1522808060; SERVERID=70356234b78238645df699ef52f30d81|1522808534|1522808375'


def get_list():
    # task = {"area_name": u"天津", "job_code": "918", "area_code": "120000", "model_name": "zhilian", "job_name": u"其他"}
    task = {"area_name": u"北京", "job_code": "228", "area_code": "110000", "model_name": "zhilian", "job_name": u"销售主管"}
    print resume_fenjianli.get_list(cookie=cookie_str
                                    , page_numner=1, params=task, proxy=settings.get_proxy())


def get_detail():
    # list_result = {'total': 169, 'code': 0, 'data': [],
    #                'ids': [['1022347197', '2018-04-03'], ['1032771612', '2018-04-03'], ['1006918947', '2018-04-03'],
    #                        ['1045864491', '2018-04-03'], ['1047088655', '2018-04-03'], ['1025484341', '2018-04-03'],
    #                        ['1069702121', '2018-04-03'], ['1033655918', '2018-04-03'], ['1030018035', '2018-04-03'],
    #                        ['1003596638', '2018-04-03'], ['1033708572', '2018-04-02'], ['1026380481', '2018-04-02'],
    #                        ['1022050585', '2018-04-02'], ['1002563812', '2018-04-02'], ['1025279315', '2018-04-02'],
    #                        ['1035975978', '2018-04-02'], ['1031484197', '2018-04-02'], ['1070907357', '2018-04-02'],
    #                        ['1066977155', '2018-04-02'], ['1022591047', '2018-04-02'], ['1030550073', '2018-04-02'],
    #                        ['1033854943', '2018-04-02'], ['1031640132', '2018-04-02'], ['1070885063', '2018-04-02'],
    #                        ['1070729932', '2018-04-02'], ['1045212527', '2018-04-02'], ['1028664287', '2018-04-02'],
    #                        ['1070885595', '2018-04-02'], ['1025872345', '2018-04-02'], ['1067914985', '2018-04-02']]}
    list_result = {'total': 321, 'code': 0, 'data': [],
                   'ids': [[u'1026367068', u'2018-04-03'], [u'1033060991', u'2018-04-03'],
                           [u'1038441431', u'2018-04-03'], [u'1001363022', u'2018-04-03'],
                           [u'1019659221', u'2018-04-03'], [u'1002660342', u'2018-04-03'],
                           [u'1035984395', u'2018-04-03'], [u'1014826155', u'2018-04-03'],
                           [u'1028142888', u'2018-04-03'], [u'1022642061', u'2018-04-03'],
                           [u'1043983298', u'2018-04-03'], [u'1029731078', u'2018-04-03'],
                           [u'1002851632', u'2018-04-03'], [u'1002354915', u'2018-04-03'],
                           [u'1027887893', u'2018-04-03'], [u'1032848553', u'2018-04-03'],
                           [u'1070807725', u'2018-04-03'], [u'1031349867', u'2018-04-03'],
                           [u'1027071847', u'2018-04-03'], [u'1021747472', u'2018-04-03'],
                           [u'1000155591', u'2018-04-03'], [u'1029013102', u'2018-04-03'],
                           [u'1070737095', u'2018-04-03'], [u'1020231833', u'2018-04-03'],
                           [u'1037316081', u'2018-04-03'], [u'1019132225', u'2018-04-03'],
                           [u'1026149838', u'2018-04-03'], [u'1070834895', u'2018-04-03'],
                           [u'1029253681', u'2018-04-03'], [u'1058461095', u'2018-04-02']]}

    for id in list_result.get('ids'):
        detail_data = resume_fenjianli.get_resume(resume_id=id[0],
                                                  cookie='JSESSIONID=%s;  huodong=fenjianli; hdflag=active; SERVERID=%s'
                                                         % (cookie.get('cookie').get('JSESSIONID'),
                                                            cookie.get('cookie').get('SERVERID')), model_name='zhilian',
                                                  proxy=settings.get_proxy())
        # logger.info(json.dumps(detail_data, ensure_ascii=False))
        # resume_result = get_resume(resume[0], cookie, task['model_name'], proxy=proxy)
        resume_uuid = uuid.uuid1()
        try:
            sql = 'insert into spider_search.resume_raw (source, content, createBy, trackId, createtime, email, emailJobType, emailCity, subject) values (%s, %s, "python", %s, now(), %s, %s, %s, %s)'
            sql_value = ('RESUME_FEN', json.dumps(detail_data['json'], ensure_ascii=False), resume_uuid,
                         '18629947965', '其他', '天津', str(id[0]))

            resume_update_time = detail_data['json']['updateDate']
            kafka_data = {
                "channelType": "WEB",
                "content": {
                    "content": json.dumps(detail_data['json'], ensure_ascii=False),
                    "id": '',
                    "createBy": "python",
                    "createTime": int(time.time() * 1000),
                    "ip": '',
                    "resumeSubmitTime": '',
                    "resumeUpdateTime": resume_update_time,
                    "source": 'RESUME_FEN',
                    "trackId": str(resume_uuid),
                    "avatarUrl": '',
                    "email": '18629947965',
                    'emailJobType': '其他',
                    'emailCity': '天津',
                    'subject': str(id[0])
                },
                "interfaceType": "PARSE",
                "resourceDataType": "RAW",
                "resourceType": "RESUME_SEARCH",
                "source": 'RESUME_FEN',
                "trackId": str(resume_uuid),
                'traceID': str(resume_uuid),
                'callSystemID': 'python',
            }
            utils.save_data(sql, sql_value, kafka_data)
        except Exception, e:
            logger.info('get error when write mns, exit!!!' + str(traceback.format_exc()))
            # return
        time.sleep(1)


def process():
    # get_list()
    get_detail()
    pass


if __name__ == '__main__':
    utils.set_setting([])
    formatter = logging.Formatter(
        fmt="%(asctime)s %(filename)s %(funcName)s [line:%(lineno)d] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()

    rotating_handler = logging.handlers.RotatingFileHandler(
        '%s/%s.log' % ('/data/logs', 'resume_test'), 'a', 50 * 1024 * 1024, 100, None, 0)

    stream_handler.setFormatter(formatter)
    rotating_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)
    logger.setLevel(logging.INFO)
    process()
    pass
